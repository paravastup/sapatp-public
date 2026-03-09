import os
from django.core.wsgi import get_wsgi_application

# Try secure settings, fallback to normal
try:
    from . import settings_secure
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')
except ImportError:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

application = get_wsgi_application()
