"""
Celery tasks for DataFeed product feed automation
Handles scheduled imports and cache invalidation
"""
import logging
import requests
from datetime import datetime
from io import BytesIO
from django.core.cache import cache
from django.core.management import call_command
from products.models import ProductImportLog

logger = logging.getLogger(__name__)

# Placeholder for Celery decorator - will work once Celery is installed
try:
    from celery import shared_task
except ImportError:
    # Fallback decorator for development without Celery
    def shared_task(func):
        func.delay = lambda *args, **kwargs: func(*args, **kwargs)
        return func


DATAFEED_FEED_URL = 'https://pim.datafeed.com/channels/6638c4dd23dda406832ca8e9/feed'


@shared_task(name='products.import_datafeed_feed', bind=True)
def import_datafeed_feed_task(self, source_url=None):
    """
    Scheduled task to import DataFeed product feed
    Runs daily to keep product data in sync

    Args:
        source_url: Optional custom feed URL (defaults to configured DataFeed feed)

    Returns:
        dict: Import statistics
    """
    url = source_url or DATAFEED_FEED_URL

    logger.info(f'[DATAFEED IMPORT] Starting scheduled import from {url}')

    try:
        # Download XML feed
        logger.info('[DATAFEED IMPORT] Fetching XML feed...')
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        # Save to temporary file
        temp_file = f'/tmp/datafeed_feed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
        with open(temp_file, 'wb') as f:
            f.write(response.content)

        logger.info(f'[DATAFEED IMPORT] Feed downloaded ({len(response.content)} bytes)')

        # Run import command
        call_command('import_datafeed_feed', temp_file)

        # Get latest import stats
        latest_log = ProductImportLog.objects.order_by('-imported_at').first()

        if latest_log and latest_log.success:
            stats = {
                'success': True,
                'products_added': latest_log.products_added,
                'products_updated': latest_log.products_updated,
                'products_total': latest_log.products_total,
                'duration_seconds': latest_log.duration_seconds,
            }

            logger.info(
                f'[DATAFEED IMPORT] Success! Added: {stats["products_added"]}, '
                f'Updated: {stats["products_updated"]}, '
                f'Total: {stats["products_total"]}, '
                f'Duration: {stats["duration_seconds"]:.1f}s'
            )

            # Invalidate all product-related caches
            invalidate_product_caches()

            return stats
        else:
            logger.error('[DATAFEED IMPORT] Import failed - check ProductImportLog')
            return {'success': False, 'error': 'Import command failed'}

    except requests.RequestException as e:
        error_msg = f'Failed to fetch feed from {url}: {e}'
        logger.error(f'[DATAFEED IMPORT] {error_msg}')

        # Log failure
        ProductImportLog.objects.create(
            source_file=url,
            products_total=0,
            duration_seconds=0,
            success=False,
            error_message=error_msg
        )

        return {'success': False, 'error': str(e)}

    except Exception as e:
        error_msg = f'Unexpected error during import: {e}'
        logger.error(f'[DATAFEED IMPORT] {error_msg}')

        # Log failure
        ProductImportLog.objects.create(
            source_file=url,
            products_total=0,
            duration_seconds=0,
            success=False,
            error_message=error_msg
        )

        return {'success': False, 'error': str(e)}


@shared_task(name='products.invalidate_product_caches')
def invalidate_product_caches():
    """
    Invalidate all product-related cache keys
    Called after successful feed import
    """
    logger.info('[CACHE] Invalidating product caches...')

    # Clear all product-related cache keys
    cache_patterns = [
        'product:*',
        'brand:*',
        'category:*',
        'products:by_brand:*',
        'products:by_category:*',
        'products:by_material:*',
        'products:search:*',
    ]

    # Note: Django's cache doesn't support pattern deletion by default
    # This requires Redis backend with django-redis
    # For now, just clear entire cache or specific keys as needed

    try:
        cache.clear()
        logger.info('[CACHE] Product caches invalidated successfully')
        return {'success': True}
    except Exception as e:
        logger.error(f'[CACHE] Failed to invalidate caches: {e}')
        return {'success': False, 'error': str(e)}


@shared_task(name='products.update_brand_counts')
def update_brand_counts():
    """
    Recalculate product counts for all brands
    Useful for maintaining accurate statistics
    """
    from products.models import Product, ProductBrand

    logger.info('[BRANDS] Updating brand counts...')

    try:
        brands = ProductBrand.objects.all()
        updated_count = 0

        for brand in brands:
            count = Product.objects.filter(catalog_brand=brand.name).count()
            if brand.product_count != count:
                brand.product_count = count
                brand.save()
                updated_count += 1

        logger.info(f'[BRANDS] Updated {updated_count} brand counts')
        return {'success': True, 'updated': updated_count}

    except Exception as e:
        logger.error(f'[BRANDS] Failed to update counts: {e}')
        return {'success': False, 'error': str(e)}


@shared_task(name='products.update_category_counts')
def update_category_counts():
    """
    Recalculate product counts for all categories
    Useful for maintaining accurate statistics
    """
    from products.models import Product, ProductCategory

    logger.info('[CATEGORIES] Updating category counts...')

    try:
        categories = ProductCategory.objects.all()
        updated_count = 0

        for category in categories:
            count = Product.objects.filter(catalog_category=category.name).count()
            if category.product_count != count:
                category.product_count = count
                category.save()
                updated_count += 1

        logger.info(f'[CATEGORIES] Updated {updated_count} category counts')
        return {'success': True, 'updated': updated_count}

    except Exception as e:
        logger.error(f'[CATEGORIES] Failed to update counts: {e}')
        return {'success': False, 'error': str(e)}
