import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from chatbot.services.entity_extractor import EntityExtractor

# Test entity extraction
extractor = EntityExtractor()
entities = extractor.extract("show me all flatware products", "product_info")

print(f"Query: 'show me all flatware products'")
print(f"is_bulk_query: {entities.get('is_bulk_query')}")
print(f"datafeed_category: {entities.get('datafeed_category')}")
print(f"datafeed_brand: {entities.get('datafeed_brand')}")
print(f"product_numbers: {entities.get('product_numbers')}")
