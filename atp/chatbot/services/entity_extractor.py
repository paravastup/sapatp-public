"""
Entity extraction service for the chatbot
Enhanced with DataFeed product catalog integration
"""

import re
import logging
from typing import Dict, List, Optional
from .ollama_client import OllamaClient
from .cache_utils import PatternCache

logger = logging.getLogger(__name__)

# Try to import ProductService - gracefully handle if products app not ready
try:
    from products.services import ProductService
    PRODUCTS_AVAILABLE = True
except ImportError:
    PRODUCTS_AVAILABLE = False
    logger.warning("ProductService not available - DataFeed integration disabled")


class EntityExtractor:
    """Service for extracting entities from user messages with DataFeed catalog support"""

    # Regular expression patterns
    PATTERNS = {
        'product_numbers': r'\b[A-Z]?\d{4,8}\b',  # 4-8 digit numbers, optionally prefixed with a letter (G3960, 10002)
        'vendor_skus': r'\b[A-Z]{2,4}-\d{3,6}\b',  # Format like "OLD-123"
        'plant_codes': r'\b(9993|9994|1000|9943)\b',  # Known plant codes
        'dates': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Date formats
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'brand_names': r'\b(?:libbey|arc|cardinal|durand|bormioli|pasabahce|crisa|chef\s*&\s*sommelier|chef\s+and\s+sommelier)\b'  # Common glass brands (legacy + Chef & Sommelier)
    }

    # Cache for DataFeed catalog entities - refreshed on init
    _datafeed_brands = None
    _datafeed_categories = None
    _datafeed_materials = None

    # Plant name mappings
    PLANT_MAPPINGS = {
        'durand': '1000',
        'durand glass': '1000',
        'millville': '9994',
        'cardinal': '9993',
        'arc canada': '9943',
        'canada': '9943'
    }

    # Export format keywords
    EXPORT_FORMATS = {
        'excel': ['excel', 'xls', 'xlsx', 'spreadsheet', 'csv'],
        'email': ['email', 'mail', 'send'],
        'pdf': ['pdf', 'document']
    }

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize entity extractor with DataFeed catalog support

        Args:
            ollama_client: Optional OllamaClient instance
        """
        self.ollama = ollama_client or OllamaClient()
        self.pattern_cache = PatternCache(cache_name='entity_cache')

        # Load DataFeed catalog entities if available
        if PRODUCTS_AVAILABLE and EntityExtractor._datafeed_brands is None:
            self._load_datafeed_entities()

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize brand/category/material names for fuzzy matching.
        Strips punctuation (®, &, etc.) and collapses whitespace.

        Examples:
            "Chef & Sommelier" -> "chef sommelier"
            "Chef and Sommelier" -> "chef and sommelier"
            "Brand_G Rocco®" -> "bormioli rocco"
        """
        # Remove special characters but keep alphanumeric and spaces
        normalized = re.sub(r'[^a-z0-9\s]+', ' ', name.lower())
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _load_datafeed_entities(self):
        """Load brands, categories, and materials from DataFeed catalog"""
        try:
            # Load brands with normalized keys for fuzzy matching
            brands = ProductService.get_all_brands()
            EntityExtractor._datafeed_brands = {}
            for b in brands:
                normalized_key = self._normalize_name(b['name'])
                EntityExtractor._datafeed_brands[normalized_key] = b['name']
                # Also store original case-insensitive version for exact matches
                EntityExtractor._datafeed_brands[b['name'].lower()] = b['name']

            # Load categories with normalized keys
            categories = ProductService.get_all_categories()
            EntityExtractor._datafeed_categories = {}
            for c in categories:
                normalized_key = self._normalize_name(c['name'])
                EntityExtractor._datafeed_categories[normalized_key] = c['name']
                EntityExtractor._datafeed_categories[c['name'].lower()] = c['name']

            # Load materials from database (top 20 most common)
            from products.models import Product
            materials = Product.objects.exclude(material__isnull=True)\
                .values_list('material', flat=True)\
                .distinct()[:20]
            EntityExtractor._datafeed_materials = {}
            for m in materials:
                if m:
                    normalized_key = self._normalize_name(m)
                    EntityExtractor._datafeed_materials[normalized_key] = m
                    EntityExtractor._datafeed_materials[m.lower()] = m

            logger.info(
                f"[DATAFEED] Loaded {len(set(EntityExtractor._datafeed_brands.values()))} brands, "
                f"{len(set(EntityExtractor._datafeed_categories.values()))} categories, "
                f"{len(set(EntityExtractor._datafeed_materials.values()))} materials"
            )

            # Guard: Warn if brand cache is empty
            if not EntityExtractor._datafeed_brands:
                logger.warning("[DATAFEED] Brand cache is EMPTY - brand matching will fall back to hardcoded regex!")

        except Exception as e:
            logger.error(f"[DATAFEED] Failed to load catalog entities: {e}")
            # Guard: Set empty dicts so we don't crash later
            EntityExtractor._datafeed_brands = {}
            EntityExtractor._datafeed_categories = {}
            EntityExtractor._datafeed_materials = {}

    def extract(self, user_message: str, intent: str, context: Dict = None,
                conversation_history: List[Dict] = None) -> Dict:
        """
        Extract entities from user message with 3-tier optimization:
        1. Pattern cache (0.001s) - Check if we've seen this pattern before
        2. Regex extraction (0.01s) - Pattern matching for product numbers, etc.
        3. LLM extraction (1-3s) - Ollama API call (only if needed)

        Args:
            user_message: The user's input
            intent: The classified intent
            context: Conversation context
            conversation_history: Previous conversation messages for context

        Returns:
            Dictionary of extracted entities
        """
        if not user_message:
            return {}

        # NOTE: Entity pattern caching disabled - specific values (product numbers) matter
        # Pattern caching works for intent (same pattern = same intent), but not for entities
        # where "stock of 10002" and "stock of 12345" have the same pattern but different entities

        # FAST PATH: Try regex extraction (0.01s)
        # This skips expensive LLM call for 90% of queries with clear product numbers
        entities = self._regex_extraction(user_message)

        # SLOW PATH: If regex fails or returns empty, use Ollama LLM extraction (1-3s)
        if not entities or not any(entities.values()):
            logger.info(f"[SLOW PATH] Regex extraction returned nothing, calling LLM for: '{user_message[:50]}...'")
            entities = self.ollama.extract_entities(user_message, intent, conversation_history)
        else:
            logger.info(f"[FAST PATH] Entities extracted via regex for: '{user_message[:50]}...'")

        # Post-process and validate entities
        entities = self._validate_entities(entities)

        # Add context-based entities (including follow-up detection)
        if context:
            entities = self._add_context_entities(entities, context, user_message)

        logger.info(f"Entities extracted: {entities}")
        return entities

    def _regex_extraction(self, message: str) -> Dict:
        """
        Extract entities using regex patterns and DataFeed catalog matching

        Args:
            message: User message

        Returns:
            Dictionary of extracted entities
        """
        entities = {
            'product_numbers': [],
            'vendor_skus': [],
            'plant_code': None,
            'plant_name': None,
            'export_format': None,
            'search_type': 'arc_sku',  # Default search type
            'date_references': [],
            'brand_names': [],
            'datafeed_brand': None,      # Matched DataFeed brand
            'datafeed_category': None,   # Matched DataFeed category
            'datafeed_material': None,   # Matched DataFeed material
            'datafeed_collection': None, # Matched DataFeed collection
            'is_bulk_query': False     # Whether this is a brand/category bulk query
        }

        # Extract product numbers (now handles alphanumeric like G3960)
        product_numbers = re.findall(self.PATTERNS['product_numbers'], message, re.IGNORECASE)
        # Filter out plant codes from product numbers
        entities['product_numbers'] = [
            num.upper() for num in product_numbers
            if num not in ['9993', '9994', '1000', '9943']
        ]

        # Extract vendor SKUs
        vendor_skus = re.findall(self.PATTERNS['vendor_skus'], message, re.IGNORECASE)
        entities['vendor_skus'] = [sku.upper() for sku in set(vendor_skus)]

        # Extract brand names
        brand_names = re.findall(self.PATTERNS['brand_names'], message, re.IGNORECASE)
        entities['brand_names'] = [brand.title() for brand in set(brand_names)]

        # Determine search type
        message_lower = message.lower()
        if vendor_skus or 'vendor' in message_lower or 'old' in message_lower:
            entities['search_type'] = 'vendor_sku'

        # Extract plant codes
        plant_codes = re.findall(self.PATTERNS['plant_codes'], message)
        if plant_codes:
            entities['plant_code'] = plant_codes[0]

        # Extract plant names
        for plant_name, plant_code in self.PLANT_MAPPINGS.items():
            if plant_name in message_lower:
                entities['plant_name'] = plant_name.title()
                entities['plant_code'] = plant_code
                break

        # Extract export format
        for format_name, keywords in self.EXPORT_FORMATS.items():
            if any(keyword in message_lower for keyword in keywords):
                entities['export_format'] = format_name
                break

        # Extract date references
        dates = re.findall(self.PATTERNS['dates'], message)
        entities['date_references'] = dates

        # Check for relative date references
        relative_dates = ['today', 'tomorrow', 'yesterday', 'next week', 'this week', 'last week']
        for rel_date in relative_dates:
            if rel_date in message_lower:
                entities['date_references'].append(rel_date)

        # ===== DATAFEED CATALOG MATCHING =====
        # Detect brands, categories, materials from DataFeed catalog
        if PRODUCTS_AVAILABLE:
            # Normalize the message for fuzzy matching
            normalized_message = self._normalize_name(message)

            # Match brand names (with fuzzy matching via normalization)
            if self._datafeed_brands:
                for brand_key, brand_name in self._datafeed_brands.items():
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(brand_key) + r'\b'
                    if re.search(pattern, normalized_message):
                        entities['datafeed_brand'] = brand_name
                        logger.info(f"[DATAFEED] Matched brand: {brand_name} (key: {brand_key})")
                        break

            # Match category names
            if self._datafeed_categories:
                for cat_key, cat_name in self._datafeed_categories.items():
                    pattern = r'\b' + re.escape(cat_key) + r'\b'
                    if re.search(pattern, normalized_message):
                        entities['datafeed_category'] = cat_name
                        logger.info(f"[DATAFEED] Matched category: {cat_name} (key: {cat_key})")
                        break

            # Match material names
            if self._datafeed_materials:
                for mat_key, mat_name in self._datafeed_materials.items():
                    # Materials can be multi-word, so check if phrase exists
                    if mat_key in normalized_message:
                        entities['datafeed_material'] = mat_name
                        logger.info(f"[DATAFEED] Matched material: {mat_name}")
                        break

            # Fallback: Use legacy brand_names if DataFeed brand not found
            # This handles "Chef and Sommelier" when cache has "Chef & Sommelier"
            if not entities['datafeed_brand'] and entities.get('brand_names'):
                # Map known fallback brands to DataFeed brands
                fallback_brand = entities['brand_names'][0].lower()
                if 'chef' in fallback_brand and 'sommelier' in fallback_brand:
                    entities['datafeed_brand'] = 'Chef & Sommelier'
                    logger.info(f"[DATAFEED] Using fallback brand mapping: {entities['brand_names'][0]} -> Chef & Sommelier")

            # Detect bulk query patterns (e.g., "Show me Arcoroc wine glasses", "all Chef & Sommelier products")
            bulk_keywords = [
                'all', 'every', 'entire', 'whole', 'complete',
                'show me all', 'list all', 'get all', 'find all',
                'show me', 'find', 'search', 'looking for'
            ]
            has_bulk_keyword = any(kw in message_lower for kw in bulk_keywords)

            # Also consider it bulk if brand/category mentioned WITHOUT specific product numbers
            has_datafeed_filter = (entities['datafeed_brand'] or entities['datafeed_category'] or entities['datafeed_material'])
            no_specific_products = len(entities['product_numbers']) == 0

            if has_datafeed_filter and (has_bulk_keyword or no_specific_products):
                entities['is_bulk_query'] = True
                logger.info("[DATAFEED] Bulk query detected")

        return entities

    def _validate_entities(self, entities: Dict) -> Dict:
        """
        Validate and clean extracted entities

        Args:
            entities: Raw extracted entities

        Returns:
            Validated entities
        """
        # Ensure product numbers are unique and valid (now allows alphanumeric)
        if 'product_numbers' in entities:
            product_nums = entities.get('product_numbers', [])
            if isinstance(product_nums, list):
                # Remove duplicates and validate length
                valid_products = []
                for num in product_nums:
                    if isinstance(num, str) and 4 <= len(num) <= 9:  # Allow up to 9 chars for alphanumeric
                        # Allow alphanumeric product codes (like G3960)
                        if re.match(r'^[A-Z]?\d{4,8}$', num, re.IGNORECASE):
                            valid_products.append(num.upper())
                entities['product_numbers'] = list(set(valid_products))

        # Ensure vendor SKUs are unique
        if 'vendor_skus' in entities:
            vendor_skus = entities.get('vendor_skus', [])
            if isinstance(vendor_skus, list):
                entities['vendor_skus'] = list(set(vendor_skus))

        # Validate plant code
        if 'plant_code' in entities:
            plant_code = entities.get('plant_code')
            if plant_code not in ['9993', '9994', '1000', '9943']:
                entities['plant_code'] = None

        # Validate export format
        if 'export_format' in entities:
            format_val = entities.get('export_format')
            if format_val not in ['excel', 'email', 'pdf']:
                entities['export_format'] = None

        return entities

    def _add_context_entities(self, entities: Dict, context: Dict, user_message: str = "") -> Dict:
        """
        Add entities from conversation context and detect follow-up questions

        Args:
            entities: Current extracted entities
            context: Conversation context
            user_message: User's message for follow-up detection

        Returns:
            Updated entities
        """
        # If no plant code extracted but one exists in context
        if not entities.get('plant_code') and context.get('selected_plant'):
            entities['plant_code'] = context['selected_plant']

        # If this is an export request and we have cached results
        if entities.get('export_format') and context.get('last_results'):
            entities['has_cached_results'] = True

        # FOLLOW-UP QUESTION DETECTION
        # If no products extracted, check if this is a follow-up question
        # BUT: Skip context injection for bulk queries (category/brand/material queries)
        if not entities.get('product_numbers') and not entities.get('vendor_skus'):
            # CRITICAL FIX: If this is a bulk query (e.g., "list all flatware"),
            # DO NOT pull products from context - user wants ALL products in that category
            is_bulk = entities.get('is_bulk_query', False)

            if is_bulk:
                logger.info(f"[BULK QUERY] Skipping context injection - user wants all products in category/brand")
            else:
                # Check if message contains follow-up indicators
                message_lower = user_message.lower() if user_message else ""

                followup_indicators = [
                    'it', 'its', 'this', 'that', 'these', 'those', 'them',
                    'the product', 'the item', 'the same', 'same one'
                ]

                is_followup = any(indicator in message_lower for indicator in followup_indicators)

                # Also check if it's a question without product numbers
                is_question = any(q in message_lower for q in ['what', 'when', 'where', 'how', 'which', '?'])
                has_no_numbers = not re.search(r'\b\d{4,}\b', user_message)

                if is_followup or (is_question and has_no_numbers):
                    # Get products from context
                    last_products = context.get('last_product_numbers', [])
                    current_product = context.get('current_product')

                    # Check if user explicitly asks for multiple products
                    message_lower = user_message.lower() if user_message else ""
                    multi_product_keywords = ['both', 'all of them', 'these products', 'those products',
                                             'all products', 'both products', 'all of these', 'all those',
                                             'for both', 'for all']
                    asking_for_multiple = any(keyword in message_lower for keyword in multi_product_keywords)

                    if asking_for_multiple and last_products and len(last_products) > 1:
                        # User explicitly wants all products from context
                        entities['product_numbers'] = last_products
                        entities['from_context'] = True
                        logger.info(f"Multi-product request detected: Using all products {last_products}")
                    elif current_product:
                        # Single product conversation
                        entities['product_numbers'] = [current_product]
                        entities['from_context'] = True
                        logger.info(f"Follow-up detected: Using current product {current_product}")
                    elif last_products:
                        # Multi-product conversation
                        entities['product_numbers'] = last_products
                        entities['from_context'] = True
                        logger.info(f"Follow-up detected: Using last products {last_products}")

                    # Preserve search type from context
                    if context.get('last_search_type'):
                        entities['search_type'] = context['last_search_type']

        return entities

    def extract_plant(self, message: str, available_plants: List) -> Optional[str]:
        """
        Extract plant selection from message

        Args:
            message: User message
            available_plants: List of available plant objects

        Returns:
            Selected plant code or None
        """
        message_lower = message.lower()

        # Check for plant codes
        for plant in available_plants:
            plant_code = plant.code if hasattr(plant, 'code') else plant.get('code')
            if plant_code and plant_code in message:
                return plant_code

            # Check for plant descriptions
            plant_desc = plant.description if hasattr(plant, 'description') else plant.get('description', '')
            if plant_desc and plant_desc.lower() in message_lower:
                return plant_code

        # Check plant name mappings
        for plant_name, plant_code in self.PLANT_MAPPINGS.items():
            if plant_name in message_lower:
                # Verify this plant is available
                for plant in available_plants:
                    p_code = plant.code if hasattr(plant, 'code') else plant.get('code')
                    if p_code == plant_code:
                        return plant_code

        return None

    def get_products_for_query(self, entities: Dict) -> List[str]:
        """
        Get list of products to query based on extracted entities

        Args:
            entities: Extracted entities

        Returns:
            List of product numbers or vendor SKUs
        """
        products = []

        # Check search type
        if entities.get('search_type') == 'vendor_sku':
            products = entities.get('vendor_skus', [])
        else:
            products = entities.get('product_numbers', [])

        return products

    def format_for_sap_query(self, entities: Dict) -> Dict:
        """
        Format entities for SAP query execution

        Args:
            entities: Extracted entities

        Returns:
            Formatted query parameters
        """
        return {
            'products': self.get_products_for_query(entities),
            'plant_code': entities.get('plant_code'),
            'search_type': entities.get('search_type', 'arc_sku'),
            'mode': 'O' if entities.get('search_type') == 'vendor_sku' else 'M'
        }