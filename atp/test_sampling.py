import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from products.services import ProductService
from chatbot.services.intent_classifier import IntentClassifier

# Test 1: URL builder
print("=== Test 1: URL Builder ===")
url = ProductService.build_product_url(
    family="Tableware",
    category="Glassware",
    subcategories="Wine",
    label="Cabernet Tall Wine 16.0 Oz"
)
print(f"Generated URL: {url}")

# Test 2: Intent classification
print("\n=== Test 2: Intent Classification ===")
classifier = IntentClassifier()

test_queries = [
    "Can I sample product 10002?",
    "I want to request a sample",
    "How do I get a sample of 10001?",
    "Sample this product please"
]

for query in test_queries:
    intent, confidence = classifier.classify(query)
    print(f"Query: '{query}'")
    print(f"  Intent: {intent} (confidence: {confidence:.2f})")

# Test 3: Field detection
print("\n=== Test 3: Field Detection ===")
from chatbot.views import _detect_field_request

for query in test_queries:
    field = _detect_field_request(query, 'product_info')
    print(f"Query: '{query}'")
    print(f"  Field: {field}")
