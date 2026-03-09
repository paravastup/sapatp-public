"""
RAG Indexing Service for Product Catalog
Converts products to embeddings and stores in FAISS index
"""
import numpy as np
import faiss
import requests
import json
import logging
from django.conf import settings
from products.models import Product

logger = logging.getLogger(__name__)


class ProductIndexer:
    """Index products into FAISS vector database"""

    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.embedding_model = 'nomic-embed-text'
        self.dimension = 768  # nomic-embed-text dimensions
        self.index_path = '/app/data/product_embeddings.index'
        self.mapping_path = '/app/data/product_skus.json'

    def get_embedding(self, text):
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f'{self.ollama_url}/api/embeddings',
                json={'model': self.embedding_model, 'prompt': text},
                timeout=30
            )
            if response.status_code == 200:
                return np.array(response.json()['embedding'], dtype='float32')
            else:
                logger.error(f"Ollama embedding failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def format_product_text(self, product):
        """Format product for embedding"""
        # Create a rich text representation including all searchable fields
        text_parts = [
            f"SKU: {product.sku}",
            f"Name: {product.label or product.product_name}",  # Use label (accurate description)
            f"Brand: {product.catalog_brand or ''}",
            f"Category: {product.catalog_category or ''}",
        ]

        # Add optional fields if available
        if product.catalog_collection:
            text_parts.append(f"Collection: {product.catalog_collection}")
        if product.material:
            text_parts.append(f"Material: {product.material}")
        if product.short_description:
            text_parts.append(f"Description: {product.short_description}")
        if product.product_tags:
            text_parts.append(f"Tags: {product.product_tags}")

        # Add price for filtering
        text_parts.append(f"Web Price: ${product.web_price}")
        text_parts.append(f"List Price: ${product.list_price}")

        return "\n".join(text_parts)

    def build_index(self):
        """Build FAISS index from all products"""
        logger.info("Building FAISS index for products...")

        # Get all products
        products = Product.objects.all().order_by('sku')
        total = products.count()

        logger.info(f"Processing {total} products...")

        # Initialize FAISS index (L2 distance)
        index = faiss.IndexFlatL2(self.dimension)

        # Store SKU mapping
        sku_mapping = []
        embeddings = []

        for i, product in enumerate(products):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{total} products...")

            # Get product text
            text = self.format_product_text(product)

            # Get embedding
            embedding = self.get_embedding(text)
            if embedding is not None:
                embeddings.append(embedding)
                sku_mapping.append(product.sku)
            else:
                logger.warning(f"Failed to get embedding for product {product.sku}")

        # Add to FAISS index
        if embeddings:
            embeddings_array = np.array(embeddings)
            index.add(embeddings_array)

            # Save index
            faiss.write_index(index, self.index_path)

            # Save SKU mapping
            with open(self.mapping_path, 'w') as f:
                json.dump(sku_mapping, f)

            logger.info(f"✅ Index built successfully! {len(sku_mapping)} products indexed.")
            logger.info(f"Index file: {self.index_path} ({index.ntotal} vectors)")
            return index, sku_mapping
        else:
            logger.error("No embeddings generated! Check Ollama connection.")
            return None, None
