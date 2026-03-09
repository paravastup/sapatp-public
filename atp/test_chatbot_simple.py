#!/usr/bin/env python3
"""Simple chatbot backend test without Unicode issues"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')
django.setup()

from chatbot.services.ollama_client import OllamaClient
from chatbot.services.intent_classifier import IntentClassifier
from chatbot.services.entity_extractor import EntityExtractor

print("\n" + "="*60)
print("CHATBOT BACKEND TEST")
print("="*60)

# Test 1: Ollama Connection
print("\n[TEST 1] Ollama Connection...")
ollama = OllamaClient()
if ollama.test_connection():
    print("SUCCESS: Ollama connected")
    response = ollama.generate("Say hello", temperature=0.1)
    if response:
        print(f"  Generation test: {response[:50]}...")
else:
    print("FAILED: Could not connect to Ollama")
    sys.exit(1)

# Test 2: Intent Classification
print("\n[TEST 2] Intent Classification...")
classifier = IntentClassifier(ollama)

test_queries = [
    ("What's the stock of product 46888?", "stock_query"),
    ("When is the next delivery?", "delivery_query"),
    ("Email me the results", "export_request"),
    ("Hello", "greeting"),
]

correct = 0
for query, expected in test_queries:
    intent, conf = classifier.classify(query)
    if intent == expected:
        correct += 1
        print(f"  PASS: '{query[:40]}' -> {intent}")
    else:
        print(f"  FAIL: '{query[:40]}' -> Expected {expected}, got {intent}")

print(f"  Accuracy: {(correct/len(test_queries))*100:.1f}%")

# Test 3: Entity Extraction
print("\n[TEST 3] Entity Extraction...")
extractor = EntityExtractor(ollama)

test_cases = [
    ("Check stock for products 12345, 67890", ["12345", "67890"]),
    ("Use plant 9995", "9995"),
]

for query, expected in test_cases:
    entities = extractor.extract(query, 'stock_query')
    if isinstance(expected, list):
        if set(entities.get('product_numbers', [])) == set(expected):
            print(f"  PASS: Found products {expected}")
        else:
            print(f"  FAIL: Expected {expected}, got {entities.get('product_numbers')}")
    else:
        if entities.get('plant_code') == expected:
            print(f"  PASS: Found plant {expected}")
        else:
            print(f"  FAIL: Expected plant {expected}, got {entities.get('plant_code')}")

print("\n" + "="*60)
print("BACKEND TESTS COMPLETE")
print("="*60 + "\n")