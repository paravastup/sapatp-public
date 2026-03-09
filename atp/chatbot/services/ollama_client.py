"""
Ollama API client for interacting with the Gemma3:4b model
"""

import requests
import json
import logging
import time
from typing import Dict, Tuple, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama API communication"""

    def __init__(self):
        """Initialize Ollama client with configuration"""
        # Get configuration from settings or use defaults
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'gemma3:4b')
        # Use atp-chatbot for intent/entity (trained), but gemma3:4b for responses (general text)
        self.intent_model = 'atp-chatbot'
        self.response_model = 'gemma3:4b'  # Use base model for natural language generation
        self.timeout = getattr(settings, 'OLLAMA_TIMEOUT', 30)
        self.max_retries = 3

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.3, max_tokens: int = 200, use_intent_model: bool = False) -> Optional[str]:
        """
        Generate text using Ollama API

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            temperature: Control randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens to generate
            use_intent_model: If True, use atp-chatbot (intent model), else use gemma3:4b (response model)

        Returns:
            Generated text or None if error
        """
        # Choose model: atp-chatbot for intent/entity, gemma3:4b for responses
        model_to_use = self.intent_model if use_intent_model else self.response_model

        payload = {
            'model': model_to_use,
            'prompt': prompt,
            'stream': False,
            'keep_alive': '15m',  # Keep model in memory for 15 minutes (avoids 2-5s loading overhead)
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
                'stop': ['```', 'json', 'JSON']  # Stop if model tries to output JSON
            }
        }

        if system_prompt:
            # Combine system prompt with user prompt for Gemma
            full_prompt = f"{system_prompt}\n\n{prompt}"
            payload['prompt'] = full_prompt

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                response = requests.post(
                    f'{self.base_url}/api/generate',
                    json=payload,
                    timeout=self.timeout
                )

                elapsed_time = time.time() - start_time
                logger.info(f"Ollama response time: {elapsed_time:.2f}s")

                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")

            except requests.Timeout:
                logger.warning(f"Ollama request timeout (attempt {attempt + 1}/{self.max_retries})")
            except requests.ConnectionError:
                logger.error(f"Cannot connect to Ollama at {self.base_url}")
                break
            except Exception as e:
                logger.error(f"Ollama API error: {str(e)}")

        return None

    def classify_intent(self, user_message: str, conversation_history: List[Dict] = None) -> Tuple[str, float]:
        """
        Classify user intent using Gemma3

        Args:
            user_message: The user's input message
            conversation_history: Previous conversation for context

        Returns:
            Tuple of (intent, confidence)
        """
        # Optimized prompt: Reduced from ~170 tokens to ~60 tokens
        system_prompt = """Classify intent: stock_query, delivery_query, product_info, plant_selection, export_request, comparison, sample_request, help, greeting, clarification_needed.
Reply with intent name only."""

        # Simplified prompt - no context for intent (not needed with fast-path routing)
        prompt = f'Query: "{user_message}"\nIntent:'

        response = self.generate(prompt, system_prompt, temperature=0.1, max_tokens=20, use_intent_model=True)

        if response:
            # Extract intent from response
            intent = response.lower().strip()

            # Validate intent
            valid_intents = [
                'stock_query', 'delivery_query', 'product_info',
                'plant_selection', 'export_request', 'comparison',
                'sample_request', 'help', 'greeting', 'clarification_needed'
            ]

            if intent in valid_intents:
                # High confidence for clear classification
                confidence = 0.9
            else:
                # Low confidence, default to clarification
                intent = 'clarification_needed'
                confidence = 0.3

            logger.info(f"Intent classified: {intent} (confidence: {confidence})")
            return intent, confidence
        else:
            # Fallback if Ollama fails
            return self._fallback_intent_classification(user_message)

    def _fallback_intent_classification(self, message: str) -> Tuple[str, float]:
        """
        Simple keyword-based fallback classification

        Args:
            message: User message

        Returns:
            Tuple of (intent, confidence)
        """
        message_lower = message.lower()

        # Keyword mappings
        if any(word in message_lower for word in ['stock', 'availability', 'inventory', 'how many', 'quantity']):
            return 'stock_query', 0.7
        elif any(word in message_lower for word in ['delivery', 'eta', 'arrival', 'coming', 'transit']):
            return 'delivery_query', 0.7
        elif any(word in message_lower for word in ['brand', 'origin', 'weight', 'upc', 'ean', 'specs']):
            return 'product_info', 0.7
        elif any(word in message_lower for word in ['excel', 'email', 'export', 'download', 'send', 'pdf']):
            return 'export_request', 0.7
        elif any(word in message_lower for word in ['plant', 'location', 'site', 'warehouse']):
            return 'plant_selection', 0.7
        elif any(word in message_lower for word in ['compare', 'difference', 'versus', 'vs']):
            return 'comparison', 0.7
        elif any(word in message_lower for word in ['help', 'how to', 'what can', 'guide']):
            return 'help', 0.7
        elif any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
            return 'greeting', 0.8
        else:
            return 'clarification_needed', 0.5

    def extract_entities(self, user_message: str, intent: str,
                        conversation_history: List[Dict] = None) -> Dict:
        """
        Extract entities from user message with conversation context

        Args:
            user_message: The user's input
            intent: The classified intent
            conversation_history: Previous conversation for context

        Returns:
            Dictionary of extracted entities
        """
        # Optimized prompt: Reduced from ~220 tokens to ~80 tokens
        # Context handling moved to entity_extractor.py, no need to duplicate here
        system_prompt = f"""Extract entities from query (intent: {intent}).
Find: product_numbers, vendor_skus, plant_codes, export_format.
JSON only: {{"product_numbers": ["123"], "plant_code": "1001", "export_format": null}}"""

        prompt = f'"{user_message}"'

        response = self.generate(prompt, system_prompt, temperature=0.1, max_tokens=150, use_intent_model=True)

        if response:
            try:
                # Strip markdown code blocks if present
                json_str = response.strip()
                if json_str.startswith('```'):
                    # Remove ```json and ``` markers
                    json_str = json_str.split('\n', 1)[1] if '\n' in json_str else json_str
                    json_str = json_str.rsplit('```', 1)[0] if '```' in json_str else json_str
                    json_str = json_str.strip()

                # Try to parse JSON response
                entities = json.loads(json_str)
                logger.info(f"Entities extracted: {entities}")
                return entities
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Ollama: {response[:200]}")

        # Fallback to regex extraction
        return self._fallback_entity_extraction(user_message)

    def _fallback_entity_extraction(self, message: str) -> Dict:
        """
        Regex-based fallback entity extraction

        Args:
            message: User message

        Returns:
            Dictionary of extracted entities
        """
        import re

        entities = {
            'product_numbers': [],
            'vendor_skus': [],
            'plant_code': None,
            'plant_name': None,
            'export_format': None,
            'search_type': 'arc_sku'  # Default
        }

        # Extract product numbers (4-8 digits)
        product_numbers = re.findall(r'\b\d{4,8}\b', message)
        entities['product_numbers'] = list(set(product_numbers))

        # Extract vendor SKUs (pattern like ABC-123)
        vendor_skus = re.findall(r'\b[A-Z]{2,4}-\d{3,6}\b', message, re.IGNORECASE)
        entities['vendor_skus'] = list(set(vendor_skus))

        # Detect if it's vendor SKU search
        if vendor_skus or 'vendor' in message.lower() or 'old' in message.lower():
            entities['search_type'] = 'vendor_sku'

        # Extract plant codes
        plant_codes = re.findall(r'\b(1001|1002|1003)\b', message)
        if plant_codes:
            entities['plant_code'] = plant_codes[0]

        # Extract plant names
        plant_names = {
            'demo_corp': '1001',
            'millville': '1002',
            'cardinal': '1001',
            'arc canada': '1003'
        }
        message_lower = message.lower()
        for name, code in plant_names.items():
            if name in message_lower:
                entities['plant_name'] = name.title()
                entities['plant_code'] = code
                break

        # Extract export format
        if 'excel' in message_lower or 'xls' in message_lower:
            entities['export_format'] = 'excel'
        elif 'email' in message_lower:
            entities['export_format'] = 'email'
        elif 'pdf' in message_lower:
            entities['export_format'] = 'pdf'

        logger.info(f"Fallback entities extracted: {entities}")
        return entities

    def generate_response(self, user_query: str, intent: str, data: Optional[List[Dict]] = None,
                          context: Dict = None) -> str:
        """
        Generate natural language response based on data

        Args:
            user_query: Original user question
            intent: The classified intent
            data: SAP query results or other data
            context: Conversation context

        Returns:
            Natural language response
        """
        # Optimized prompt: Reduced from ~180 tokens to ~50 tokens + data
        system_prompt = """Product assistant. Be concise, friendly. Use **bold** for numbers."""

        # Simplified data format
        data_str = ""
        if data and len(data) > 0:
            for item in data[:3]:  # Reduced from 5 to 3 items
                if 'error' in item:
                    data_str += f"{item.get('MATNR')}: {item['error']}\n"
                else:
                    data_str += f"{item.get('MATNR')}: {item.get('STOCK')} pcs, delivery {item.get('EEIND', 'none')}\n"
            if len(data) > 3:
                data_str += f"...+{len(data)-3} more\n"
        else:
            data_str = "No data"

        prompt = f'Q: "{user_query}"\nData:\n{data_str}\nResponse:'

        response = self.generate(prompt, system_prompt, temperature=0.7, max_tokens=200)

        if response:
            return response
        else:
            # Fallback response
            return self._generate_fallback_response(intent, data)

    def _generate_fallback_response(self, intent: str, data: Optional[List[Dict]] = None) -> str:
        """
        Generate fallback response without LLM

        Args:
            intent: The classified intent
            data: Query results

        Returns:
            Fallback response string
        """
        if intent == 'stock_query' and data:
            if len(data) == 1:
                item = data[0]
                if 'error' in item:
                    return f"I couldn't find product {item.get('MATNR', 'Unknown')}. Please check the product number."
                return f"Product **{item['MATNR']}** has **{item['STOCK']}** pieces in stock."
            else:
                return f"I found {len(data)} products. Check the results panel for details."

        elif intent == 'delivery_query' and data:
            item = data[0] if data else {}
            if item.get('EEIND'):
                return f"Next delivery for **{item['MATNR']}** is on **{item['EEIND']}**."
            else:
                return f"No scheduled deliveries for **{item.get('MATNR', 'this product')}**."

        elif intent == 'help':
            return """I can help you with:
• Check stock: "What's the stock of 10001?"
• Delivery info: "When is the next delivery?"
• Export data: "Send me the results by email"
• Product details: "What's the brand of product 123?"

Just ask naturally!"""

        elif intent == 'greeting':
            return "Hello! How can I help you check product availability today?"

        else:
            return "I'm not sure I understand. Could you please rephrase your question?"

    def test_connection(self) -> bool:
        """
        Test connection to Ollama API

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"Ollama connection successful. Available models: {[m['name'] for m in models]}")
                return True
        except Exception as e:
            logger.error(f"Ollama connection failed: {str(e)}")

        return False