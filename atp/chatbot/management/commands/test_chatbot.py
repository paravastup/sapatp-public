"""
Django management command to test the chatbot backend
Usage: python manage.py test_chatbot
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chatbot.services.ollama_client import OllamaClient
from chatbot.services.intent_classifier import IntentClassifier
from chatbot.services.entity_extractor import EntityExtractor
from chatbot.services.response_generator import ResponseGenerator
from chatbot.services.conversation_manager import ConversationManager
from chatbot.services.query_executor import QueryExecutor
from chatbot.models import ChatSession, ChatMessage
import sys


class Command(BaseCommand):
    help = 'Test the chatbot backend services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            type=str,
            default='all',
            help='Which test to run: all, ollama, intent, entity, response, conversation, sap'
        )
        parser.add_argument(
            '--query',
            type=str,
            help='Test a specific query'
        )

    def handle(self, *args, **options):
        test_type = options['test']
        query = options.get('query')

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('CHATBOT BACKEND TESTING'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Initialize Ollama client
        ollama = OllamaClient()

        if test_type == 'all' or test_type == 'ollama':
            self.test_ollama(ollama)

        if test_type == 'all' or test_type == 'intent':
            self.test_intent(ollama, query)

        if test_type == 'all' or test_type == 'entity':
            self.test_entity(ollama, query)

        if test_type == 'all' or test_type == 'response':
            self.test_response(ollama)

        if test_type == 'all' or test_type == 'conversation':
            self.test_conversation(ollama)

        if test_type == 'all' or test_type == 'sap':
            self.test_sap()

        if query and test_type not in ['intent', 'entity']:
            self.test_single_query(ollama, query)

    def test_ollama(self, ollama):
        """Test Ollama connection"""
        self.stdout.write('\nTEST 1: OLLAMA CONNECTION')
        self.stdout.write('-' * 40)

        if ollama.test_connection():
            self.stdout.write(self.style.SUCCESS('✅ Ollama connection successful'))

            # Test generation
            response = ollama.generate("Say 'Hello World'", temperature=0.1)
            if response:
                self.stdout.write(self.style.SUCCESS(f'✅ Generation test: {response[:50]}...'))
            else:
                self.stdout.write(self.style.ERROR('❌ Generation test failed'))
        else:
            self.stdout.write(self.style.ERROR('❌ Ollama connection failed'))
            self.stdout.write('Make sure Ollama is running: ollama serve')

    def test_intent(self, ollama, query=None):
        """Test intent classification"""
        self.stdout.write('\nTEST 2: INTENT CLASSIFICATION')
        self.stdout.write('-' * 40)

        classifier = IntentClassifier(ollama)

        if query:
            # Test specific query
            intent, confidence = classifier.classify(query)
            self.stdout.write(f'Query: "{query}"')
            self.stdout.write(f'Intent: {intent} (confidence: {confidence:.2f})')
        else:
            # Test multiple queries
            test_queries = [
                ("What's the stock of product 10001?", "stock_query"),
                ("When is the next delivery?", "delivery_query"),
                ("Email me the results", "export_request"),
                ("Hello", "greeting"),
                ("Help", "help"),
            ]

            correct = 0
            for query_text, expected_intent in test_queries:
                intent, confidence = classifier.classify(query_text)
                is_correct = intent == expected_intent
                correct += is_correct

                status = self.style.SUCCESS('✅') if is_correct else self.style.ERROR('❌')
                self.stdout.write(f'{status} "{query_text[:40]}..."')
                self.stdout.write(f'   Expected: {expected_intent}, Got: {intent} ({confidence:.2f})')

            accuracy = (correct / len(test_queries)) * 100
            self.stdout.write(f'\nAccuracy: {accuracy:.1f}%')

    def test_entity(self, ollama, query=None):
        """Test entity extraction"""
        self.stdout.write('\nTEST 3: ENTITY EXTRACTION')
        self.stdout.write('-' * 40)

        extractor = EntityExtractor(ollama)

        if query:
            # Test specific query
            entities = extractor.extract(query, 'stock_query')
            self.stdout.write(f'Query: "{query}"')
            self.stdout.write(f'Entities: {entities}')
        else:
            # Test multiple cases
            test_cases = [
                ("Check stock for products 12345, 67890", ["12345", "67890"]),
                ("Use plant 1000", "1000"),
                ("Email me the results", "email"),
                ("Check vendor SKU OLD-123", "OLD-123"),
            ]

            for query_text, expected in test_cases:
                entities = extractor.extract(query_text, 'stock_query')
                self.stdout.write(f'Query: "{query_text}"')
                self.stdout.write(f'   Extracted: {entities}')

    def test_response(self, ollama):
        """Test response generation"""
        self.stdout.write('\nTEST 4: RESPONSE GENERATION')
        self.stdout.write('-' * 40)

        generator = ResponseGenerator(ollama)

        # Test greeting
        response = generator.generate_greeting_response({'username': 'TestUser'})
        self.stdout.write(f'Greeting: {response[:100]}...')

        # Test help
        response = generator.generate_help_response()
        self.stdout.write(f'Help: {response[:100]}...')

        # Test stock response with data
        mock_data = [
            {
                "MATNR": "10001",
                "STOCK": 150,
                "DISMM": "Stock item",
                "MAKTX": "Test Product"
            }
        ]
        response = generator.generate("What's the stock?", "stock_query", mock_data, {})
        self.stdout.write(f'Stock Response: {response[:100]}...')

    def test_conversation(self, ollama):
        """Test conversation flow"""
        self.stdout.write('\nTEST 5: CONVERSATION FLOW')
        self.stdout.write('-' * 40)

        # Get or create test user
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_user('test_chatbot', 'test@example.com', 'test123')
            self.stdout.write(f'Using user: {user.username}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {e}'))
            return

        # Create session
        session = ChatSession.objects.create(user=user)
        self.stdout.write(f'Created session: {session.id}')

        # Initialize services
        classifier = IntentClassifier(ollama)
        extractor = EntityExtractor(ollama)
        generator = ResponseGenerator(ollama)
        conversation = ConversationManager(session)

        # Test conversation
        test_messages = [
            "Hello",
            "What's the stock of product 10001?",
            "Email me the results"
        ]

        for message in test_messages:
            # Process message
            conversation.add_message('user', message)
            intent, confidence = classifier.classify(message, conversation.get_history())
            entities = extractor.extract(message, intent)

            # Generate response
            response = generator.generate(message, intent, None, conversation.get_context())
            conversation.add_message('assistant', response, {
                'intent': intent,
                'confidence': confidence,
                'entities': entities
            })

            self.stdout.write(f'\n👤 User: {message}')
            self.stdout.write(f'🤖 Bot: {response[:100]}...')
            self.stdout.write(f'   Intent: {intent} ({confidence:.2f})')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Conversation completed with {session.messages.count()} messages'))

        # Clean up test session
        session.delete()

    def test_sap(self):
        """Test SAP integration"""
        self.stdout.write('\nTEST 6: SAP INTEGRATION')
        self.stdout.write('-' * 40)

        try:
            # Get test user
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(self.style.WARNING('No admin user found'))
                return

            # Check plant access
            plants = user.plant.all()
            if not plants:
                self.stdout.write(self.style.WARNING('User has no plant assignments'))
                return

            self.stdout.write(f'User has access to {plants.count()} plant(s)')

            # Test query executor
            executor = QueryExecutor(user)
            plant = plants.first()

            try:
                results = executor.execute_search(plant.code, ['10001'], 'M')
                if results:
                    self.stdout.write(self.style.SUCCESS(f'✅ SAP query returned {len(results)} result(s)'))
                    for result in results[:3]:
                        if 'error' in result:
                            self.stdout.write(f'   {result["MATNR"]}: {result["error"]}')
                        else:
                            self.stdout.write(f'   {result.get("MATNR")}: {result.get("STOCK")} in stock')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'SAP not available: {e}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def test_single_query(self, ollama, query):
        """Test a single query through the full pipeline"""
        self.stdout.write('\nSINGLE QUERY TEST')
        self.stdout.write('-' * 40)
        self.stdout.write(f'Query: "{query}"')

        # Process through pipeline
        classifier = IntentClassifier(ollama)
        extractor = EntityExtractor(ollama)
        generator = ResponseGenerator(ollama)

        intent, confidence = classifier.classify(query)
        entities = extractor.extract(query, intent)
        response = generator.generate(query, intent, None, {})

        self.stdout.write(f'\nIntent: {intent} ({confidence:.2f})')
        self.stdout.write(f'Entities: {entities}')
        self.stdout.write(f'\nResponse: {response}')