"""
Secure SAP connection handler - Python 3.6 & pyrfc compatible
This module provides secure handling of SAP credentials
"""

import os
import sys
from configparser import ConfigParser
from django.conf import settings

def get_sap_connection_params():
    """
    Get SAP connection parameters from environment variables or settings.ini.
    Environment variables take precedence for security.

    Returns:
        dict: SAP connection parameters
    """
    # First, try to get from environment variables (most secure)
    env_params = {
        'ashost': os.environ.get('SAP_HOST'),
        'sysnr': os.environ.get('SAP_SYSNR'),
        'client': os.environ.get('SAP_CLIENT'),
        'user': os.environ.get('SAP_USER'),
        'passwd': os.environ.get('SAP_PASSWORD'),
        'lang': os.environ.get('SAP_LANG', 'EN')
    }

    # Check if all required parameters are in environment
    if all(v is not None for k, v in env_params.items() if k != 'lang'):
        print("SAP credentials loaded from environment variables", file=sys.stderr)
        return env_params

    # Fall back to settings.ini for backward compatibility
    config = ConfigParser()
    config_file = os.path.join(settings.PROJECT_DIR, 'settings.ini')

    if os.path.exists(config_file):
        config.read(config_file)
        if 'connection' in config._sections:
            print("WARNING: SAP credentials loaded from settings.ini - Consider moving to environment variables!", file=sys.stderr)
            return dict(config._sections['connection'])

    # If we get here, credentials are missing
    raise ValueError(
        "SAP connection parameters not found. "
        "Please set SAP_HOST, SAP_SYSNR, SAP_CLIENT, SAP_USER, SAP_PASSWORD in environment "
        "or provide settings.ini file."
    )

def get_secure_connection():
    """
    Create a secure SAP connection using pyrfc.

    Returns:
        Connection: pyrfc Connection object
    """
    from pyrfc import Connection

    params = get_sap_connection_params()

    # Log connection attempt (without password)
    safe_params = params.copy()
    safe_params['passwd'] = '***hidden***'
    print(f"Connecting to SAP: {safe_params}", file=sys.stderr)

    return Connection(**params)

# Create a cached version of connection params
_cached_params = None

def get_cached_connection_params():
    """
    Get cached connection parameters to avoid repeated file/env reads.

    Returns:
        dict: SAP connection parameters
    """
    global _cached_params
    if _cached_params is None:
        _cached_params = get_sap_connection_params()
    return _cached_params