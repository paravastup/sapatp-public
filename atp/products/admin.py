"""
Admin interface for Plytix product management
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductBrand, ProductCategory, ProductImportLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model
    """
    list_display = [
        'sku', 'product_name_short', 'catalog_brand', 'catalog_category',
        'web_price_display', 'sap_case_qty', 'thumbnail_preview',
        'catalog_status', 'is_new_feature', 'last_modified'
    ]

    list_filter = [
        'catalog_brand', 'catalog_category', 'catalog_status',
        'is_new_feature', 'is_sampleable', 'material', 'family'
    ]

    search_fields = [
        'sku', 'product_name', 'label', 'gtin', 'old_item_number',
        'catalog_brand', 'catalog_collection', 'product_tags'
    ]

    readonly_fields = ['imported_at', 'thumbnail_display', 'get_all_images']

    fieldsets = (
        ('Identifiers', {
            'fields': ('sku', 'gtin', 'old_item_number')
        }),
        ('Product Information', {
            'fields': (
                'product_name', 'label', 'catalog_brand', 'catalog_collection',
                'family', 'catalog_category', 'website_subcategories',
                'long_description', 'short_description', 'product_tags'
            )
        }),
        ('Pricing', {
            'fields': ('list_price', 'web_price')
        }),
        ('SAP Integration', {
            'fields': ('sap_case_qty', 'sap_case_weight', 'sap_case_volume')
        }),
        ('Specifications', {
            'fields': (
                'material', 'dimensions', 'length', 'width', 'height',
                'capacity', 'color'
            )
        }),
        ('Media', {
            'fields': ('thumbnail', 'thumbnail_display', 'get_all_images', 'assets', 'beauty_gallery', 'brand_thumbnail')
        }),
        ('Status', {
            'fields': ('status', 'catalog_status', 'is_new_feature', 'is_sampleable')
        }),
        ('Relationships', {
            'fields': (
                'variations', 'variation_of', 'related_products',
                'suggested_substitute', 'direct_match'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'last_modified', 'imported_at')
        }),
    )

    def product_name_short(self, obj):
        """Truncated product name for list display"""
        if len(obj.product_name) > 50:
            return obj.product_name[:50] + '...'
        return obj.product_name
    product_name_short.short_description = 'Product Name'

    def web_price_display(self, obj):
        """Formatted price display"""
        return f"${obj.web_price}"
    web_price_display.short_description = 'Web Price'
    web_price_display.admin_order_field = 'web_price'

    def thumbnail_preview(self, obj):
        """Small thumbnail preview in list"""
        if obj.thumbnail:
            return format_html('<img src="{}" width="40" height="40"/>', obj.thumbnail)
        return '-'
    thumbnail_preview.short_description = 'Image'

    def thumbnail_display(self, obj):
        """Full thumbnail in detail view"""
        if obj.thumbnail:
            return format_html('<img src="{}" width="300"/>', obj.thumbnail)
        return 'No image'
    thumbnail_display.short_description = 'Product Image'

    def get_all_images(self, obj):
        """Display all product images"""
        urls = obj.get_image_urls()
        if urls:
            html = '<div>'
            for url in urls[:5]:  # Show first 5 images
                html += f'<img src="{url}" width="100" style="margin: 5px;"/> '
            if len(urls) > 5:
                html += f'<p>...and {len(urls) - 5} more images</p>'
            html += '</div>'
            return format_html(html)
        return 'No images'
    get_all_images.short_description = 'All Images'


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    """
    Admin interface for Product Brands
    """
    list_display = ['name', 'product_count', 'brand_thumbnail_preview']
    search_fields = ['name']
    readonly_fields = ['product_count']

    def brand_thumbnail_preview(self, obj):
        """Brand logo preview"""
        if obj.thumbnail:
            return format_html('<img src="{}" height="30"/>', obj.thumbnail)
        return '-'
    brand_thumbnail_preview.short_description = 'Logo'


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Product Categories
    """
    list_display = ['name', 'product_count', 'subcategory_list']
    search_fields = ['name', 'subcategories']
    readonly_fields = ['product_count']

    def subcategory_list(self, obj):
        """Display subcategories"""
        if obj.subcategories:
            subs = obj.subcategories.split(',')
            if len(subs) > 3:
                return ', '.join(subs[:3]) + f' (+{len(subs)-3} more)'
            return ', '.join(subs)
        return '-'
    subcategory_list.short_description = 'Subcategories'


@admin.register(ProductImportLog)
class ProductImportLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Import Logs
    """
    list_display = [
        'imported_at', 'success_icon', 'products_total',
        'products_added', 'products_updated', 'duration_display', 'source_short'
    ]

    list_filter = ['success', 'imported_at']
    search_fields = ['source_file', 'error_message']
    readonly_fields = [
        'imported_at', 'source_file', 'products_added', 'products_updated',
        'products_total', 'duration_seconds', 'success', 'error_message'
    ]

    def success_icon(self, obj):
        """Success/failure icon"""
        if obj.success:
            return format_html('<span style="color: green;">✓ SUCCESS</span>')
        return format_html('<span style="color: red;">✗ FAILED</span>')
    success_icon.short_description = 'Status'

    def duration_display(self, obj):
        """Formatted duration"""
        if obj.duration_seconds < 60:
            return f"{obj.duration_seconds:.1f}s"
        return f"{obj.duration_seconds/60:.1f}m"
    duration_display.short_description = 'Duration'
    duration_display.admin_order_field = 'duration_seconds'

    def source_short(self, obj):
        """Shortened source file path"""
        if len(obj.source_file) > 50:
            return '...' + obj.source_file[-47:]
        return obj.source_file
    source_short.short_description = 'Source'

    def has_add_permission(self, request):
        """Prevent manual creation of import logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make import logs read-only"""
        return False
