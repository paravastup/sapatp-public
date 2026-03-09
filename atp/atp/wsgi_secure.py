"""
WSGI config for atp project with security enhancements.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments.
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Use secure settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')

# Initialize the Django application
application = get_wsgi_application()

# Log successful initialization
print("WSGI application initialized with secure settings", file=sys.stderr)