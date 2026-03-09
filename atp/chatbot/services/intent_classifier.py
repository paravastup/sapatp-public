"""
Intent classification service for the chatbot
"""

import logging
from typing import Tuple, List, Dict, Optional
from .ollama_client import OllamaClient
from .cache_utils import PatternCache

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Service for classifying user intents"""

    # Define all supported intents
    INTENTS = {
        'stock_query': 'Checking product stock levels',
        'delivery_query': 'Checking delivery dates and quantities',
        'product_info': 'Getting product details (brand, origin, specs)',
        'plant_selection': 'Selecting or changing plant',
        'export_request': 'Exporting results (Excel/Email/PDF)',
        'comparison': 'Comparing multiple products',
        'help': 'Getting help or instructions',
        'greeting': 'Greetings and small talk',
        'clarification_needed': 'Ambiguous query requiring more info'
    }

    # Intent examples for better classification
    INTENT_EXAMPLES = {
        'stock_query': [
            "What's the stock of product 10001?",
            "Check availability for SKU 123456",
            "How many units of 11111 do we have?",
            "Show inventory levels for product 999",
            "Do we have stock for 12345?"
        ],
        'delivery_query': [
            "When is the next delivery for 10001?",
            "What's the ETA for product 123?",
            "Show delivery schedule",
            "What's coming in next week?",
            "Check in-transit quantity"
        ],
        'product_info': [
            "What's the brand of product 10001?",
            "Where is product 123 manufactured?",
            "What's the case pack for SKU 789?",
            "Get UPC code for product 456",
            "Show product specifications",
            "What's the price of 10001?",
            "How much does product FP906 cost?",
            "Show me the description of 12345",
            "What category is product 10002 in?",
            "Display image for SKU 789"
        ],
        'plant_selection': [
            "Use Durand plant",
            "Switch to plant 1000",
            "Check Plant City location",
            "Change to Brand_D site",
            "Select plant 1002"
        ],
        'export_request': [
            "Send me the results by email",
            "Download as Excel",
            "Export to PDF",
            "Email this report",
            "Get Excel file"
        ],
        'comparison': [
            "Compare products 111 and 222",
            "Which has more stock?",
            "Show differences between these items",
            "Compare availability",
            "What's the difference?"
        ],
        'help': [
            "What can you do?",
            "Help",
            "How do I search?",
            "Show me examples",
            "What queries can I make?"
        ],
        'greeting': [
            "Hello",
            "Hi",
            "Good morning",
            "Hey there",
            "Good afternoon"
        ]
    }

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize intent classifier

        Args:
            ollama_client: Optional OllamaClient instance
        """
        self.ollama = ollama_client or OllamaClient()
        self.confidence_threshold = 0.6
        self.pattern_cache = PatternCache(cache_name='intent_cache')

    def classify(self, user_message: str, conversation_history: List[Dict] = None) -> Tuple[str, float]:
        """
        Classify user intent with 3-tier optimization:
        1. Pattern cache (0.001s) - Check if we've seen this pattern before
        2. Rule-based (0.01s) - Regex pattern matching
        3. LLM (2-5s) - Ollama API call (only if needed)

        Args:
            user_message: The user's input message
            conversation_history: Previous conversation for context

        Returns:
            Tuple of (intent, confidence)
        """
        if not user_message or not user_message.strip():
            return 'clarification_needed', 0.0

        # CACHE CHECK: Try pattern cache FIRST (0.001s)
        cached_result = self.pattern_cache.get_cached_intent(user_message)
        if cached_result:
            intent, confidence = cached_result
            logger.info(f"[CACHE HIT] Intent: '{intent}' (confidence {confidence:.2f}) for: '{user_message[:50]}...'")
            return intent, confidence

        # FAST PATH: Try rule-based classification (regex pattern matching - 0.01s)
        # This skips expensive LLM call for 90% of queries
        intent, confidence = self._rule_based_classification(user_message)

        # If rule-based confidence is high enough, use it (skip LLM!)
        if confidence >= self.confidence_threshold:
            logger.info(f"[FAST PATH] Intent classified: '{intent}' with confidence {confidence:.2f} for message: '{user_message[:50]}...'")
            # Cache the result for future queries with similar pattern
            self.pattern_cache.cache_intent(user_message, intent, confidence)
            return intent, confidence

        # SLOW PATH: Rule-based failed, use Ollama LLM classification (2-5s)
        logger.info(f"[SLOW PATH] Rule-based confidence too low ({confidence:.2f}), calling LLM for: '{user_message[:50]}...'")
        intent, confidence = self.ollama.classify_intent(user_message, conversation_history)

        # Log and cache classification result
        logger.info(f"Intent classified via LLM: '{intent}' with confidence {confidence:.2f}")
        self.pattern_cache.cache_intent(user_message, intent, confidence)

        return intent, confidence

    def _rule_based_classification(self, message: str) -> Tuple[str, float]:
        """
        Rule-based classification using keywords and patterns

        Args:
            message: User message

        Returns:
            Tuple of (intent, confidence)
        """
        message_lower = message.lower().strip()

        # Check each intent's keywords
        intent_scores = {}

        # Stock query patterns
        stock_keywords = ['stock', 'availability', 'inventory', 'how many', 'quantity', 'available', 'have']
        stock_score = sum(1 for kw in stock_keywords if kw in message_lower)
        if stock_score > 0:
            intent_scores['stock_query'] = stock_score / len(stock_keywords)

        # Delivery query patterns
        delivery_keywords = ['delivery', 'eta', 'arrival', 'coming', 'transit', 'scheduled', 'next', 'when']
        delivery_score = sum(1 for kw in delivery_keywords if kw in message_lower)
        if delivery_score > 0:
            intent_scores['delivery_query'] = delivery_score / len(delivery_keywords)

        # Product info patterns (including DataFeed data: price, description, image, category, etc.)
        info_keywords = ['brand', 'origin', 'weight', 'upc', 'ean', 'barcode', 'specs', 'case pack', 'manufactured',
                         'price', 'cost', 'description', 'details', 'info', 'information', 'category', 'material',
                         'dimensions', 'collection', 'image', 'photo', 'picture']
        info_score = sum(1 for kw in info_keywords if kw in message_lower)
        if info_score > 0:
            intent_scores['product_info'] = info_score / len(info_keywords)

        # Export patterns
        export_keywords = ['excel', 'email', 'export', 'download', 'send', 'pdf', 'file', 'spreadsheet']
        export_score = sum(1 for kw in export_keywords if kw in message_lower)
        if export_score > 0:
            intent_scores['export_request'] = export_score / len(export_keywords)

        # Plant selection patterns
        plant_keywords = ['plant', 'location', 'site', 'warehouse', 'durand', 'millville', 'cardinal', '1000', '1002', '1001']
        plant_score = sum(1 for kw in plant_keywords if kw in message_lower)
        if plant_score > 0:
            intent_scores['plant_selection'] = plant_score / len(plant_keywords)

        # Comparison patterns
        compare_keywords = ['compare', 'difference', 'versus', 'vs', 'between', 'which']
        compare_score = sum(1 for kw in compare_keywords if kw in message_lower)
        if compare_score > 0:
            intent_scores['comparison'] = compare_score / len(compare_keywords)

        # Sample request patterns
        sample_keywords = ['sample', 'sampling', 'try', 'request sample', 'get sample', 'order sample',
                          'sample this', 'can i sample', 'send sample', 'sample product']
        sample_score = sum(1 for kw in sample_keywords if kw in message_lower)
        if sample_score > 0:
            intent_scores['sample_request'] = sample_score / len(sample_keywords)

        # Help patterns
        help_keywords = ['help', 'how to', 'what can', 'guide', 'instructions', 'example', 'show me how']
        help_score = sum(1 for kw in help_keywords if kw in message_lower)
        if help_score > 0:
            intent_scores['help'] = help_score / len(help_keywords)

        # Greeting patterns
        greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        for greeting in greeting_keywords:
            if message_lower.startswith(greeting):
                intent_scores['greeting'] = 0.9
                break

        # Find intent with highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent] * 0.8, 0.9)  # Cap at 0.9 for rule-based
            return best_intent, confidence

        # Default to clarification needed
        return 'clarification_needed', 0.4

    def get_intent_description(self, intent: str) -> str:
        """
        Get human-readable description of an intent

        Args:
            intent: Intent name

        Returns:
            Description string
        """
        return self.INTENTS.get(intent, "Unknown intent")

    def get_intent_examples(self, intent: str) -> List[str]:
        """
        Get example queries for an intent

        Args:
            intent: Intent name

        Returns:
            List of example queries
        """
        return self.INTENT_EXAMPLES.get(intent, [])

    def requires_clarification(self, confidence: float) -> bool:
        """
        Check if clarification is needed based on confidence

        Args:
            confidence: Confidence score

        Returns:
            True if clarification needed
        """
        return confidence < self.confidence_threshold