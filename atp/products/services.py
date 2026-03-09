"""
Product data access services for chatbot integration
Provides efficient querying and caching for product information
"""
from typing import List, Dict, Optional
from django.core.cache import cache
from django.db.models import Q
from products.models import Product, ProductBrand, ProductCategory


class ProductService:
    """Service layer for product data access"""

    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_product_by_sku(cls, sku: str) -> Optional[Product]:
        """
        Get product by SKU with caching

        Args:
            sku: Product SKU (e.g., 'FP906')

        Returns:
            Product instance or None
        """
        cache_key = f'product:sku:{sku}'
        product = cache.get(cache_key)

        if product is None:
            try:
                product = Product.objects.get(sku=sku)
                cache.set(cache_key, product, cls.CACHE_TIMEOUT)
            except Product.DoesNotExist:
                return None

        return product

    @classmethod
    def get_product_by_gtin(cls, gtin: str) -> Optional[Product]:
        """
        Get product by GTIN/barcode

        Args:
            gtin: GTIN/UPC barcode

        Returns:
            Product instance or None
        """
        cache_key = f'product:gtin:{gtin}'
        product = cache.get(cache_key)

        if product is None:
            try:
                product = Product.objects.get(gtin=gtin)
                cache.set(cache_key, product, cls.CACHE_TIMEOUT)
            except Product.DoesNotExist:
                return None

        return product

    @classmethod
    def get_product_by_legacy_sku(cls, old_sku: str) -> Optional[Product]:
        """
        Get product by legacy/old item number

        Args:
            old_sku: Old item number (e.g., 'Q5761#1')

        Returns:
            Product instance or None
        """
        cache_key = f'product:legacy:{old_sku}'
        product = cache.get(cache_key)

        if product is None:
            try:
                product = Product.objects.get(old_item_number=old_sku)
                cache.set(cache_key, product, cls.CACHE_TIMEOUT)
            except Product.DoesNotExist:
                return None

        return product

    @classmethod
    def get_products_by_brand(cls, brand: str, limit: int = 100) -> List[Product]:
        """
        Get all products for a specific brand

        Args:
            brand: Brand name (e.g., 'Brand Zeta')
            limit: Maximum number of products to return

        Returns:
            List of Product instances
        """
        cache_key = f'products:by_brand:{brand}:{limit}'
        products = cache.get(cache_key)

        if products is None:
            products = list(
                Product.objects.filter(catalog_brand__iexact=brand)
                .order_by('sku')[:limit]
            )
            cache.set(cache_key, products, cls.CACHE_TIMEOUT)

        return products

    @classmethod
    def get_products_by_category(cls, category: str, limit: int = 100) -> List[Product]:
        """
        Get all products for a specific category

        Args:
            category: Category name (e.g., 'Glassware')
            limit: Maximum number of products to return

        Returns:
            List of Product instances
        """
        cache_key = f'products:by_category:{category}:{limit}'
        products = cache.get(cache_key)

        if products is None:
            products = list(
                Product.objects.filter(catalog_category__iexact=category)
                .order_by('sku')[:limit]
            )
            cache.set(cache_key, products, cls.CACHE_TIMEOUT)

        return products

    @classmethod
    def get_products_by_material(cls, material: str, limit: int = 100) -> List[Product]:
        """
        Get all products made of specific material

        Args:
            material: Material name (e.g., 'Vitrified Ceramic')
            limit: Maximum number of products to return

        Returns:
            List of Product instances
        """
        cache_key = f'products:by_material:{material}:{limit}'
        products = cache.get(cache_key)

        if products is None:
            products = list(
                Product.objects.filter(material__iexact=material)
                .order_by('sku')[:limit]
            )
            cache.set(cache_key, products, cls.CACHE_TIMEOUT)

        return products

    @classmethod
    def get_products_by_collection(cls, collection: str, limit: int = 100) -> List[Product]:
        """
        Get all products in a specific collection

        Args:
            collection: Collection name (e.g., 'Papillon Green')
            limit: Maximum number of products to return

        Returns:
            List of Product instances
        """
        cache_key = f'products:by_collection:{collection}:{limit}'
        products = cache.get(cache_key)

        if products is None:
            products = list(
                Product.objects.filter(catalog_collection__iexact=collection)
                .order_by('sku')[:limit]
            )
            cache.set(cache_key, products, cls.CACHE_TIMEOUT)

        return products

    @classmethod
    def search_products(cls, query: str, limit: int = 50) -> List[Product]:
        """
        Search products by name, SKU, tags, or description

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of Product instances
        """
        cache_key = f'products:search:{query}:{limit}'
        products = cache.get(cache_key)

        if products is None:
            q_filter = (
                Q(sku__icontains=query) |
                Q(product_name__icontains=query) |
                Q(label__icontains=query) |
                Q(product_tags__icontains=query) |
                Q(short_description__icontains=query)
            )

            products = list(
                Product.objects.filter(q_filter)
                .order_by('sku')[:limit]
            )
            cache.set(cache_key, products, cls.CACHE_TIMEOUT)

        return products

    @classmethod
    def get_all_brands(cls) -> List[Dict[str, any]]:
        """
        Get list of all brands with product counts

        Returns:
            List of dicts with brand info
        """
        cache_key = 'brands:all'
        brands = cache.get(cache_key)

        if brands is None:
            brands = list(
                ProductBrand.objects.all()
                .order_by('name')
                .values('name', 'product_count', 'thumbnail')
            )
            cache.set(cache_key, brands, cls.CACHE_TIMEOUT)

        return brands

    @classmethod
    def get_all_categories(cls) -> List[Dict[str, any]]:
        """
        Get list of all categories with product counts

        Returns:
            List of dicts with category info
        """
        cache_key = 'categories:all'
        categories = cache.get(cache_key)

        if categories is None:
            categories = list(
                ProductCategory.objects.all()
                .order_by('name')
                .values('name', 'product_count', 'subcategories')
            )
            cache.set(cache_key, categories, cls.CACHE_TIMEOUT)

        return categories

    @classmethod
    def get_product_enrichment(cls, sku: str) -> Optional[Dict[str, any]]:
        """
        Get enriched product data for chatbot responses

        Args:
            sku: Product SKU

        Returns:
            Dict with product details optimized for chatbot
        """
        product = cls.get_product_by_sku(sku)

        if not product:
            return None

        return {
            'sku': product.sku,
            'name': product.product_name,
            'brand': product.catalog_brand,
            'category': product.catalog_category,
            'collection': product.catalog_collection,
            'description': product.label,  # Use label (accurate description from DataFeed XML)
            'family': product.family,  # For URL building
            'catalog_category': product.catalog_category,  # For URL building
            'website_subcategories': product.website_subcategories,  # For URL building
            'label': product.label,  # For URL building
            'price': {
                'list': float(product.list_price),
                'web': float(product.web_price),
                'currency': 'USD'
            },
            'case_info': {
                'qty': product.sap_case_qty,
                'weight': float(product.sap_case_weight) if product.sap_case_weight else None,
                'volume': float(product.sap_case_volume) if product.sap_case_volume else None,
            },
            'specs': {
                'material': product.material,
                'dimensions': product.dimensions,
                'capacity': product.capacity,
                'color': product.color,
            },
            'images': {
                'thumbnail': product.thumbnail,
                'all_images': product.get_image_urls(),
            },
            'status': {
                'active': product.status == 'Active',
                'new': product.is_new_feature,
                'sampleable': product.is_sampleable,
            },
            'relationships': {
                'related_skus': product.get_related_skus(),
            }
        }

    @classmethod
    def get_skus_for_bulk_query(cls, brand: str = None, category: str = None,
                                 material: str = None, collection: str = None,
                                 limit: int = 50) -> List[str]:
        """
        Get list of SKUs matching filter criteria for bulk SAP queries

        Args:
            brand: Filter by brand
            category: Filter by category
            material: Filter by material
            collection: Filter by collection
            limit: Maximum SKUs to return

        Returns:
            List of SKU strings
        """
        filters = Q()

        if brand:
            filters &= Q(catalog_brand__iexact=brand)
        if category:
            filters &= Q(catalog_category__iexact=category)
        if material:
            filters &= Q(material__iexact=material)
        if collection:
            filters &= Q(catalog_collection__iexact=collection)

        cache_key = f'skus:bulk:{brand}:{category}:{material}:{collection}:{limit}'
        skus = cache.get(cache_key)

        if skus is None:
            skus = list(
                Product.objects.filter(filters)
                .values_list('sku', flat=True)
                .order_by('sku')[:limit]
            )
            cache.set(cache_key, skus, cls.CACHE_TIMEOUT)

        return skus

    @staticmethod
    def build_product_url(family: str = None, category: str = None,
                         subcategories: str = None, label: str = None) -> str:
        """
        Build Plant A product URL from DataFeed data fields

        Args:
            family: Product family (e.g., 'Tableware')
            category: Catalog category (e.g., 'Glassware')
            subcategories: Website subcategories (e.g., 'Wine')
            label: Product label/name (e.g., 'Cabernet Tall Wine 16.0 Oz')

        Returns:
            Product URL (e.g., 'https://www.example.com/our-products/tableware/glassware/wine/cabernet-tall-wine-16.0-oz/')
        """
        base_url = "https://example.com/our-products"

        def url_encode(text: str) -> str:
            """Convert text to URL-safe format"""
            if not text:
                return ""
            return (text.strip()
                   .lower()
                   .replace(' ', '-')
                   .replace('&', 'and')
                   .replace('/', '-')
                   .replace('.', '-')
                   .replace('  ', '-'))

        # Build URL parts from available fields
        parts = [
            url_encode(family),
            url_encode(category),
            url_encode(subcategories),
            url_encode(label)
        ]

        # Filter out empty parts
        parts = [p for p in parts if p]

        if not parts:
            return base_url

        return f"{base_url}/{'/'.join(parts)}/"
