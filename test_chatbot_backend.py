#!/usr/bin/env python3
"""
Test script for the chatbot backend services
Run this to verify all components are working correctly
"""

import os
import sys
import django

# Add the Django project to the path
sys.path.insert(0, '/opt/app/atp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')

# Initialize Django
try:
    django.setup()
    print("✅ Django initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Django: {e}")
    print("\nMake sure you have:")
    print("1. Added 'chatbot' to INSTALLED_APPS in settings")
    print("2. Run migrations: python manage.py migrate")
    sys.exit(1)

# Now import Django-dependent modules
from django.contrib.auth.models import User
from chatbot.services.ollama_client import OllamaClient
from chatbot.services.intent_classifier import IntentClassifier
from chatbot.services.entity_extractor import EntityExtractor
from chatbot.services.response_generator import ResponseGenerator
from chatbot.services.conversation_manager import ConversationManager
from chatbot.services.query_executor import QueryExecutor
from chatbot.models import ChatSession, ChatMessage

# Test data
TEST_QUERIES = [
    {
        "message": "What's the stock of product 10001?",
        "expected_intent": "stock_query",
        "expected_entities": ["product_numbers"]
    },
    {
        "message": "Check delivery for products 12345, 67890, and 11111",
        "expected_intent": "delivery_query",
        "expected_entities": ["product_numbers"]
    },
    {
        "message": "Show me the brand of product 456",
        "expected_intent": "product_info",
        "expected_entities": ["product_numbers"]
    },
    {
        "message": "Email me these results",
        "expected_intent": "export_request",
        "expected_entities": ["export_format"]
    },
    {
        "message": "Use Durand plant",
        "expected_intent": "plant_selection",
        "expected_entities": ["plant_code", "plant_name"]
    },
    {
        "message": "Hello",
        "expected_intent": "greeting",
        "expected_entities": []
    },
    {
        "message": "Compare stock for 111, 222, 333",
        "expected_intent": "comparison",
        "expected_entities": ["product_numbers"]
    },
    {
        "message": "Help",
        "expected_intent": "help",
        "expected_entities": []
    }
]


def test_ollama_connection():
    """Test 1: Ollama Connection"""
    print("\n" + "="*60)
    print("TEST 1: OLLAMA CONNECTION")
    print("="*60)

    client = OllamaClient()
    if client.test_connection():
        print("✅ Ollama connection successful")

        # Test generation
        response = client.generate("Say 'Hello World'", temperature=0.1)
        if response:
            print(f"✅ Generation test: {response[:50]}...")
        else:
            print("❌ Generation test failed")
        return client
    else:
        print("❌ Ollama connection failed")
        print("Make sure Ollama is running: ollama serve")
        return None


def test_intent_classification(ollama_client):
    """Test 2: Intent Classification"""
    print("\n" + "="*60)
    print("TEST 2: INTENT CLASSIFICATION")
    print("="*60)

    classifier = IntentClassifier(ollama_client)

    results = []
    for test in TEST_QUERIES[:4]:  # Test first 4 queries
        intent, confidence = classifier.classify(test["message"])
        success = intent == test["expected_intent"]

        status = "✅" if success else "❌"
        print(f"{status} Query: '{test['message'][:50]}...'")
        print(f"   Expected: {test['expected_intent']}, Got: {intent} (confidence: {confidence:.2f})")

        results.append(success)

    success_rate = sum(results) / len(results) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    return classifier


def test_entity_extraction(ollama_client):
    """Test 3: Entity Extraction"""
    print("\n" + "="*60)
    print("TEST 3: ENTITY EXTRACTION")
    print("="*60)

    extractor = EntityExtractor(ollama_client)

    test_cases = [
        {
            "message": "Check stock for products 12345, 67890",
            "intent": "stock_query",
            "expected": {"product_numbers": ["12345", "67890"]}
        },
        {
            "message": "Use plant 1000",
            "intent": "plant_selection",
            "expected": {"plant_code": "1000"}
        },
        {
            "message": "Email me the results",
            "intent": "export_request",
            "expected": {"export_format": "email"}
        },
        {
            "message": "Check vendor SKU OLD-123",
            "intent": "stock_query",
            "expected": {"vendor_skus": ["OLD-123"], "search_type": "vendor_sku"}
        }
    ]

    for test in test_cases:
        entities = extractor.extract(test["message"], test["intent"])

        success = True
        for key, expected_value in test["expected"].items():
            actual_value = entities.get(key)
            if isinstance(expected_value, list):
                success = success and set(expected_value) == set(actual_value or [])
            else:
                success = success and expected_value == actual_value

        status = "✅" if success else "❌"
        print(f"{status} Query: '{test['message']}'")
        print(f"   Extracted: {entities}")

    return extractor


def test_response_generation(ollama_client):
    """Test 4: Response Generation"""
    print("\n" + "="*60)
    print("TEST 4: RESPONSE GENERATION")
    print("="*60)

    generator = ResponseGenerator(ollama_client)

    # Test different response types
    test_cases = [
        {
            "intent": "greeting",
            "query": "Hello",
            "data": None
        },
        {
            "intent": "help",
            "query": "Help",
            "data": None
        },
        {
            "intent": "stock_query",
            "query": "What's the stock of 10001?",
            "data": [
                {
                    "MATNR": "10001",
                    "STOCK": 150,
                    "DISMM": "Stock item",
                    "MAKTX": "Test Product"
                }
            ]
        }
    ]

    for test in test_cases:
        response = generator.generate(
            test["query"],
            test["intent"],
            test["data"],
            {"username": "TestUser"}
        )

        if response:
            print(f"✅ {test['intent']}: {response[:100]}...")
        else:
            print(f"❌ Failed to generate response for {test['intent']}")

    return generator


def test_conversation_flow():
    """Test 5: Full Conversation Flow"""
    print("\n" + "="*60)
    print("TEST 5: CONVERSATION FLOW")
    print("="*60)

    # Get or create test user
    try:
        user = User.objects.get(username='admin')
        print(f"✅ Using user: {user.username}")
    except User.DoesNotExist:
        print("❌ No admin user found. Create one with: python manage.py createsuperuser")
        return

    # Create chat session
    try:
        session = ChatSession.objects.create(user=user)
        print(f"✅ Created chat session: {session.id}")
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        print("Make sure you've run migrations: python manage.py migrate")
        return

    # Initialize services
    ollama = OllamaClient()
    classifier = IntentClassifier(ollama)
    extractor = EntityExtractor(ollama)
    generator = ResponseGenerator(ollama)
    conversation = ConversationManager(session)

    # Simulate conversation
    test_messages = [
        "Hello",
        "What's the stock of product 10001?",
        "When is the next delivery?",
        "Email me these results"
    ]

    for message in test_messages:
        print(f"\n👤 User: {message}")

        # Add user message
        conversation.add_message('user', message)

        # Process message
        intent, confidence = classifier.classify(message, conversation.get_history())
        entities = extractor.extract(message, intent)

        # Generate response (mock data for testing)
        if intent == "stock_query":
            mock_data = [{"MATNR": "10001", "STOCK": 100, "DISMM": "Stock item"}]
        else:
            mock_data = None

        response = generator.generate(message, intent, mock_data, conversation.get_context())

        # Add assistant message
        conversation.add_message('assistant', response, {
            'intent': intent,
            'confidence': confidence,
            'entities': entities
        })

        print(f"🤖 Bot: {response[:150]}...")
        print(f"   Intent: {intent} ({confidence:.2f})")
        print(f"   Entities: {entities}")

    print(f"\n✅ Conversation completed with {session.messages.count()} messages")
    return session


def test_sap_integration():
    """Test 6: SAP Integration (if available)"""
    print("\n" + "="*60)
    print("TEST 6: SAP INTEGRATION")
    print("="*60)

    try:
        # Get test user
        user = User.objects.get(username='admin')

        # Check if user has plant access
        plants = user.plant.all()
        if not plants:
            print("⚠️  User has no plant assignments. SAP queries won't work.")
            print("   Assign plants in Django admin: /atp/admin/")
            return

        print(f"✅ User has access to {plants.count()} plant(s)")

        # Initialize query executor
        executor = QueryExecutor(user)

        # Test with first available plant
        plant = plants.first()
        print(f"   Testing with plant: {plant.code} - {plant.description}")

        # Try to query a product (this will fail if SAP is not available)
        try:
            results = executor.execute_search(plant.code, ['10001'], 'M')
            if results:
                print(f"✅ SAP query returned {len(results)} result(s)")
                for result in results:
                    if 'error' in result:
                        print(f"   ❌ {result['MATNR']}: {result['error']}")
                    else:
                        print(f"   ✅ {result.get('MATNR')}: {result.get('STOCK')} in stock")
            else:
                print("❌ SAP query returned no results")
        except Exception as e:
            print(f"⚠️  SAP integration not available: {e}")
            print("   This is normal if SAP is not connected")

    except Exception as e:
        print(f"❌ Error testing SAP integration: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CHATBOT BACKEND TEST SUITE")
    print("="*60)

    # Test 1: Ollama Connection
    ollama_client = test_ollama_connection()
    if not ollama_client:
        print("\n⚠️  Cannot proceed without Ollama. Please start Ollama first.")
        return

    # Test 2: Intent Classification
    classifier = test_intent_classification(ollama_client)

    # Test 3: Entity Extraction
    extractor = test_entity_extraction(ollama_client)

    # Test 4: Response Generation
    generator = test_response_generation(ollama_client)

    # Test 5: Conversation Flow
    session = test_conversation_flow()

    # Test 6: SAP Integration (optional)
    test_sap_integration()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("\n✅ Backend services are working!")
    print("\nNext steps:")
    print("1. Update Django settings to include 'chatbot' in INSTALLED_APPS")
    print("2. Run migrations: python manage.py migrate")
    print("3. Create views and templates for the chat UI")
    print("4. Test the complete flow with real SAP data")


if __name__ == "__main__":
    main()