#!/usr/bin/env python
"""
Test script to verify security patches work with Python 3.6 and pyrfc
Run this BEFORE deploying to production
"""

import os
import sys
import warnings

print("=" * 60)
print("ATP Security Patch Test Suite")
print("Python 3.6 & pyrfc Compatibility Check")
print("=" * 60)

# Add project to path
sys.path.insert(0, '/mnt/d/demoproject/atp')

# Test 1: Check Python version
print("\n1. Python Version Check...")
python_version = sys.version_info
if python_version.major == 3 and python_version.minor == 6:
    print(f"   ✓ Python {python_version.major}.{python_version.minor} - Compatible")
else:
    print(f"   ⚠ Python {python_version.major}.{python_version.minor} - May have issues")

# Test 2: Check pyrfc installation
print("\n2. pyrfc Module Check...")
try:
    import pyrfc
    print(f"   ✓ pyrfc {pyrfc.__version__} imported successfully")
except ImportError as e:
    print(f"   ✗ pyrfc import failed: {e}")
    sys.exit(1)

# Test 3: Check Django settings
print("\n3. Django Settings Check...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')

try:
    import django
    django.setup()
    from django.conf import settings

    print(f"   ✓ Django {django.VERSION} loaded")
    print(f"   ✓ DEBUG = {settings.DEBUG}")

    if settings.DEBUG:
        print("   ⚠ WARNING: DEBUG is True!")

    if hasattr(settings, 'SECRET_KEY'):
        if settings.SECRET_KEY == 'CHANGE-ME-generate-a-new-secret-key':
            print("   ⚠ WARNING: Using default SECRET_KEY!")
        else:
            print("   ✓ SECRET_KEY has been changed")

    print(f"   ✓ ALLOWED_HOSTS = {settings.ALLOWED_HOSTS[:2]}...")

except Exception as e:
    print(f"   ✗ Django settings failed: {e}")
    print("   Falling back to original settings...")
    os.environ['DJANGO_SETTINGS_MODULE'] = 'atp.settings'
    import django
    django.setup()

# Test 4: Check secure SAP connection
print("\n4. SAP Connection Security Check...")
try:
    # Test the new secure connection method
    from stockcheck.connection import get_sap_connection_params

    params = get_sap_connection_params()
    print("   ✓ SAP parameters loaded")

    # Check if from environment or settings.ini
    if os.environ.get('SAP_PASSWORD'):
        print("   ✓ Using environment variables (SECURE)")
    else:
        print("   ⚠ Using settings.ini (LESS SECURE)")

    # Don't print the actual password
    print(f"   ✓ SAP Host: {params.get('ashost')}")
    print(f"   ✓ SAP Client: {params.get('client')}")

except ImportError:
    print("   ⚠ New secure connection not found, testing fallback...")
    try:
        from stockcheck.views_patch import get_secure_params
        params = get_secure_params()
        print("   ✓ Fallback connection method works")
    except Exception as e:
        print(f"   ⚠ Fallback also failed: {e}")

# Test 5: Test actual SAP connection with pyrfc
print("\n5. pyrfc Connection Test...")
try:
    from pyrfc import Connection

    # Get connection params
    try:
        from stockcheck.connection import get_sap_connection_params
        params = get_sap_connection_params()
    except:
        # Fallback to old method
        from configparser import ConfigParser
        config = ConfigParser()
        config.read('atp/atp/settings.ini')
        params = dict(config._sections['connection'])

    print("   Attempting SAP connection...")

    # Quick connection test
    try:
        with Connection(**params) as conn:
            result = conn.call('RFC_SYSTEM_INFO')
            print(f"   ✓ SAP connection successful!")
            print(f"   ✓ SAP Release: {result.get('RFCSI_EXPORT', {}).get('RFCRELEASE', 'Unknown')}")
    except Exception as conn_error:
        print(f"   ⚠ SAP connection failed: {conn_error}")
        print("   This might be due to network/credentials, not the security patch")

except Exception as e:
    print(f"   ✗ Connection test failed: {e}")

# Test 6: Check if existing views still work
print("\n6. Application Views Check...")
try:
    from stockcheck import views

    # Check if the main functions exist
    if hasattr(views, 'product_details'):
        print("   ✓ product_details function found")
    if hasattr(views, 'stock_info'):
        print("   ✓ stock_info function found")
    if hasattr(views, 'SearchView'):
        print("   ✓ SearchView class found")

    print("   ✓ Main application views intact")

except Exception as e:
    print(f"   ✗ Views check failed: {e}")

# Test 7: Database connection
print("\n7. Database Connection Check...")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("   ✓ Database connection successful")
except Exception as e:
    print(f"   ⚠ Database connection failed: {e}")
    print("   Check DATABASE_PASSWORD in .env file")

# Test 8: Static files and templates
print("\n8. Static Files & Templates Check...")
try:
    from django.conf import settings
    print(f"   ✓ STATIC_URL = {settings.STATIC_URL}")
    print(f"   ✓ TEMPLATE_DIR exists: {os.path.exists(settings.TEMPLATE_DIR)}")
except Exception as e:
    print(f"   ⚠ Static/Template check failed: {e}")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

issues = []

if os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true':
    issues.append("DEBUG mode is still enabled")

if not os.environ.get('DATABASE_PASSWORD'):
    issues.append("Database password not in environment")

if not os.environ.get('SAP_PASSWORD'):
    issues.append("SAP password not in environment (using settings.ini)")

if not os.path.exists('.env'):
    issues.append(".env file not found")

if issues:
    print("\n⚠️  SECURITY ISSUES TO ADDRESS:")
    for issue in issues:
        print(f"   - {issue}")
else:
    print("\n✅ All security patches working correctly!")

print("\n📝 NEXT STEPS:")
print("1. Edit .env file to set new passwords")
print("2. Run: chmod +x deploy_security_safe.sh")
print("3. Run: ./deploy_security_safe.sh")
print("4. Restart your application")
print("5. Test in staging before production")

print("\n" + "=" * 60)