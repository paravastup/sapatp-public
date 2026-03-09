"""
RAG Retrieval Service
Searches vector index for relevant products
"""
import numpy as np
import faiss
import json
import requests
import logging
import os
from typing import List, Dict, Optional
from django.conf import settings
from products.models import Product

logger = logging.getLogger(__name__)


class ProductRetriever:
    """Retrieve products using vector similarity search"""

    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.embedding_model = 'nomic-embed-text'
        self.index_path = '/app/data/product_embeddings.index'
        self.mapping_path = '/app/data/product_skus.json'

        # Load index and mapping
        self.index = None
        self.sku_mapping = None
        self._load_index()

    def _load_index(self):
        """Load FAISS index and SKU mapping"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, 'r') as f:
                    self.sku_mapping = json.load(f)
                logger.info(f"✅ RAG index loaded: {self.index.ntotal} products")
            else:
                logger.warning(f"⚠️  RAG index not found. Run 'python manage.py build_product_index' to create it.")
        except Exception as e:
            logger.error(f"Error loading RAG index: {e}")

    def is_ready(self):
        """Check if RAG system is ready"""
        return self.index is not None and self.sku_mapping is not None

    def get_embedding(self, text):
        """Get query embedding from Ollama"""
        try:
            response = requests.post(
                f'{self.ollama_url}/api/embeddings',
                json={'model': self.embedding_model, 'prompt': text},
                timeout=10
            )
            if response.status_code == 200:
                embedding = response.json()['embedding']
                return np.array([embedding], dtype='float32')
            else:
                logger.error(f"Ollama embedding failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def search(self, query: str, k: int = 10, filters: Optional[Dict] = None) -> List[Product]:
        """
        Search for products matching query

        Args:
            query: User search query
            k: Number of results to return
            filters: Optional structured filters (brand, category, price, etc.)

        Returns:
            List of Product objects
        """
        if not self.is_ready():
            logger.warning("RAG not ready, returning empty results")
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            logger.error("Failed to get query embedding")
            return []

        # Search FAISS index (get extra for filtering)
        try:
            distances, indices = self.index.search(query_embedding, k * 3)
        except Exception as e:
            logger.error(f"FAISS search error: {e}")
            return []

        # Get matching SKUs
        matching_skus = []
        for i in indices[0]:
            if i < len(self.sku_mapping) and i >= 0:
                matching_skus.append(self.sku_mapping[i])

        if not matching_skus:
            return []

        # Retrieve products from database
        products = Product.objects.filter(sku__in=matching_skus)

        # Apply structured filters if provided
        if filters:
            if 'brand' in filters and filters['brand']:
                products = products.filter(catalog_brand__iexact=filters['brand'])
            if 'category' in filters and filters['category']:
                products = products.filter(catalog_category__iexact=filters['category'])
            if 'material' in filters and filters['material']:
                products = products.filter(material__iexact=filters['material'])
            if 'max_price' in filters and filters['max_price']:
                products = products.filter(web_price__lte=filters['max_price'])
            if 'min_price' in filters and filters['min_price']:
                products = products.filter(web_price__gte=filters['min_price'])

        # Convert to list and preserve RAG ranking order
        products_dict = {p.sku: p for p in products}
        ranked_products = []
        for sku in matching_skus:
            if sku in products_dict:
                ranked_products.append(products_dict[sku])
                if len(ranked_products) >= k:
                    break

        logger.info(f"RAG search '{query}' returned {len(ranked_products)} products")
        return ranked_products

    def get_product_context(self, products: List[Product], max_products: int = 5) -> str:
        """
        Format products as context for LLM

        Args:
            products: List of Product objects
            max_products: Maximum products to include

        Returns:
            Formatted context string
        """
        if not products:
            return "No products found matching the query."

        context = f"Found {len(products)} relevant product(s):\n\n"

        for i, product in enumerate(products[:max_products], 1):
            context += f"{i}. SKU: {product.sku}\n"
            context += f"   Name: {product.label or product.product_name}\n"
            context += f"   Brand: {product.catalog_brand}\n"
            context += f"   Category: {product.catalog_category}\n"

            if product.material:
                context += f"   Material: {product.material}\n"

            if product.catalog_collection:
                context += f"   Collection: {product.catalog_collection}\n"

            context += f"   Web Price: ${product.web_price}\n"
            context += f"   List Price: ${product.list_price}\n"

            if product.short_description:
                # Truncate long descriptions
                desc = product.short_description
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                context += f"   Description: {desc}\n"

            context += "\n"

        if len(products) > max_products:
            context += f"...and {len(products) - max_products} more product(s).\n"

        return context
