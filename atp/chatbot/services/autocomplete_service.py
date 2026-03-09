"""
Autocomplete service for generating search suggestions
"""

import re
import logging
from typing import List, Dict
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class AutocompleteService:
    """Generate autocomplete suggestions for the search interface"""

    # Common query templates
    QUERY_TEMPLATES = [
        "What's the stock of {product}?",
        "Check stock for {product}",
        "Show me stock for {product}",
        "Get stock info for {product}",
        "What's the delivery date for {product}?",
        "When is {product} arriving?",
        "Check delivery for {product}",
        "Show me the UPC for {product}",
        "What's the brand of {product}?",
        "Get product details for {product}",
        "Show me info about {product}",
        "Compare {product} and {other}",
        "Check stock for {product} and {other}",
    ]

    # Common question starters
    QUESTION_STARTERS = [
        "What's the stock",
        "Check stock for",
        "Show me stock",
        "What's the delivery",
        "When is",
        "Check delivery",
        "Show me the UPC",
        "What's the brand",
        "Get product details",
        "Compare products",
    ]

    def __init__(self, user: User = None):
        """
        Initialize autocomplete service

        Args:
            user: Django user for personalized suggestions
        """
        self.user = user

    def get_suggestions(self, partial_query: str, max_suggestions: int = 7) -> List[Dict]:
        """
        Get autocomplete suggestions based on partial query

        Args:
            partial_query: User's partial input
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggestion dictionaries with 'text', 'icon', and 'type' keys
        """
        suggestions = []

        if not partial_query or len(partial_query) < 2:
            # Show common queries if input is empty/short
            return self._get_default_suggestions()

        partial_lower = partial_query.lower().strip()

        # Detect if user is typing a product number
        product_numbers = self._extract_product_numbers(partial_query)

        if product_numbers:
            # Generate suggestions with detected product numbers
            suggestions.extend(self._generate_product_suggestions(product_numbers))
        else:
            # Generate suggestions based on partial text
            suggestions.extend(self._generate_text_suggestions(partial_lower))

        # Limit to max suggestions
        return suggestions[:max_suggestions]

    def _get_default_suggestions(self) -> List[Dict]:
        """Get default suggestions when no input"""
        return [
            {
                'text': "What's the stock of [product number]?",
                'icon': '📦',
                'type': 'template',
                'description': 'Check current stock levels'
            },
            {
                'text': "Check delivery for [product number]",
                'icon': '🚚',
                'type': 'template',
                'description': 'View delivery schedule'
            },
            {
                'text': "Show me product info for [product number]",
                'icon': 'ℹ️',
                'type': 'template',
                'description': 'Get UPC, brand, weight, etc.'
            },
            {
                'text': "Compare products [number1] and [number2]",
                'icon': '📊',
                'type': 'template',
                'description': 'Compare multiple products'
            },
        ]

    def _extract_product_numbers(self, text: str) -> List[str]:
        """
        Extract product numbers from text

        Args:
            text: Input text

        Returns:
            List of detected product numbers
        """
        # Pattern for product numbers (4-8 digits, optionally prefixed with letter)
        pattern = r'\b[A-Z]?\d{4,8}\b'
        products = re.findall(pattern, text, re.IGNORECASE)
        return [p.upper() for p in products]

    def _generate_product_suggestions(self, product_numbers: List[str]) -> List[Dict]:
        """
        Generate suggestions when product numbers are detected

        Args:
            product_numbers: List of detected product numbers

        Returns:
            List of suggestions
        """
        suggestions = []

        if len(product_numbers) == 1:
            product = product_numbers[0]
            suggestions = [
                {
                    'text': f"What's the stock of {product}?",
                    'icon': '📦',
                    'type': 'query',
                    'highlight': product
                },
                {
                    'text': f"Check delivery for {product}",
                    'icon': '🚚',
                    'type': 'query',
                    'highlight': product
                },
                {
                    'text': f"Show me product info for {product}",
                    'icon': 'ℹ️',
                    'type': 'query',
                    'highlight': product
                },
                {
                    'text': f"Get the UPC for {product}",
                    'icon': '🏷️',
                    'type': 'query',
                    'highlight': product
                },
                {
                    'text': f"What's the brand of {product}?",
                    'icon': '🏭',
                    'type': 'query',
                    'highlight': product
                },
            ]
        elif len(product_numbers) >= 2:
            # Multiple products detected
            products_str = " and ".join(product_numbers[:3])  # Show first 3
            suggestions = [
                {
                    'text': f"Check stock for {products_str}",
                    'icon': '📦',
                    'type': 'query',
                    'highlight': products_str
                },
                {
                    'text': f"Compare {products_str}",
                    'icon': '📊',
                    'type': 'query',
                    'highlight': products_str
                },
                {
                    'text': f"Get delivery dates for {products_str}",
                    'icon': '🚚',
                    'type': 'query',
                    'highlight': products_str
                },
            ]

        return suggestions

    def _generate_text_suggestions(self, partial_text: str) -> List[Dict]:
        """
        Generate suggestions based on partial text matching

        Args:
            partial_text: Lowercase partial query

        Returns:
            List of suggestions
        """
        suggestions = []

        # Match against question starters
        for starter in self.QUESTION_STARTERS:
            if starter.lower().startswith(partial_text) or partial_text in starter.lower():
                icon = self._get_icon_for_query(starter)
                suggestions.append({
                    'text': f"{starter} [product number]",
                    'icon': icon,
                    'type': 'template',
                    'highlight': starter
                })

        # If no matches, return common queries
        if not suggestions:
            suggestions = self._get_default_suggestions()[:5]

        return suggestions

    def _get_icon_for_query(self, query_text: str) -> str:
        """
        Get appropriate icon for a query type

        Args:
            query_text: Query text

        Returns:
            Emoji icon
        """
        query_lower = query_text.lower()

        if 'stock' in query_lower:
            return '📦'
        elif 'delivery' in query_lower or 'arriv' in query_lower or 'when' in query_lower:
            return '🚚'
        elif 'upc' in query_lower or 'barcode' in query_lower:
            return '🏷️'
        elif 'brand' in query_lower:
            return '🏭'
        elif 'compare' in query_lower:
            return '📊'
        elif 'info' in query_lower or 'detail' in query_lower:
            return 'ℹ️'
        else:
            return '🔍'

    def get_recent_queries(self, limit: int = 5) -> List[Dict]:
        """
        Get user's recent queries for history

        Args:
            limit: Maximum number of recent queries

        Returns:
            List of recent query dictionaries
        """
        if not self.user:
            return []

        try:
            from ..models import ChatMessage

            # Get recent user messages
            recent_messages = ChatMessage.objects.filter(
                session__user=self.user,
                role='user'
            ).order_by('-timestamp')[:limit]

            return [
                {
                    'text': msg.content,
                    'timestamp': msg.timestamp.strftime('%I:%M %p'),
                    'id': msg.id
                }
                for msg in recent_messages
            ]
        except Exception as e:
            logger.error(f"Error retrieving recent queries: {e}")
            return []
