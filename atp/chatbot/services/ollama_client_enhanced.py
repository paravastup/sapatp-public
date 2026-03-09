"""
Enhanced Ollama API client with constrained generation and multi-pass verification
For exact value extraction without hallucination
"""

import requests
import json
import logging
import time
import re
from typing import Dict, Tuple, List, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class EnhancedOllamaClient:
    """Enhanced client with extraction-specific features"""

    def __init__(self):
        """Initialize enhanced Ollama client"""
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.intent_model = 'atp-chatbot'  # For intent/entity
        self.extraction_model = 'atp-extraction-v4'  # Using v4 model with 99% accuracy
        self.timeout = getattr(settings, 'OLLAMA_TIMEOUT', 30)
        self.max_retries = 3

    def extract_with_constraints(self, context: str, fields_requested: List[str],
                                  product_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract values with constraints to prevent hallucination

        Args:
            context: The data context (SAP results)
            fields_requested: List of fields to extract
            product_number: Specific product to extract from

        Returns:
            Dictionary with extracted values (null if not found)
        """
        # Build constrained system prompt
        system_prompt = """You are a precise data extraction assistant.

CRITICAL RULES:
1. ONLY extract values that appear EXACTLY in the context
2. If a value is not present, return null
3. NEVER generate or guess values
4. Return valid JSON only

Extract these fields if present in the context:"""

        for field in fields_requested:
            system_prompt += f"\n- {field}"

        # Build extraction prompt
        if product_number:
            prompt = f"""Context: {context}

Extract the requested fields for product {product_number} only.
Return JSON with the fields. Use null for any field not found.

Response:"""
        else:
            prompt = f"""Context: {context}

Extract the requested fields from the context.
Return JSON with the fields. Use null for any field not found.

Response:"""

        # Call with constraints
        payload = {
            'model': self.extraction_model,
            'prompt': prompt,
            'system': system_prompt,
            'stream': False,
            'options': {
                'temperature': 0.1,  # Very low for deterministic extraction
                'top_p': 0.1,  # Narrow sampling
                'top_k': 10,  # Limited choices
                'repeat_penalty': 1.0,  # No penalty - we want exact copying
                'num_predict': 200,  # Enough for JSON
                'stop': ['}', '```']  # Stop after JSON closes
            },
            'format': {  # JSON schema constraint (if Ollama supports it)
                'type': 'object',
                'properties': {field: {'type': ['string', 'null']} for field in fields_requested},
                'required': fields_requested
            }
        }

        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                # Parse JSON response
                try:
                    # Clean up if wrapped in markdown
                    if '```' in response_text:
                        response_text = response_text.split('```')[1].strip()
                        if response_text.startswith('json'):
                            response_text = response_text[4:].strip()

                    extracted = json.loads(response_text)

                    # Verify extracted values exist in context
                    verified = {}
                    for field, value in extracted.items():
                        if value and self._verify_value_in_context(value, context):
                            verified[field] = value
                        else:
                            verified[field] = None

                    return verified

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response_text[:200]}")
                    return {field: None for field in fields_requested}

            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {field: None for field in fields_requested}

        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return {field: None for field in fields_requested}

    def extract_with_multi_pass(self, context: str, fields_requested: List[str],
                                 product_number: Optional[str] = None,
                                 num_passes: int = 5) -> Dict[str, Any]:
        """
        Extract values with multiple passes for critical fields
        Only accept values that appear consistently

        Args:
            context: The data context
            fields_requested: Fields to extract
            product_number: Specific product
            num_passes: Number of extraction attempts (default 5)

        Returns:
            Dictionary with high-confidence extracted values
        """
        all_results = []

        # Run extraction multiple times
        for i in range(num_passes):
            result = self.extract_with_constraints(context, fields_requested, product_number)
            all_results.append(result)
            logger.debug(f"Pass {i+1}/{num_passes}: {result}")

        # Consolidate results - only keep values that appear in majority
        consolidated = {}
        for field in fields_requested:
            values = [r.get(field) for r in all_results if r.get(field) is not None]

            if not values:
                consolidated[field] = None
            else:
                # Find most common value
                from collections import Counter
                value_counts = Counter(values)
                most_common_value, count = value_counts.most_common(1)[0]

                # Only accept if appears in >60% of passes
                if count >= num_passes * 0.6:
                    consolidated[field] = most_common_value
                    logger.info(f"Field '{field}' extracted with {count}/{num_passes} consistency: {most_common_value}")
                else:
                    consolidated[field] = None
                    logger.warning(f"Field '{field}' inconsistent across passes: {value_counts}")

        return consolidated

    def _verify_value_in_context(self, value: str, context: str) -> bool:
        """
        Verify that an extracted value actually exists in the context

        Args:
            value: The extracted value
            context: The source context

        Returns:
            True if value exists in context
        """
        if not value:
            return False

        # Exact match
        if value in context:
            return True

        # Case-insensitive match
        if value.lower() in context.lower():
            return True

        # Check for numeric values that might be formatted differently
        if value.isdigit():
            # Remove formatting from context and check again
            context_numbers = re.findall(r'\b\d+\b', context)
            if value in context_numbers:
                return True

        return False

    def extract_upc_with_fallback(self, context: str, product_number: Optional[str] = None) -> Optional[str]:
        """
        Special method for UPC extraction with multiple fallback strategies

        Args:
            context: The data context
            product_number: Specific product number

        Returns:
            UPC value or None
        """
        # Strategy 1: Multi-pass extraction
        result = self.extract_with_multi_pass(context, ['upc'], product_number, num_passes=5)
        if result.get('upc'):
            return result['upc']

        # Strategy 2: Regex fallback
        upc_patterns = [
            r'UPC[:\s]+(\d{10,14})',
            r'EAN[:\s]+(\d{10,14})',
            r'barcode[:\s]+(\d{10,14})',
            r'\b(\d{13})\b',  # Common UPC length
            r'\b(\d{12})\b',  # Another common length
        ]

        for pattern in upc_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                # If product number specified, try to find UPC near it
                if product_number:
                    # Look for UPC near the product number
                    product_pattern = rf'{re.escape(product_number)}.*?(\d{{10,14}})'
                    product_matches = re.findall(product_pattern, context)
                    if product_matches:
                        return product_matches[0]

                # Return first match
                return matches[0]

        # Strategy 3: Ask LLM with very explicit prompt
        explicit_prompt = f"""Find the exact UPC/EAN/barcode number in this text.
It should be 10-14 digits long.
Copy it EXACTLY as shown.

Text: {context}

UPC number (digits only):"""

        response = self.generate(explicit_prompt, temperature=0.0, max_tokens=20)
        if response and response.isdigit() and 10 <= len(response) <= 14:
            return response

        return None

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.3, max_tokens: int = 200,
                 use_intent_model: bool = False) -> Optional[str]:
        """
        Generate text using Ollama API (original method preserved)

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Control randomness
            max_tokens: Maximum tokens to generate
            use_intent_model: Use atp-chatbot for intent

        Returns:
            Generated text or None
        """
        model_to_use = self.intent_model if use_intent_model else self.extraction_model

        payload = {
            'model': model_to_use,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
            }
        }

        if system_prompt:
            payload['system'] = system_prompt

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f'{self.base_url}/api/generate',
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()

            except Exception as e:
                logger.error(f"Ollama API error (attempt {attempt + 1}): {e}")

        return None

    def classify_intent(self, user_message: str, conversation_history: List[Dict] = None) -> Tuple[str, float]:
        """Original intent classification (preserved)"""
        system_prompt = """Classify intent: stock_query, delivery_query, product_info, plant_selection, export_request, comparison, help, greeting, clarification_needed.
Reply with intent name only."""

        prompt = f'Query: "{user_message}"\nIntent:'

        response = self.generate(prompt, system_prompt, temperature=0.1, max_tokens=20, use_intent_model=True)

        if response:
            intent = response.lower().strip()

            valid_intents = [
                'stock_query', 'delivery_query', 'product_info',
                'plant_selection', 'export_request', 'comparison',
                'help', 'greeting', 'clarification_needed'
            ]

            if intent in valid_intents:
                confidence = 0.9
            else:
                intent = 'clarification_needed'
                confidence = 0.3

            logger.info(f"Intent classified: {intent} (confidence: {confidence})")
            return intent, confidence
        else:
            return 'clarification_needed', 0.5

    def extract_entities(self, user_message: str, intent: str,
                         conversation_history: List[Dict] = None) -> Dict:
        """
        Enhanced entity extraction with verification

        Args:
            user_message: User's input
            intent: Classified intent
            conversation_history: Previous conversation

        Returns:
            Dictionary of extracted entities
        """
        # For extraction queries, use constrained extraction
        if intent == 'product_info':
            # Detect which fields are requested
            fields = self._detect_requested_fields(user_message)

            # Extract with constraints
            if fields:
                # Create a mock context from the message for entity extraction
                result = self.extract_with_constraints(user_message, fields)
                logger.info(f"Constrained extraction result: {result}")
                return result

        # Fall back to original entity extraction for non-extraction queries
        system_prompt = f"""Extract entities from query (intent: {intent}).
Find: product_numbers, vendor_skus, plant_codes, export_format.
JSON only."""

        prompt = f'"{user_message}"'

        response = self.generate(prompt, system_prompt, temperature=0.1, max_tokens=150, use_intent_model=True)

        if response:
            try:
                json_str = response.strip()
                if json_str.startswith('```'):
                    json_str = json_str.split('\n', 1)[1] if '\n' in json_str else json_str
                    json_str = json_str.rsplit('```', 1)[0] if '```' in json_str else json_str

                entities = json.loads(json_str.strip())
                return entities
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON: {response[:200]}")

        # Fallback to regex
        return self._fallback_entity_extraction(user_message)

    def _detect_requested_fields(self, message: str) -> List[str]:
        """Detect which fields are being requested"""
        message_lower = message.lower()
        requested = []

        field_keywords = {
            'upc': ['upc', 'ean', 'barcode', 'scan code'],
            'brand': ['brand', 'manufacturer', 'make'],
            'stock': ['stock', 'inventory', 'quantity', 'how many'],
            'origin': ['origin', 'country', 'made in'],
            'weight': ['weight', 'kg', 'pounds'],
            'delivery_date': ['delivery', 'eta', 'arriving'],
            'case_pack': ['case pack', 'case', 'pack size'],
            'vendor_sku': ['vendor', 'sku', 'supplier code']
        }

        for field, keywords in field_keywords.items():
            if any(kw in message_lower for kw in keywords):
                requested.append(field)

        return requested

    def _fallback_entity_extraction(self, message: str) -> Dict:
        """Regex-based fallback (original preserved)"""
        import re

        entities = {
            'product_numbers': [],
            'vendor_skus': [],
            'plant_code': None,
            'export_format': None
        }

        # Extract product numbers
        product_numbers = re.findall(r'\b\d{4,8}\b', message)
        entities['product_numbers'] = list(set(product_numbers))

        # Extract vendor SKUs
        vendor_skus = re.findall(r'\b[A-Z]{2,4}-\d{3,6}\b', message, re.IGNORECASE)
        entities['vendor_skus'] = list(set(vendor_skus))

        # Extract plant codes
        plant_codes = re.findall(r'\b(9993|9994|1000|9943)\b', message)
        if plant_codes:
            entities['plant_code'] = plant_codes[0]

        return entities

    def test_connection(self) -> bool:
        """Test connection to Ollama API"""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.info(f"Ollama connection successful. Models: {[m['name'] for m in models]}")
                return True
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
        return False