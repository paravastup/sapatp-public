"""
Django management command to import products from Plytix XML feed
Usage: python manage.py import_plytix_feed <xml_file_path>
       python manage.py import_plytix_feed --url https://pim.plytix.com/channels/.../feed
"""
import xml.etree.ElementTree as ET
import time
import requests
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from products.models import Product, ProductBrand, ProductCategory, ProductImportLog


class Command(BaseCommand):
    help = 'Import products from Plytix XML feed'

    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            nargs='?',
            type=str,
            help='Path to XML file or use --url for remote feed'
        )
        parser.add_argument(
            '--url',
            type=str,
            help='URL to fetch XML feed from Plytix'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse XML but do not save to database'
        )

    def handle(self, *args, **options):
        start_time = time.time()

        # Determine source
        if options.get('url'):
            source = options['url']
            xml_content = self.fetch_from_url(source)
        elif options.get('source'):
            source = options['source']
            xml_content = self.read_from_file(source)
        else:
            raise CommandError('Please provide either a file path or --url parameter')

        self.stdout.write(self.style.SUCCESS(f'[*] Starting import from: {source}'))

        # Parse XML
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise CommandError(f'XML parsing error: {e}')

        products_data = []
        brands = set()
        categories = set()

        product_elements = root.findall('product')
        total_products = len(product_elements)

        self.stdout.write(f'Found {total_products} products in feed')

        # Parse each product
        for idx, product_el in enumerate(product_elements, 1):
            if idx % 100 == 0:
                self.stdout.write(f'  Parsing... {idx}/{total_products}')

            try:
                product_data = self.parse_product(product_el)
                products_data.append(product_data)
                brands.add(product_data['catalog_brand'])
                categories.add(product_data['catalog_category'])
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  [!] Skipping product {idx}: {e}')
                )
                continue

        self.stdout.write(self.style.SUCCESS(f'[+] Parsed {len(products_data)} products'))
        self.stdout.write(f'  Brands: {len(brands)}')
        self.stdout.write(f'  Categories: {len(categories)}')

        # Save to database
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes made to database'))
            return

        added, updated = self.save_products(products_data)
        self.update_brands(brands)
        self.update_categories(categories)

        duration = time.time() - start_time

        # Create import log
        ProductImportLog.objects.create(
            source_file=source,
            products_added=added,
            products_updated=updated,
            products_total=len(products_data),
            duration_seconds=duration,
            success=True
        )

        self.stdout.write(self.style.SUCCESS(f'\n[SUCCESS] Import complete!'))
        self.stdout.write(f'  Added: {added} new products')
        self.stdout.write(f'  Updated: {updated} existing products')
        self.stdout.write(f'  Duration: {duration:.1f}s')

    def fetch_from_url(self, url):
        """Fetch XML feed from remote URL"""
        self.stdout.write(f'[*] Fetching from URL...')
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise CommandError(f'Failed to fetch URL: {e}')

    def read_from_file(self, file_path):
        """Read XML feed from local file"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')
        except Exception as e:
            raise CommandError(f'Error reading file: {e}')

    def get_text(self, element, tag, default=''):
        """Safely extract text from XML element"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return default

    def get_decimal(self, element, tag, default=None):
        """Extract decimal value from XML element"""
        text = self.get_text(element, tag)
        if not text:
            return default
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            return default

    def get_int(self, element, tag, default=None):
        """Extract integer value from XML element"""
        text = self.get_text(element, tag)
        if not text:
            return default
        try:
            return int(float(text))  # Handle "6.0" -> 6
        except (ValueError, TypeError):
            return default

    def get_date(self, element, tag, default=None):
        """Extract date from XML element"""
        text = self.get_text(element, tag)
        if not text:
            return default

        # Try common date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y']:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue

        return default

    def get_bool(self, element, tag, default=False):
        """Extract boolean from XML element"""
        text = self.get_text(element, tag).lower()
        if text in ['yes', 'true', '1', 'y']:
            return True
        elif text in ['no', 'false', '0', 'n']:
            return False
        return default

    def parse_product(self, product_el):
        """Parse a single product element into dict"""

        # Required fields
        sku = self.get_text(product_el, 'SKU')
        if not sku:
            raise ValueError('Missing required SKU')

        product_name = self.get_text(product_el, 'Label') or self.get_text(product_el, 'Product_Name')
        if not product_name:
            raise ValueError(f'Missing product name for SKU {sku}')

        catalog_brand = self.get_text(product_el, 'Catalog_Brand')
        if not catalog_brand:
            raise ValueError(f'Missing brand for SKU {sku}')

        catalog_category = self.get_text(product_el, 'Catalog_Category')
        if not catalog_category:
            raise ValueError(f'Missing category for SKU {sku}')

        # Parse all fields
        return {
            # Identifiers
            'sku': sku,
            'gtin': self.get_text(product_el, 'GTIN') or None,
            'old_item_number': self.get_text(product_el, 'Old_Item_Number_Reference') or None,

            # Product Information
            'label': self.get_text(product_el, 'Label'),
            'product_name': product_name,
            'catalog_brand': catalog_brand,
            'catalog_collection': self.get_text(product_el, 'Catalog_Collection') or None,
            'family': self.get_text(product_el, 'Family') or None,
            'categories': self.get_text(product_el, 'Categories') or None,
            'catalog_category': catalog_category,
            'website_subcategories': self.get_text(product_el, 'Website_Subcategories') or None,

            # Descriptions
            'long_description': self.get_text(product_el, 'Long_Description') or None,
            'short_description': self.get_text(product_el, 'Short_Description') or None,
            'product_tags': self.get_text(product_el, 'Product_Tags') or None,

            # Pricing
            'list_price': self.get_decimal(product_el, 'Current_List_Price_Per_PC__USD_', Decimal('0.00')),
            'web_price': self.get_decimal(product_el, 'Website_Price', Decimal('0.00')),

            # SAP Integration
            'sap_case_qty': self.get_int(product_el, 'SAP_Base_Unit_To_CS'),
            'sap_case_weight': self.get_decimal(product_el, 'SAP_Case_Gross_Weight__lbs_'),
            'sap_case_volume': self.get_decimal(product_el, 'SAP_Case_Volume__cu_ft_'),

            # Physical Specifications
            'material': self.get_text(product_el, 'Catalog_Item_Material') or None,
            'dimensions': self.get_text(product_el, 'Item_Dimensions') or None,
            'length': self.get_decimal(product_el, 'Item_Actual_Length__inch_'),
            'width': self.get_decimal(product_el, 'Item_Actual_Width__inch_'),
            'height': self.get_decimal(product_el, 'Item_Actual_Height__inch_'),
            'capacity': self.get_text(product_el, 'Item_Capacity__oz_') or None,
            'color': self.get_text(product_el, 'Item_Color') or None,

            # Media
            'thumbnail': self.get_text(product_el, 'Thumbnail') or None,
            'assets': self.get_text(product_el, 'Assets') or None,
            'beauty_gallery': self.get_text(product_el, 'Beauty_Gallery') or None,
            'brand_thumbnail': self.get_text(product_el, 'Brand_Thumbnail') or None,

            # Status & Flags
            'status': self.get_text(product_el, 'Status', 'Active'),
            'catalog_status': self.get_text(product_el, 'Catalog_Status', 'Active'),
            'is_new_feature': self.get_bool(product_el, 'New_Feature'),
            'is_sampleable': self.get_bool(product_el, 'Sampleable_Products'),

            # Product Relationships
            'variations': self.get_text(product_el, 'Variations') or None,
            'variation_of': self.get_text(product_el, 'Variation_of') or None,
            'related_products': self.get_text(product_el, 'Related_Products') or None,
            'suggested_substitute': self.get_text(product_el, 'Suggested_Substitute') or None,
            'direct_match': self.get_text(product_el, 'Direct_Match') or None,

            # Metadata
            'created': self.get_date(product_el, 'Created') or datetime.now().date(),
            'last_modified': self.get_date(product_el, 'Last_Modified') or datetime.now().date(),
        }

    @transaction.atomic
    def save_products(self, products_data):
        """Bulk create/update products"""
        self.stdout.write('[*] Saving products to database...')

        existing_skus = set(Product.objects.values_list('sku', flat=True))

        products_to_create = []
        products_to_update = []

        for data in products_data:
            if data['sku'] in existing_skus:
                products_to_update.append(data)
            else:
                products_to_create.append(Product(**data))

        # Bulk create new products
        if products_to_create:
            Product.objects.bulk_create(products_to_create, batch_size=500)

        # Update existing products
        updated_count = 0
        for data in products_to_update:
            Product.objects.filter(sku=data['sku']).update(**{
                k: v for k, v in data.items() if k != 'sku'
            })
            updated_count += 1

        return len(products_to_create), updated_count

    def update_brands(self, brands):
        """Update brand counts and create new brands"""
        for brand_name in brands:
            count = Product.objects.filter(catalog_brand=brand_name).count()
            thumbnail = Product.objects.filter(
                catalog_brand=brand_name,
                brand_thumbnail__isnull=False
            ).values_list('brand_thumbnail', flat=True).first()

            ProductBrand.objects.update_or_create(
                name=brand_name,
                defaults={
                    'product_count': count,
                    'thumbnail': thumbnail
                }
            )

    def update_categories(self, categories):
        """Update category counts and subcategories"""
        for category_name in categories:
            count = Product.objects.filter(catalog_category=category_name).count()

            # Collect unique subcategories
            subcats = Product.objects.filter(
                catalog_category=category_name,
                website_subcategories__isnull=False
            ).values_list('website_subcategories', flat=True)

            unique_subcats = set()
            for subcat_str in subcats:
                if subcat_str:
                    unique_subcats.update([s.strip() for s in subcat_str.split(',')])

            ProductCategory.objects.update_or_create(
                name=category_name,
                defaults={
                    'product_count': count,
                    'subcategories': ','.join(sorted(unique_subcats))
                }
            )
