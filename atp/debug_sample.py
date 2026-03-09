import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from products.services import ProductService

# Get product enrichment (what chatbot should be using)
product = ProductService.get_product_enrichment('10002')

print("Product data from get_product_enrichment:")
print(f"  family: {product.get('family')}")
print(f"  catalog_category: {product.get('catalog_category')}")
print(f"  website_subcategories: {product.get('website_subcategories')}")
print(f"  label: {product.get('label')}")

# Test URL building with this data
url = ProductService.build_product_url(
    family=product.get('family'),
    category=product.get('catalog_category'),
    subcategories=product.get('website_subcategories'),
    label=product.get('label')
)

print(f"\nURL built: {url}")
print(f"URL length: {len(url)}")

# Check if any fields are None
if not product.get('family'):
    print("WARNING: family is None!")
if not product.get('catalog_category'):
    print("WARNING: catalog_category is None!")
if not product.get('website_subcategories'):
    print("WARNING: website_subcategories is None!")
if not product.get('label'):
    print("WARNING: label is None!")
