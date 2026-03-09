#!/usr/bin/env python3
"""
SAP Connection Test Script

This script tests the connection to SAP using the pyrfc library.
It reads connection parameters from settings.ini or environment variables.
"""

import os
import sys
from configparser import ConfigParser
from pprint import pprint

try:
    from pyrfc import Connection
except ImportError:
    print("Error: pyrfc module not found. Make sure it's installed.")
    print("You can install it with: pip install pyrfc")
    sys.exit(1)

def get_connection_params():
    """Get SAP connection parameters from settings.ini or environment variables."""
    # Try to get connection parameters from settings.ini
    config = ConfigParser()
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'atp', 'atp', 'settings.ini')
    
    if os.path.exists(settings_path):
        print(f"Reading connection parameters from {settings_path}")
        config.read(settings_path)
        if 'connection' in config._sections:
            return dict(config._sections['connection'])
    
    # If settings.ini doesn't exist or doesn't have connection section,
    # try to get parameters from environment variables
    print("Reading connection parameters from environment variables")
    params = {
        'ashost': os.environ.get('SAP_HOST'),
        'sysnr': os.environ.get('SAP_SYSNR'),
        'client': os.environ.get('SAP_CLIENT'),
        'user': os.environ.get('SAP_USER'),
        'passwd': os.environ.get('SAP_PASSWORD'),
        'lang': 'EN'
    }
    
    # Check if all required parameters are present
    missing_params = [k for k, v in params.items() if v is None]
    if missing_params:
        print(f"Error: Missing SAP connection parameters: {', '.join(missing_params)}")
        print("Please set them in settings.ini or as environment variables.")
        sys.exit(1)
    
    return params

def test_connection():
    """Test the connection to SAP."""
    params = get_connection_params()
    
    print("\nConnection parameters:")
    # Print parameters but hide password
    safe_params = params.copy()
    if 'passwd' in safe_params:
        safe_params['passwd'] = '********'
    pprint(safe_params)
    
    print("\nAttempting to connect to SAP...")
    try:
        with Connection(**params) as conn:
            print("Connection successful!")
            print("\nSAP version info:")
            result = conn.call('RFC_SYSTEM_INFO')
            pprint(result)
            
            print("\nTesting a simple RFC call...")
            # Try a simple RFC call that should be available in most SAP systems
            result = conn.call('STFC_CONNECTION', REQUTEXT='Hello SAP!')
            print(f"Response: {result['ECHOTEXT']}")
            
            print("\nConnection test completed successfully.")
            return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("SAP Connection Test")
    print("===================")
    
    success = test_connection()
    sys.exit(0 if success else 1)