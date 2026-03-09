"""
Security patch for views.py - Minimal changes to use secure connections
Add this to the top of your existing views.py file
"""

import os
import sys
from configparser import ConfigParser
from django.conf import settings

# Override the params_connection to use secure method
def get_secure_params():
    """Get SAP parameters securely from environment or settings.ini"""
    # Try environment variables first
    env_params = {
        'ashost': os.environ.get('SAP_HOST'),
        'sysnr': os.environ.get('SAP_SYSNR'),
        'client': os.environ.get('SAP_CLIENT'),
        'user': os.environ.get('SAP_USER'),
        'passwd': os.environ.get('SAP_PASSWORD'),
        'lang': os.environ.get('SAP_LANG', 'EN')
    }

    if all(v is not None for k, v in env_params.items() if k != 'lang'):
        return env_params

    # Fall back to existing settings.ini
    config = ConfigParser()
    config_file = os.path.join(settings.PROJECT_DIR, 'settings.ini')
    if os.path.exists(config_file):
        config.read(config_file)
        if 'connection' in config._sections:
            return dict(config._sections['connection'])

    raise ValueError("SAP connection parameters not found")

# MINIMAL CHANGE: Add these 3 lines to your existing views.py after line 53
# Replace:
#   params_connection = config._sections['connection']
# With:
#   from stockcheck.views_patch import get_secure_params
#   params_connection = get_secure_params()