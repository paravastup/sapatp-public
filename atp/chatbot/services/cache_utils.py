"""
Cache utility for pattern-based caching of intent classifications and entity extractions
"""

import re
import hashlib
import logging
from typing import Tuple, Optional, Dict, Any
from django.core.cache import caches

logger = logging.getLogger(__name__)


class PatternCache:
    """
    Pattern-based caching for intent classification and entity extraction

    Normalizes queries by replacing specific values with placeholders:
    - "stock of 10002" → "stock of <PRODUCT>"
    - "delivery for G3960" → "delivery for <PRODUCT>"
    - "check plant 1000" → "check plant <PLANT>"

    This allows cache hits for similar queries with different product numbers.
    """

    # Regex patterns for normalization
    PRODUCT_PATTERN = r'\b[A-Z]?\d{4,8}\b'  # Product numbers (10002, G3960)
    VENDOR_SKU_PATTERN = r'\b[A-Z]{2,4}-\d{3,6}\b'  # Vendor SKUs (OLD-123)
    PLANT_CODE_PATTERN = r'\b(9993|9994|1000|9943)\b'  # Plant codes
    DATE_PATTERN = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'  # Dates
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Emails

    def __init__(self, cache_name: str = 'default'):
        """
        Initialize pattern cache

        Args:
            cache_name: Name of the Django cache to use (default, intent_cache, entity_cache)
        """
        self.cache = caches[cache_name]
        self.cache_name = cache_name

    def normalize_query(self, query: str) -> str:
        """
        Normalize query by replacing specific values with placeholders

        Args:
            query: User query string

        Returns:
            Normalized pattern string

        Example:
            "What's the stock of 10002?" → "what's the stock of <product>?"
            "Delivery for G3960 and 12345" → "delivery for <product> and <product>"
        """
        normalized = query.lower().strip()

        # IMPORTANT: Replace plant codes FIRST (before products)
        # Plant codes are 4-digit numbers that also match product pattern
        normalized = re.sub(self.PLANT_CODE_PATTERN, '<PLANT>', normalized)

        # Replace vendor SKUs with <VENDOR_SKU>
        normalized = re.sub(self.VENDOR_SKU_PATTERN, '<VENDOR_SKU>', normalized, flags=re.IGNORECASE)

        # Replace product numbers with <PRODUCT>
        normalized = re.sub(self.PRODUCT_PATTERN, '<PRODUCT>', normalized, flags=re.IGNORECASE)

        # Replace dates with <DATE>
        normalized = re.sub(self.DATE_PATTERN, '<DATE>', normalized)

        # Replace emails with <EMAIL>
        normalized = re.sub(self.EMAIL_PATTERN, '<EMAIL>', normalized, flags=re.IGNORECASE)

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    def generate_cache_key(self, query: str, prefix: str = '') -> str:
        """
        Generate cache key from normalized query pattern

        Args:
            query: User query string
            prefix: Optional prefix for cache key (e.g., 'intent_', 'entity_')

        Returns:
            Cache key string
        """
        normalized = self.normalize_query(query)

        # Use SHA256 hash for consistent key length
        # But keep it readable by including first 50 chars of pattern
        pattern_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]

        # Create readable key: prefix + pattern_snippet + hash
        pattern_snippet = normalized[:50].replace(' ', '_')
        cache_key = f"{prefix}{pattern_snippet}_{pattern_hash}"

        return cache_key

    def get_cached_intent(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Get cached intent classification for query

        Args:
            query: User query string

        Returns:
            Tuple of (intent, confidence) if cache hit, None if cache miss
        """
        cache_key = self.generate_cache_key(query, prefix='intent_')

        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"[CACHE HIT] Intent cache hit for pattern: '{self.normalize_query(query)[:50]}...'")
            return cached['intent'], cached['confidence']

        logger.debug(f"[CACHE MISS] Intent cache miss for pattern: '{self.normalize_query(query)[:50]}...'")
        return None

    def cache_intent(self, query: str, intent: str, confidence: float, ttl: int = 900):
        """
        Cache intent classification result

        Args:
            query: User query string
            intent: Classified intent
            confidence: Confidence score
            ttl: Time to live in seconds (default 15 minutes)
        """
        cache_key = self.generate_cache_key(query, prefix='intent_')

        self.cache.set(cache_key, {
            'intent': intent,
            'confidence': confidence,
            'pattern': self.normalize_query(query)
        }, timeout=ttl)

        logger.info(f"[CACHE WRITE] Intent cached for pattern: '{self.normalize_query(query)[:50]}...'")

    def get_cached_entities(self, query: str, intent: str) -> Optional[Dict[str, Any]]:
        """
        Get cached entity extraction for query

        Args:
            query: User query string
            intent: Classified intent (used in cache key for better accuracy)

        Returns:
            Dictionary of entities if cache hit, None if cache miss
        """
        # Include intent in cache key for better accuracy
        cache_key = self.generate_cache_key(f"{intent}_{query}", prefix='entity_')

        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"[CACHE HIT] Entity cache hit for pattern: '{self.normalize_query(query)[:50]}...'")
            return cached['entities']

        logger.debug(f"[CACHE MISS] Entity cache miss for pattern: '{self.normalize_query(query)[:50]}...'")
        return None

    def cache_entities(self, query: str, intent: str, entities: Dict[str, Any], ttl: int = 900):
        """
        Cache entity extraction result

        Args:
            query: User query string
            intent: Classified intent
            entities: Extracted entities dictionary
            ttl: Time to live in seconds (default 15 minutes)
        """
        # Include intent in cache key
        cache_key = self.generate_cache_key(f"{intent}_{query}", prefix='entity_')

        self.cache.set(cache_key, {
            'entities': entities,
            'pattern': self.normalize_query(query)
        }, timeout=ttl)

        logger.info(f"[CACHE WRITE] Entities cached for pattern: '{self.normalize_query(query)[:50]}...'")

    def clear_cache(self):
        """Clear all cached items in this cache"""
        self.cache.clear()
        logger.info(f"[CACHE CLEAR] Cleared all items from {self.cache_name}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics (if supported by backend)

        Returns:
            Dictionary with cache stats
        """
        # Note: Database cache doesn't provide stats, but Redis will in Phase 2
        return {
            'cache_name': self.cache_name,
            'backend': str(type(self.cache)),
        }
