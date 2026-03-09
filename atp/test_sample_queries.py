import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

import django
django.setup()

from chatbot.services.intent_classifier import IntentClassifier
from chatbot.views import _detect_field_request

print("=== Testing Various Sample Queries ===\n")

classifier = IntentClassifier()

test_queries = [
    "Can I sample product 46961?",
    "I want to try 46888",
    "How do I get a sample of the Cabernet wine glasses?",
    "Sample request for 46961",
    "I'd like to request samples",
    "Can I try this product?",
]

for query in test_queries:
    intent, confidence = classifier.classify(query)
    field = _detect_field_request(query, intent)
    print(f"Query: '{query}'")
    print(f"  Intent: {intent} ({confidence:.2f}) | Field: {field}")
    print()
