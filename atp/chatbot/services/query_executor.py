"""
Query executor service for SAP integration
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Execute SAP queries using existing stock_info function"""

    def __init__(self, user: User):
        """
        Initialize query executor

        Args:
            user: Django user object for permission checking
        """
        self.user = user
        self.cache_duration_minutes = 5  # Cache results for 5 minutes

    def execute_search(self, plant_code: str, product_numbers: List[str], mode: str = 'M') -> List[Dict]:
        """
        Execute search using existing SAP integration

        Args:
            plant_code: Plant code (e.g., '9995')
            product_numbers: List of product numbers
            mode: 'M' for Arc SKU, 'O' for Vendor SKU

        Returns:
            List of product data dictionaries
        """
        # Import here to avoid circular imports
        from stockcheck.views import stock_info

        results = []

        # Check if user has access to the plant
        if not self._user_has_plant_access(plant_code):
            logger.warning(f"User {self.user.username} does not have access to plant {plant_code}")
            return [{
                'error': f"You don't have access to plant {plant_code}"
            }]

        # Limit number of products per query to prevent timeouts
        # Note: Each product query takes ~100-200ms, so:
        # - 200 products = ~20-40 seconds (acceptable)
        # - 500 products = ~50-100 seconds (may timeout but user requested no limits)
        # - 1000 products = ~100-200 seconds (long but covers all brands)
        MAX_BULK_QUERY = 1000  # User requested no restrictions on bulk queries

        if len(product_numbers) > MAX_BULK_QUERY:
            logger.warning(f"Large query requested: {len(product_numbers)} products, limiting to {MAX_BULK_QUERY} to prevent extreme timeout")
            # Return partial results with a flag
            product_numbers = product_numbers[:MAX_BULK_QUERY]
        elif len(product_numbers) > 200:
            logger.info(f"Very large bulk query: {len(product_numbers)} products (may take 30-60+ seconds)")
        elif len(product_numbers) > 100:
            logger.info(f"Large bulk query: {len(product_numbers)} products (may take 10-20 seconds)")

        # Execute queries for each product
        for product in product_numbers:
            try:
                # Check cache first
                cached_result = self._get_cached_result(plant_code, product, mode)
                if cached_result:
                    logger.info(f"Using cached result for {product}")
                    results.append(cached_result)
                    continue

                # Call existing stock_info function
                logger.info(f"Querying SAP for product {product} at plant {plant_code}")
                data = stock_info(plant_code, product.upper(), mode)

                # Process and format the data
                data = self._process_sap_data(data)

                # Cache the result
                self._cache_result(plant_code, product, mode, data)

                results.append(data)

            except Exception as e:
                logger.error(f"Error fetching data for product {product}: {str(e)}")
                results.append({
                    'MATNR': product,
                    'error': f"Error retrieving data: {str(e)}"
                })

        return results

    def _user_has_plant_access(self, plant_code: str) -> bool:
        """
        Check if user has access to the specified plant

        Args:
            plant_code: Plant code to check

        Returns:
            True if user has access
        """
        try:
            # Check if user has plant assignments
            user_plants = self.user.plant.all()
            plant_codes = [p.code for p in user_plants]
            return plant_code in plant_codes
        except:
            # If plant relationship doesn't exist, allow access (for backward compatibility)
            return True

    def _process_sap_data(self, data: Dict) -> Dict:
        """
        Process and format SAP data
        Enriches with Plytix product information (descriptions, pricing, etc.)

        Args:
            data: Raw SAP data

        Returns:
            Processed data dictionary enriched with Plytix data
        """
        try:
            # ENRICH WITH PLYTIX DESCRIPTION
            # Replace SAP's MAKTX with accurate Plytix label if available
            if 'MATNR' in data:
                product_sku = data['MATNR']
                try:
                    from products.models import Product
                    plytix_product = Product.objects.filter(sku=product_sku).first()

                    if plytix_product:
                        # Override SAP description with Plytix label (accurate description)
                        data['MAKTX'] = plytix_product.label

                        # Add flat Plytix fields for backward compatibility
                        data['PLYTIX_BRAND'] = plytix_product.catalog_brand
                        data['PLYTIX_CATEGORY'] = plytix_product.catalog_category
                        data['PLYTIX_LIST_PRICE'] = float(plytix_product.list_price) if plytix_product.list_price else None
                        data['PLYTIX_WEB_PRICE'] = float(plytix_product.web_price) if plytix_product.web_price else None
                        data['PLYTIX_MATERIAL'] = plytix_product.material
                        data['PLYTIX_COLLECTION'] = plytix_product.catalog_collection

                        # Create nested plytix structure for response generator
                        data['plytix'] = {
                            'name': plytix_product.label,
                            'description': plytix_product.label,  # Use label as description
                            'brand': plytix_product.catalog_brand,
                            'category': plytix_product.catalog_category,
                            'collection': plytix_product.catalog_collection,
                            'family': plytix_product.family,  # For URL building
                            'catalog_category': plytix_product.catalog_category,  # For URL building
                            'website_subcategories': plytix_product.website_subcategories,  # For URL building
                            'label': plytix_product.label,  # For URL building
                            'price': {
                                'list': float(plytix_product.list_price) if plytix_product.list_price else 0,
                                'web': float(plytix_product.web_price) if plytix_product.web_price else 0
                            },
                            'specs': {
                                'material': plytix_product.material
                            }
                        }

                        logger.debug(f"Enriched {product_sku} with Plytix data: {plytix_product.label}")
                    else:
                        logger.debug(f"No Plytix data found for {product_sku}, using SAP description")
                except Exception as e:
                    logger.error(f"Error enriching product {product_sku} with Plytix data: {e}")
                    # Fall back to SAP description if Plytix lookup fails

            # Convert ACTUAL to float
            if 'ACTUAL' in data:
                try:
                    data['ACTUAL'] = float(data['ACTUAL'])
                except:
                    data['ACTUAL'] = 0.0

            # Format date if present
            if data.get('EEIND'):
                try:
                    # Convert from YYYYMMDD to MM/DD/YYYY
                    date_str = str(data['EEIND'])
                    if len(date_str) == 8:
                        year = date_str[:4]
                        month = date_str[4:6]
                        day = date_str[6:8]
                        data['EEIND'] = f"{month}/{day}/{year}"
                except Exception as e:
                    logger.error(f"Error formatting date: {e}")

            # Map DISMM codes to human-readable values
            dismm_mapping = {
                'V2': 'Stock item',
                'V1': 'Stock item',
                'Z5': 'Stock item',
                'Z9': 'Stock item',
                'ZD': 'On demand' if data.get('PRMOD') == '0' else 'Stock item',
            }

            if 'DISMM' in data:
                original_dismm = data['DISMM']
                data['DISMM'] = dismm_mapping.get(original_dismm, 'No planning')

            # Ensure numeric fields are properly formatted
            numeric_fields = ['STOCK', 'MNG01', 'ZMENG', 'ZKWMENG', 'UMREZ', 'BRGEW']
            for field in numeric_fields:
                if field in data:
                    try:
                        data[field] = float(data[field])
                    except:
                        data[field] = 0.0

        except Exception as e:
            logger.error(f"Error processing SAP data: {e}")

        return data

    def _get_cached_result(self, plant_code: str, product: str, mode: str) -> Optional[Dict]:
        """
        Get cached query result if available

        Args:
            plant_code: Plant code
            product: Product number
            mode: Search mode

        Returns:
            Cached result or None
        """
        try:
            from ..models import QueryCache

            # Generate cache key
            cache_key = self._generate_cache_key(plant_code, product, mode)

            # Look for non-expired cache entry
            cache_entry = QueryCache.objects.filter(
                query_key=cache_key,
                expires_at__gt=timezone.now()
            ).first()

            if cache_entry:
                return cache_entry.get_results()

        except Exception as e:
            logger.error(f"Error retrieving cached result: {e}")

        return None

    def _cache_result(self, plant_code: str, product: str, mode: str, data: Dict):
        """
        Cache query result

        Args:
            plant_code: Plant code
            product: Product number
            mode: Search mode
            data: Query result data
        """
        try:
            from ..models import QueryCache, ChatSession

            # Get current session if available
            session = ChatSession.objects.filter(
                user=self.user,
                is_active=True
            ).order_by('-updated_at').first()

            if session:
                # Generate cache key
                cache_key = self._generate_cache_key(plant_code, product, mode)

                # Set expiration time
                expires_at = timezone.now() + timedelta(minutes=self.cache_duration_minutes)

                # Create or update cache entry
                QueryCache.objects.update_or_create(
                    session=session,
                    query_key=cache_key,
                    defaults={
                        'results': json.dumps(data),
                        'expires_at': expires_at
                    }
                )

        except Exception as e:
            logger.error(f"Error caching result: {e}")

    def _generate_cache_key(self, plant_code: str, product: str, mode: str) -> str:
        """
        Generate unique cache key for query

        Args:
            plant_code: Plant code
            product: Product number
            mode: Search mode

        Returns:
            Cache key string
        """
        key_string = f"{plant_code}:{product.upper()}:{mode}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def execute_comparison(self, plant_code: str, product_numbers: List[str], mode: str = 'M') -> Dict:
        """
        Execute comparison query for multiple products

        Args:
            plant_code: Plant code
            product_numbers: List of products to compare
            mode: Search mode

        Returns:
            Comparison results dictionary
        """
        # Get data for all products
        results = self.execute_search(plant_code, product_numbers, mode)

        # Organize comparison data
        comparison = {
            'products': results,
            'summary': {
                'total_products': len(results),
                'in_stock': 0,
                'out_of_stock': 0,
                'on_demand': 0,
                'with_delivery': 0,
                'total_stock': 0.0
            }
        }

        # Calculate summary statistics
        for product in results:
            if 'error' not in product:
                stock = product.get('STOCK', 0)
                if isinstance(stock, (int, float)):
                    comparison['summary']['total_stock'] += stock
                    if stock > 0:
                        comparison['summary']['in_stock'] += 1
                    else:
                        comparison['summary']['out_of_stock'] += 1

                if product.get('DISMM') == 'On demand':
                    comparison['summary']['on_demand'] += 1

                if product.get('EEIND'):
                    comparison['summary']['with_delivery'] += 1

        return comparison

    def get_available_plants(self) -> List[Dict]:
        """
        Get list of plants available to the user

        Returns:
            List of plant dictionaries
        """
        try:
            user_plants = self.user.plant.all()
            return [
                {
                    'code': plant.code,
                    'description': plant.description
                }
                for plant in user_plants
            ]
        except:
            # Return empty list if no plants configured
            return []