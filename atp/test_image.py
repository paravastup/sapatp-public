import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

# Test field detection
from chatbot.views import _detect_field_request

message = "show me the product image of 46961?"
intent = "product_info"

field = _detect_field_request(message, intent)
print(f"Message: {message}")
print(f"Detected field: {field}")

# Check if it's in non_stock_fields
non_stock_fields = ['image', 'price', 'list_price', 'web_price', 'upc', 'brand', 'origin',
                   'description', 'category', 'material', 'dimensions', 'collection', 'weight',
                   'case_pack', 'vendor_sku']
print(f"Is non-stock field: {field in non_stock_fields}")
