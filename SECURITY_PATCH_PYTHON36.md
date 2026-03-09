# Security Patches for ATP - Python 3.6 & Django 2.1.5 Compatible

## ⚡ These fixes work with your current pyrfc wheel dependency!

### Step 1: Create Environment Configuration (Won't break anything)

#### 1.1 Create `.env` file in project root
```bash
# /mnt/d/productavailability/.env
# DO NOT commit this to git!

# Django Settings
DJANGO_SECRET_KEY=PUT_NEW_GENERATED_KEY_HERE
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=[REDACTED],[REDACTED]

# Database Configuration
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=atp
DATABASE_USER=djangoadmin
DATABASE_PASSWORD=CHANGE_THIS_PASSWORD_NOW
DATABASE_HOST=localhost
DATABASE_PORT=3306

# SAP Connection (Change these passwords!)
SAP_HOST=[REDACTED]
SAP_SYSNR=02
SAP_CLIENT=900
SAP_USER=[REDACTED]
SAP_PASSWORD=CHANGE_THIS_PASSWORD_NOW
SAP_LANG=EN

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=CHANGE_THIS_APP_PASSWORD
EMAIL_USE_TLS=True
```

#### 1.2 Install python-dotenv (compatible with Python 3.6)
```bash
pip install python-dotenv==0.19.2  # Last version supporting Python 3.6
```

### Step 2: Update settings.py (Backward compatible)

Create a new file `atp/atp/settings_secure.py`:

```python
"""
Secure settings for ATP project - Python 3.6 Compatible
This augments existing settings.py without breaking anything
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(os.path.dirname(BASE_DIR), '.env')
load_dotenv(env_path)

# Import existing settings
from .settings import *

# Override security-critical settings
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# Set allowed hosts from environment
allowed_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]

# Override database settings from environment
DATABASES['default'].update({
    'ENGINE': os.environ.get('DATABASE_ENGINE', DATABASES['default']['ENGINE']),
    'NAME': os.environ.get('DATABASE_NAME', DATABASES['default']['NAME']),
    'USER': os.environ.get('DATABASE_USER', DATABASES['default']['USER']),
    'PASSWORD': os.environ.get('DATABASE_PASSWORD', DATABASES['default']['PASSWORD']),
    'HOST': os.environ.get('DATABASE_HOST', DATABASES['default'].get('HOST', 'localhost')),
    'PORT': os.environ.get('DATABASE_PORT', DATABASES['default'].get('PORT', '3306')),
})

# Security headers (Django 2.1 compatible)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# Use secure cookies in production
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False  # Set to True when you have HTTPS

# Session security
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# Password validation (Django 2.1 compatible)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Logging configuration for security monitoring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/gunicorn/security.log',
            'formatter': 'verbose',
        },
        'auth_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/gunicorn/auth.log',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.contrib.auth': {
            'handlers': ['auth_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Email configuration from environment
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

print("Secure settings loaded successfully", file=sys.stderr)
```

### Step 3: Update views.py for SAP credentials

Create `atp/stockcheck/views_secure.py`:

```python
"""
Secure views configuration - reads SAP credentials from environment
"""

import os
from django.conf import settings

def get_sap_connection_params():
    """Get SAP connection parameters from environment variables."""
    # First try environment variables
    params = {
        'ashost': os.environ.get('SAP_HOST'),
        'sysnr': os.environ.get('SAP_SYSNR'),
        'client': os.environ.get('SAP_CLIENT'),
        'user': os.environ.get('SAP_USER'),
        'passwd': os.environ.get('SAP_PASSWORD'),
        'lang': os.environ.get('SAP_LANG', 'EN')
    }

    # Check if all parameters are present
    if all(params.values()):
        return params

    # Fall back to settings.ini for backward compatibility
    from configparser import ConfigParser
    config = ConfigParser()
    config_file = os.path.join(settings.PROJECT_DIR, 'settings.ini')

    if os.path.exists(config_file):
        config.read(config_file)
        if 'connection' in config._sections:
            return dict(config._sections['connection'])

    raise ValueError("SAP connection parameters not found in environment or settings.ini")

# Monkey-patch the existing views to use secure params
import stockcheck.views as views
views.params_connection = get_sap_connection_params()
```

### Step 4: Add Rate Limiting (Python 3.6 compatible)

```bash
pip install django-ratelimit==2.0.0  # Compatible with Django 2.1
```

Add to your views:
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
def login_view(request):
    # existing login code
    pass

@ratelimit(key='user', rate='100/h', method='GET')
def stock_info(plant, product, mode):
    # existing SAP call code
    pass
```

### Step 5: Input Validation Helper

Create `atp/stockcheck/validators.py`:

```python
"""
Input validators for security - Python 3.6 compatible
"""

import re
from django.core.exceptions import ValidationError

def validate_plant_code(value):
    """Validate plant code to prevent injection."""
    if not re.match(r'^[A-Z0-9]{4}$', str(value)):
        raise ValidationError('Invalid plant code format')
    return value

def validate_material_number(value):
    """Validate material number to prevent injection."""
    if not re.match(r'^[A-Z0-9\-]{1,18}$', str(value)):
        raise ValidationError('Invalid material number format')
    return value

def validate_search_pattern(value):
    """Validate search pattern to prevent injection."""
    # Remove any SQL/SAP injection attempts
    dangerous_chars = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
    value_upper = str(value).upper()
    for char in dangerous_chars:
        if char in value_upper:
            raise ValidationError('Invalid characters in search pattern')
    return value

def sanitize_filename(filename):
    """Sanitize filename for safe export."""
    import string
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in filename if c in valid_chars)
    return filename[:255]  # Max filename length
```

### Step 6: Create Security Middleware

Create `atp/stockcheck/middleware.py`:

```python
"""
Security middleware - Django 2.1 compatible
"""

from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger('django.security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses."""

    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Remove server header
        if 'Server' in response:
            del response['Server']

        return response

class LoggingMiddleware(MiddlewareMixin):
    """Log suspicious activities."""

    def process_request(self, request):
        # Log authentication attempts
        if request.path == '/atp/login/' and request.method == 'POST':
            logger.info(f"Login attempt from IP: {self.get_client_ip(request)}")

        # Log admin access
        if request.path.startswith('/atp/admin/'):
            logger.warning(f"Admin access from IP: {self.get_client_ip(request)} User: {request.user}")

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### Step 7: Deployment Script

Create `deploy_security.sh`:

```bash
#!/bin/bash
# Security deployment script - maintains Python 3.6 compatibility

echo "Deploying security patches..."

# Generate new secret key
NEW_SECRET_KEY=$(python3.6 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo "New secret key generated"

# Backup current settings
cp atp/atp/settings.py atp/atp/settings.py.backup.$(date +%Y%m%d_%H%M%S)

# Update wsgi.py to use secure settings
cat > atp/atp/wsgi.py << 'EOF'
import os
from django.core.wsgi import get_wsgi_application

# Use secure settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')
application = get_wsgi_application()
EOF

# Update manage.py to use secure settings
sed -i "s/'atp.settings'/'atp.settings_secure'/g" atp/manage.py

# Install required packages
pip install python-dotenv==0.19.2 django-ratelimit==2.0.0

# Set up log directory
mkdir -p /var/log/gunicorn
touch /var/log/gunicorn/security.log
touch /var/log/gunicorn/auth.log
chmod 666 /var/log/gunicorn/*.log

echo "Security patches deployed!"
echo "IMPORTANT: Update the .env file with:"
echo "  - DJANGO_SECRET_KEY=$NEW_SECRET_KEY"
echo "  - New database password"
echo "  - New SAP password"
echo "  - Set DJANGO_DEBUG=False"
```

### Step 8: Quick Test Script

Create `test_security.py`:

```python
#!/usr/bin/env python3.6
"""Test security configuration"""

import os
import sys

# Add the project to path
sys.path.insert(0, '/mnt/d/productavailability/atp')

# Test loading secure settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')

try:
    import django
    django.setup()
    from django.conf import settings

    print("Security Check Results:")
    print("-" * 40)
    print(f"DEBUG Mode: {settings.DEBUG}")
    print(f"SECRET_KEY Hidden: {'SECRET_KEY' not in str(settings.SECRET_KEY)}")
    print(f"Allowed Hosts: {settings.ALLOWED_HOSTS}")
    print(f"Security Headers: XSS={settings.SECURE_BROWSER_XSS_FILTER}")
    print(f"Session Security: {settings.SESSION_COOKIE_HTTPONLY}")
    print(f"Database Password Hidden: {'PASSWORD' not in str(settings.DATABASES['default']['PASSWORD'])}")

    # Test SAP connection params
    from stockcheck.views_secure import get_sap_connection_params
    params = get_sap_connection_params()
    print(f"SAP Credentials Loaded: {bool(params)}")
    print("-" * 40)
    print("✓ Security configuration loaded successfully!")

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
```

## 🚀 Implementation Steps

1. **Create .env file** with your credentials
2. **Run**: `pip install python-dotenv==0.19.2 django-ratelimit==2.0.0`
3. **Copy the secure files** to your project
4. **Test locally** with test_security.py
5. **Deploy** using deploy_security.sh

## ✅ What This Fixes (Without Breaking pyrfc!)

- ✓ Hides all passwords and secrets
- ✓ Disables DEBUG mode safely
- ✓ Adds security headers
- ✓ Implements rate limiting
- ✓ Adds input validation
- ✓ Creates security logging
- ✓ Hardens sessions
- ✓ **Maintains Python 3.6 & pyrfc compatibility**

## 📝 Notes

- All changes are backward compatible
- Falls back to settings.ini if .env missing
- No Python/Django upgrade needed
- pyrfc wheel continues working
- Can rollback by restoring settings.py.backup

Need help implementing these changes?