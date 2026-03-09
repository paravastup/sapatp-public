"""
Product models for DataFeed feed integration
Master product data source for enriching SAP availability queries
"""
from django.db import models
from django.utils import timezone


class Product(models.Model):
    """
    Complete product information from DataFeed PIM system
    Serves as master data source for product details, pricing, images, and specifications
    """

    # ======================
    # IDENTIFIERS
    # ======================
    sku = models.CharField(
        max_length=50,
        primary_key=True,
        help_text="Primary SKU identifier (e.g., FP906, X0463)"
    )

    gtin = models.CharField(
        max_length=14,
        db_index=True,
        null=True,
        blank=True,
        help_text="Global Trade Item Number / Barcode (EAN/UPC)"
    )

    old_item_number = models.CharField(
        max_length=50,
        db_index=True,
        null=True,
        blank=True,
        help_text="Legacy SKU reference (e.g., Q5761#1)"
    )

    # ======================
    # PRODUCT INFORMATION
    # ======================
    label = models.CharField(
        max_length=500,
        help_text="Product label/display name"
    )

    product_name = models.CharField(
        max_length=500,
        help_text="Full product name"
    )

    catalog_brand = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Brand name (e.g., Brand_Kappa, Dudson, Brand Zeta)"
    )

    catalog_collection = models.CharField(
        max_length=100,
        db_index=True,
        null=True,
        blank=True,
        help_text="Product collection/line (e.g., Islande, Papillon Green)"
    )

    family = models.CharField(
        max_length=100,
        db_index=True,
        null=True,
        blank=True,
        help_text="Product family (e.g., Tableware, Buffetware)"
    )

    categories = models.TextField(
        null=True,
        blank=True,
        help_text="Hierarchical categories (comma-separated)"
    )

    catalog_category = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Main catalog category (Dinnerware, Glassware, Flatware, etc.)"
    )

    website_subcategories = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Website subcategories for navigation"
    )

    # ======================
    # DESCRIPTIONS
    # ======================
    long_description = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed product description for marketing"
    )

    short_description = models.TextField(
        null=True,
        blank=True,
        help_text="Brief product description/summary"
    )

    product_tags = models.TextField(
        null=True,
        blank=True,
        help_text="Search tags (comma-separated)"
    )

    # ======================
    # PRICING
    # ======================
    list_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="List price per unit (USD)"
    )

    web_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Website/customer price per unit (USD)"
    )

    # ======================
    # SAP INTEGRATION
    # ======================
    sap_case_qty = models.IntegerField(
        null=True,
        blank=True,
        help_text="Base units per case (SAP_Base_Unit_To_CS)"
    )

    sap_case_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Case gross weight in pounds"
    )

    sap_case_volume = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Case volume in cubic feet"
    )

    # ======================
    # PHYSICAL SPECIFICATIONS
    # ======================
    material = models.CharField(
        max_length=100,
        db_index=True,
        null=True,
        blank=True,
        help_text="Item material (e.g., Vitrified Ceramic, Soda Lime Glass)"
    )

    dimensions = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Combined dimensions string"
    )

    length = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Length in inches"
    )

    width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Width in inches"
    )

    height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Height in inches"
    )

    capacity = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Volume capacity (e.g., 12 oz, 500ml)"
    )

    color = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Product color"
    )

    # ======================
    # MEDIA
    # ======================
    thumbnail = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Primary product image URL (600x600)"
    )

    assets = models.TextField(
        null=True,
        blank=True,
        help_text="Additional image URLs (comma-separated)"
    )

    beauty_gallery = models.TextField(
        null=True,
        blank=True,
        help_text="Lifestyle/beauty shot URLs (comma-separated)"
    )

    brand_thumbnail = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Brand logo URL"
    )

    # ======================
    # STATUS & FLAGS
    # ======================
    status = models.CharField(
        max_length=20,
        help_text="DataFeed status (Draft/Active)"
    )

    catalog_status = models.CharField(
        max_length=20,
        help_text="Catalog status (New/Active)"
    )

    is_new_feature = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Featured as new product"
    )

    is_sampleable = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Available for sampling"
    )

    # ======================
    # PRODUCT RELATIONSHIPS
    # ======================
    variations = models.TextField(
        null=True,
        blank=True,
        help_text="Product variant SKUs (comma-separated)"
    )

    variation_of = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Parent product SKU if this is a variant"
    )

    related_products = models.TextField(
        null=True,
        blank=True,
        help_text="Related product SKUs (comma-separated)"
    )

    suggested_substitute = models.TextField(
        null=True,
        blank=True,
        help_text="Substitute product SKUs (comma-separated)"
    )

    direct_match = models.TextField(
        null=True,
        blank=True,
        help_text="Direct match product SKUs (comma-separated)"
    )

    # ======================
    # METADATA
    # ======================
    created = models.DateField(
        help_text="Created date in DataFeed"
    )

    last_modified = models.DateField(
        help_text="Last modified date in DataFeed"
    )

    imported_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when imported into our system"
    )

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['sku']

        indexes = [
            models.Index(fields=['catalog_brand', 'catalog_category']),
            models.Index(fields=['material']),
            models.Index(fields=['catalog_collection']),
            models.Index(fields=['family']),
            models.Index(fields=['is_new_feature']),
            models.Index(fields=['is_sampleable']),
            models.Index(fields=['last_modified']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.product_name}"

    def get_case_price(self):
        """Calculate price per case"""
        if self.web_price and self.sap_case_qty:
            return self.web_price * self.sap_case_qty
        return None

    def get_image_urls(self):
        """Get list of all image URLs"""
        urls = []
        if self.thumbnail:
            urls.append(self.thumbnail)
        if self.assets:
            urls.extend([url.strip() for url in self.assets.split(',') if url.strip()])
        if self.beauty_gallery:
            urls.extend([url.strip() for url in self.beauty_gallery.split(',') if url.strip()])
        return urls

    def get_related_skus(self):
        """Get all related product SKUs"""
        skus = []
        if self.related_products:
            skus.extend([sku.strip() for sku in self.related_products.split(',') if sku.strip()])
        if self.suggested_substitute:
            skus.extend([sku.strip() for sku in self.suggested_substitute.split(',') if sku.strip()])
        return list(set(skus))  # Remove duplicates


class ProductBrand(models.Model):
    """
    Deduplicated brand list for efficient filtering
    """
    name = models.CharField(max_length=100, unique=True)
    product_count = models.IntegerField(default=0)
    thumbnail = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'product_brands'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.product_count} products)"


class ProductCategory(models.Model):
    """
    Product category hierarchy
    """
    name = models.CharField(max_length=100, unique=True)
    product_count = models.IntegerField(default=0)
    subcategories = models.TextField(null=True, blank=True, help_text="Comma-separated subcategories")

    class Meta:
        db_table = 'product_categories'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.product_count} products)"


class ProductImportLog(models.Model):
    """
    Track import history and statistics
    """
    imported_at = models.DateTimeField(default=timezone.now)
    source_file = models.CharField(max_length=500, help_text="XML file path or URL")
    products_added = models.IntegerField(default=0)
    products_updated = models.IntegerField(default=0)
    products_total = models.IntegerField(default=0)
    duration_seconds = models.FloatField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'product_import_logs'
        ordering = ['-imported_at']

    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{status} - {self.imported_at} - {self.products_total} products"
