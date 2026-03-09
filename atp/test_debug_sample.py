import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from products.services import ProductService

# Get product enrichment
product = ProductService.get_product_enrichment('46961')

print("Product structure:")
for key, value in product.items():
    print(f"  {key}: {value}")

# Check if it has the expected keys
print(f"\nHas 'MATNR': {'MATNR' in product}")
print(f"Has 'sku': {'sku' in product}")
print(f"Has 'plytix': {'plytix' in product}")
