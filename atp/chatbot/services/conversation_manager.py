"""
Conversation manager service for handling chat sessions and context
"""

import logging
import json
import re
from typing import Dict, List, Optional
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def strip_emojis(text: str) -> str:
    """
    Remove 4-byte UTF-8 characters (emojis) from text for MySQL utf8 compatibility

    Args:
        text: Input text potentially containing emojis

    Returns:
        Text with emojis removed
    """
    # Pattern to match 4-byte UTF-8 characters (emojis)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


class ConversationManager:
    """Manage conversation state and context"""

    CONFIDENCE_THRESHOLD = 0.6
    MAX_HISTORY_LENGTH = 10  # Keep last 10 messages for context

    def __init__(self, session):
        """
        Initialize conversation manager

        Args:
            session: ChatSession model instance
        """
        self.session = session
        self.context = self.session.get_context() if session else {}

    def get_context(self) -> Dict:
        """
        Get current conversation context

        Returns:
            Context dictionary
        """
        return self.context

    def update_context(self, updates: Dict):
        """
        Update conversation context

        Args:
            updates: Dictionary of context updates
        """
        self.context.update(updates)
        if self.session:
            self.session.update_context(self.context)

    def get_history(self, limit: int = 5) -> List[Dict]:
        """
        Get conversation history

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        if not self.session:
            return []

        try:
            messages = self.session.messages.order_by('-timestamp')[:limit]
            return [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat()
                }
                for msg in reversed(messages)
            ]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    def add_message(self, role: str, content: str, metadata: Dict = None) -> 'ChatMessage':
        """
        Add message to conversation

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata

        Returns:
            Created ChatMessage instance
        """
        if not self.session:
            return None

        try:
            from ..models import ChatMessage

            # Strip emojis from content for MySQL utf8 compatibility
            safe_content = strip_emojis(content)

            message = ChatMessage.objects.create(
                session=self.session,
                role=role,
                content=safe_content
            )

            if metadata:
                message.set_metadata(metadata)
                message.save()

            # Update session timestamp
            self.session.save()

            # Keep unlimited history per session (removed auto-deletion for full conversation thread)
            # Note: Users can start new session via "New Chat" button if desired
            # self._trim_history()  # Commented out to maintain full conversation history

            return message

        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return None

    def _trim_history(self):
        """Trim conversation history to prevent unlimited growth"""
        try:
            message_count = self.session.messages.count()
            if message_count > self.MAX_HISTORY_LENGTH * 2:
                # Keep only recent messages
                old_messages = self.session.messages.order_by('timestamp')[:-self.MAX_HISTORY_LENGTH]
                old_messages.delete()
                logger.info(f"Trimmed {len(old_messages)} old messages from session {self.session.id}")
        except Exception as e:
            logger.error(f"Error trimming history: {e}")

    def handle_low_confidence(self, intent: str, confidence: float, user_message: str) -> Dict:
        """
        Handle cases where LLM confidence is low

        Args:
            intent: Detected intent
            confidence: Confidence score
            user_message: Original user message

        Returns:
            Response dictionary
        """
        if confidence < self.CONFIDENCE_THRESHOLD:
            # Offer clarification options
            response = {
                'response': "I'm not quite sure what you're looking for. Are you trying to:",
                'suggestions': [
                    "Check product stock",
                    "See delivery dates",
                    "Get product information",
                    "Export results",
                    "Something else"
                ],
                'requires_clarification': True,
                'original_intent': intent,
                'confidence': confidence
            }

            # Store in context for follow-up
            self.update_context({
                'pending_clarification': True,
                'unclear_message': user_message,
                'suggested_intent': intent
            })

            return response

        return None

    def needs_plant_selection(self, user) -> bool:
        """
        Check if plant selection is needed

        Args:
            user: Django user object

        Returns:
            True if plant selection needed
        """
        # Check if plant already selected in context
        if self.context.get('selected_plant'):
            return False

        # Check if user has multiple plants
        try:
            plant_count = user.plant.count()
            return plant_count > 1
        except:
            return False

    def get_selected_plant(self) -> Optional[str]:
        """
        Get currently selected plant

        Returns:
            Plant code or None
        """
        return self.context.get('selected_plant')

    def set_selected_plant(self, plant_code: str):
        """
        Set selected plant

        Args:
            plant_code: Plant code to select
        """
        self.update_context({'selected_plant': plant_code})
        logger.info(f"Plant {plant_code} selected for session {self.session.id}")

    def cache_results(self, results: List[Dict], product_numbers: List[str] = None,
                      search_type: str = None):
        """
        Cache query results in context

        Args:
            results: Query results to cache
            product_numbers: List of product numbers queried
            search_type: 'arc_sku' or 'vendor_sku'
        """
        # Store ALL results for export functionality
        # User requested no limits on bulk queries and exports
        cached_results = results

        # Extract product numbers from results if not provided
        if not product_numbers and results:
            product_numbers = []
            for result in results:
                product = result.get('MATNR') or result.get('product')
                if product and product not in product_numbers:
                    product_numbers.append(product)

        context_update = {
            'last_results': cached_results,
            'last_query_time': timezone.now().isoformat(),
            'result_count': len(results),
            'last_product_numbers': product_numbers or [],
            'products_in_results': product_numbers or []
        }

        # Set current product if only one product queried
        if product_numbers and len(product_numbers) == 1:
            context_update['current_product'] = product_numbers[0]

        # Store search type if provided
        if search_type:
            context_update['last_search_type'] = search_type

        self.update_context(context_update)
        logger.info(f"Cached {len(results)} results for products: {product_numbers}")

    def get_cached_results(self) -> Optional[List[Dict]]:
        """
        Get cached results from context

        Returns:
            Cached results or None
        """
        return self.context.get('last_results')

    def has_recent_results(self, minutes: int = 5) -> bool:
        """
        Check if there are recent cached results

        Args:
            minutes: Time window in minutes

        Returns:
            True if recent results exist
        """
        last_query_time = self.context.get('last_query_time')
        if not last_query_time:
            return False

        try:
            from datetime import datetime
            last_time = datetime.fromisoformat(last_query_time)
            time_diff = timezone.now() - last_time
            return time_diff < timedelta(minutes=minutes)
        except:
            return False

    def clear_context(self):
        """Clear conversation context (for new topic/reset)"""
        self.context = {}
        if self.session:
            self.session.update_context({})
        logger.info(f"Context cleared for session {self.session.id if self.session else 'N/A'}")

    def end_session(self):
        """Mark session as ended"""
        if self.session:
            self.session.is_active = False
            self.session.save()
            logger.info(f"Session {self.session.id} ended")

    def get_session_analytics(self) -> Dict:
        """
        Get analytics for current session

        Returns:
            Analytics dictionary
        """
        if not self.session:
            return {}

        try:
            from ..models import IntentLog

            messages = self.session.messages.all()
            intent_logs = IntentLog.objects.filter(message__session=self.session)

            analytics = {
                'session_id': self.session.id,
                'duration_minutes': (timezone.now() - self.session.created_at).seconds / 60,
                'total_messages': messages.count(),
                'user_messages': messages.filter(role='user').count(),
                'assistant_messages': messages.filter(role='assistant').count(),
                'sap_queries': messages.filter(sap_query_executed=True).count(),
                'intents_detected': list(intent_logs.values_list('detected_intent', flat=True)),
                'avg_confidence': intent_logs.aggregate(models.Avg('confidence'))['confidence__avg'] or 0,
                'selected_plant': self.context.get('selected_plant'),
                'exports_requested': self.context.get('export_count', 0)
            }

            return analytics

        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return {}

    def suggest_next_actions(self, current_intent: str, results: List[Dict] = None) -> List[str]:
        """
        Suggest relevant next actions based on current context

        Args:
            current_intent: The current intent
            results: Current query results

        Returns:
            List of suggested actions
        """
        suggestions = []

        if current_intent == 'stock_query' and results:
            suggestions.extend([
                "Check delivery schedule for these products",
                "Export results to Excel",
                "Compare with other products",
                "Get detailed product information"
            ])
        elif current_intent == 'delivery_query':
            suggestions.extend([
                "Check current stock levels",
                "Export delivery schedule",
                "Set up delivery alerts"
            ])
        elif current_intent == 'product_info':
            suggestions.extend([
                "Check stock availability",
                "View similar products",
                "Export product specifications"
            ])
        elif current_intent == 'export_request':
            suggestions.extend([
                "Search for more products",
                "Change export format",
                "Schedule regular reports"
            ])
        else:
            # Generic suggestions
            suggestions.extend([
                "Check product stock",
                "View delivery schedules",
                "Search for products",
                "Get help"
            ])

        return suggestions[:4]  # Limit to 4 suggestions

    def get_last_products(self) -> List[str]:
        """
        Get product numbers from last query

        Returns:
            List of product numbers from last query
        """
        return self.context.get('last_product_numbers', [])

    def get_current_product(self) -> Optional[str]:
        """
        Get current product in focus (for single-product conversations)

        Returns:
            Current product number or None
        """
        return self.context.get('current_product')

    def is_followup_question(self, user_message: str) -> bool:
        """
        Detect if this is a follow-up question referring to previous context

        Args:
            user_message: User's message

        Returns:
            True if appears to be a follow-up question
        """
        message_lower = user_message.lower()

        # Check for pronouns and references
        followup_indicators = [
            'it', 'its', 'this', 'that', 'these', 'those', 'them',
            'the product', 'the item', 'the same', 'same one',
            'which one', 'what about', 'how about', 'also'
        ]

        # Check if message contains follow-up indicators
        has_indicator = any(indicator in message_lower for indicator in followup_indicators)

        # Check if message doesn't contain product numbers (likely follow-up)
        import re
        has_product_number = bool(re.search(r'\b\d{4,}\b', user_message))

        # It's a follow-up if it has indicators or asks a question without specifying products
        is_question = any(q in message_lower for q in ['what', 'when', 'where', 'how', 'which', 'who', '?'])

        return has_indicator or (is_question and not has_product_number)

    def set_current_products(self, product_numbers: List[str], search_type: str = None):
        """
        Update context with currently queried products

        Args:
            product_numbers: List of product numbers being queried
            search_type: 'arc_sku' or 'vendor_sku'
        """
        context_update = {
            'last_product_numbers': product_numbers
        }

        # Set current product if only one
        if len(product_numbers) == 1:
            context_update['current_product'] = product_numbers[0]
        else:
            context_update['current_product'] = None

        if search_type:
            context_update['last_search_type'] = search_type

        self.update_context(context_update)
        logger.info(f"Set current products: {product_numbers}")

    def track_action(self, intent: str, field_requested: str = None, action_description: str = None):
        """
        Track the last action taken for intelligent follow-ups

        Args:
            intent: The intent that was executed
            field_requested: Specific field user asked for (upc, stock, delivery, brand, etc.)
            action_description: Human-readable description of the action
        """
        context_update = {
            'last_intent': intent,
            'last_action_time': timezone.now().isoformat()
        }

        if field_requested:
            context_update['last_field_requested'] = field_requested

        if action_description:
            context_update['last_action_description'] = action_description

        self.update_context(context_update)
        logger.info(f"Tracked action: {intent}, field: {field_requested}")

    def get_last_action(self) -> Dict:
        """
        Get information about the last action taken

        Returns:
            Dictionary with last_intent, last_field_requested, etc.
        """
        return {
            'intent': self.context.get('last_intent'),
            'field': self.context.get('last_field_requested'),
            'description': self.context.get('last_action_description'),
            'products': self.context.get('last_product_numbers', [])
        }

    def detect_action_repeat(self, user_message: str) -> bool:
        """
        Detect if user wants to repeat the last action

        Args:
            user_message: User's message

        Returns:
            True if user wants to repeat an action
        """
        message_lower = user_message.lower()

        repeat_phrases = [
            'do the same', 'same thing', 'same for', 'same with',
            'also check', 'also show', 'also get',
            'how about', 'what about',
            'check that for', 'show that for',
            'repeat for', 'again for'
        ]

        return any(phrase in message_lower for phrase in repeat_phrases)

    def store_pending_query(self, query_data: Dict):
        """
        Store a pending query for large result sets

        Args:
            query_data: Dictionary containing query parameters
                - products: List of product SKUs
                - brand/category/material: Filter criteria
                - plant_code: Selected plant
                - mode: Search mode (M/O)
                - intent: Original intent
        """
        self.update_context({
            'pending_query': query_data,
            'pending_query_time': timezone.now().isoformat()
        })
        logger.info(f"Stored pending query for {len(query_data.get('products', []))} products")

    def get_pending_query(self) -> Optional[Dict]:
        """
        Get stored pending query

        Returns:
            Pending query data or None
        """
        return self.context.get('pending_query')

    def clear_pending_query(self):
        """Clear pending query from context"""
        if 'pending_query' in self.context:
            del self.context['pending_query']
        if 'pending_query_time' in self.context:
            del self.context['pending_query_time']
        self.update_context(self.context)
        logger.info("Cleared pending query from context")