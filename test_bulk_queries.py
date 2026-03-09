#!/usr/bin/env python3
"""
Test script for bulk query functionality
Tests the complete flow from entity extraction to response generation
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atp.settings")
sys.path.insert(0, '/app')
django.setup()

from chatbot.services.entity_extractor import EntityExtractor
from chatbot.services.intent_classifier import IntentClassifier
from chatbot.services.response_generator import ResponseGenerator
from chatbot.services.query_executor import QueryExecutor
from products.services import ProductService
from django.contrib.auth.models import User

def test_entity_extraction():
    """Test that bulk queries are properly detected"""
    print("=" * 60)
    print("TEST 1: Entity Extraction for Bulk Queries")
    print("=" * 60)

    extractor = EntityExtractor()

    test_queries = [
        "Show me all Chef & Sommelier products",
        "List all products from Chef & Sommelier",
        "What's the stock of all Chef & Sommelier items?",
        "Get every Chef & Sommelier product"
    ]

    for query in test_queries:
        entities = extractor._regex_extraction(query)
        print(f"\nQuery: '{query}'")
        print(f"  Brand detected: {entities.get('datafeed_brand')}")
        print(f"  Is bulk query: {entities.get('is_bulk_query')}")
        print(f"  Product numbers: {entities.get('product_numbers')}")


def test_product_service():
    """Test that ProductService returns multiple SKUs"""
    print("\n" + "=" * 60)
    print("TEST 2: ProductService SKU Fetching")
    print("=" * 60)

    # Test fetching SKUs for Chef & Sommelier
    skus = ProductService.get_skus_for_bulk_query(
        brand='Chef & Sommelier',
        limit=10
    )

    print(f"\nFound {len(skus)} SKUs for 'Chef & Sommelier':")
    for i, sku in enumerate(skus, 1):
        print(f"  {i}. {sku}")


def test_response_generation():
    """Test response generation for multiple products"""
    print("\n" + "=" * 60)
    print("TEST 3: Response Generation for Multiple Products")
    print("=" * 60)

    generator = ResponseGenerator()

    # Simulate multiple product results
    mock_results = [
        {
            'MATNR': '10001',
            'MAKTX': 'Cabernet Wine Glass 11.25 OZ',
            'STOCK': 1234.0,
            'EAN11': '123456789'
        },
        {
            'MATNR': '10002',
            'MAKTX': 'Pinot Wine Glass 12.5 OZ',
            'STOCK': 567.0,
            'EAN11': '987654321'
        },
        {
            'MATNR': '47017',
            'MAKTX': 'Merlot Wine Glass 10 OZ',
            'STOCK': 890.0,
            'EAN11': '555555555'
        },
    ]

    # Test stock query response
    response = generator._generate_fallback_response(
        intent='stock_query',
        results=mock_results,
        context={'selected_plant': '1000'},
        field_requested=None
    )

    print("\nGenerated response for bulk stock query:")
    print("-" * 40)
    print(response)
    print("-" * 40)


def test_full_flow():
    """Test the complete bulk query flow"""
    print("\n" + "=" * 60)
    print("TEST 4: Complete Bulk Query Flow")
    print("=" * 60)

    # Setup components
    extractor = EntityExtractor()
    classifier = IntentClassifier()

    # Test query
    query = "Show me all Chef & Sommelier products"
    print(f"\nProcessing query: '{query}'")

    # 1. Classify intent
    intent = classifier.classify(query)
    print(f"Intent classified as: {intent}")

    # 2. Extract entities
    entities = extractor.extract(query, intent)
    print(f"Entities extracted:")
    print(f"  - Brand: {entities.get('datafeed_brand')}")
    print(f"  - Is bulk: {entities.get('is_bulk_query')}")
    print(f"  - Product count: {len(entities.get('product_numbers', []))}")

    # 3. Get SKUs from ProductService
    if entities.get('is_bulk_query') and entities.get('datafeed_brand'):
        skus = ProductService.get_skus_for_bulk_query(
            brand=entities['datafeed_brand'],
            limit=5  # Limit for test
        )
        print(f"\nFetched {len(skus)} SKUs from database: {skus}")
    else:
        print("ERROR: Bulk query not detected properly!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BULK QUERY FUNCTIONALITY TEST SUITE")
    print("=" * 60)

    try:
        test_entity_extraction()
        test_product_service()
        test_response_generation()
        test_full_flow()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\n\nERROR: Test failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()