"""
Secure settings for ATP project - Python 3.6 & Django 2.1.5 Compatible
Maintains backward compatibility with pyrfc wheel
"""

import os
import sys
from pathlib import Path

# Try to load dotenv, but don't fail if not installed
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(os.path.dirname(BASE_DIR), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}", file=sys.stderr)
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables only.", file=sys.stderr)

# Import ALL existing settings first
from .settings import *

# Override ONLY security-critical settings
# This maintains all your existing configurations

# Add chatbot app to INSTALLED_APPS
if 'chatbot' not in INSTALLED_APPS:
    INSTALLED_APPS.append('chatbot')
    print("Added 'chatbot' app to INSTALLED_APPS", file=sys.stderr)

# 1. SECRET KEY - Get from environment or generate warning
env_secret = os.environ.get('DJANGO_SECRET_KEY')
if env_secret:
    SECRET_KEY = env_secret
else:
    print("WARNING: Using hardcoded SECRET_KEY. Set DJANGO_SECRET_KEY in environment!", file=sys.stderr)
    # Keep existing key for backward compatibility during transition

# 2. DEBUG - Force to False in production
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')
if DEBUG:
    print("WARNING: DEBUG mode is enabled!", file=sys.stderr)

# 3. ALLOWED_HOSTS - Expand from environment if provided
allowed_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]
    print(f"Allowed hosts set to: {ALLOWED_HOSTS}", file=sys.stderr)

# 4. Database configuration - Override with environment variables if present
if os.environ.get('DATABASE_PASSWORD'):
    DATABASES['default'].update({
        'ENGINE': os.environ.get('DATABASE_ENGINE', DATABASES['default']['ENGINE']),
        'NAME': os.environ.get('DATABASE_NAME', DATABASES['default']['NAME']),
        'USER': os.environ.get('DATABASE_USER', DATABASES['default']['USER']),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),  # This is the critical one
        'HOST': os.environ.get('DATABASE_HOST', DATABASES['default'].get('HOST', 'localhost')),
        'PORT': os.environ.get('DATABASE_PORT', DATABASES['default'].get('PORT', '3306')),
    })
    print("Database password loaded from environment", file=sys.stderr)

# 5. Security headers - These are safe to add to Django 2.1
SECURE_BROWSER_XSS_FILTER = True  # Prevent XSS attacks
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie

# 6. Secure cookies (only in production)
if not DEBUG:
    # Only set these if you have HTTPS configured
    if os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true':
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_SSL_REDIRECT = True

# 7. Session security
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Force login on browser restart
SESSION_COOKIE_AGE = int(os.environ.get('SESSION_COOKIE_AGE', 3600))  # Default 1 hour
SESSION_SAVE_EVERY_REQUEST = True  # Reset timeout on activity

# 8. Enhanced password validation (Django 2.1 compatible)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,  # Increased from default 8
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 9. Email configuration from environment (if provided)
if os.environ.get('EMAIL_HOST_PASSWORD'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', EMAIL_HOST if 'EMAIL_HOST' in locals() else 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', EMAIL_PORT if 'EMAIL_PORT' in locals() else 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    print("Email configuration loaded from environment", file=sys.stderr)

# 10. Enhanced logging for security monitoring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/gunicorn/django_security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# 11. Additional security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add custom security middleware if it exists
]

# Try to add custom middleware if the file exists
try:
    from stockcheck.middleware import SecurityHeadersMiddleware
    MIDDLEWARE.insert(1, 'stockcheck.middleware.SecurityHeadersMiddleware')
    print("Custom security middleware added", file=sys.stderr)
except ImportError:
    pass

# Final security check
security_issues = []
if DEBUG:
    security_issues.append("DEBUG is True")
if SECRET_KEY == 'CHANGE-ME-generate-a-new-secret-key':
    security_issues.append("Using default SECRET_KEY")
if not os.environ.get('DATABASE_PASSWORD'):
    security_issues.append("Database password not in environment")

if security_issues:
    print("=" * 60, file=sys.stderr)
    print("SECURITY WARNINGS:", file=sys.stderr)
    for issue in security_issues:
        print(f"  - {issue}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
else:
    print("✓ Security settings loaded successfully", file=sys.stderr)

# 12. Ollama Configuration for Chatbot
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:4b')
OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '30'))

# For Docker containers accessing host Ollama
if os.environ.get('RUNNING_IN_DOCKER'):
    # Windows/Mac Docker Desktop
    if sys.platform in ['win32', 'darwin']:
        OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
    # Linux Docker
    else:
        OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://172.17.0.1:11434')

print(f"Ollama configured: {OLLAMA_BASE_URL} using model {OLLAMA_MODEL}", file=sys.stderr)

# 13. Cache Configuration (Database cache - with Phase 1 optimizations active)
# Note: Redis migration postponed due to dependency conflicts with Django 2.1.5
# Performance is already >99% improved with Phase 1 optimizations (fast-path + caching)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'chatbot_cache_table',
        'TIMEOUT': 3600,  # 1 hour default timeout
        'OPTIONS': {
            'MAX_ENTRIES': 10000,  # Limit cache size
            'CULL_FREQUENCY': 3,   # Remove 1/3 of entries when max reached
        }
    },
    # Pattern-based cache for intent classification (15 minutes)
    'intent_cache': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'intent_cache_table',
        'TIMEOUT': 900,  # 15 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
        }
    },
    # Pattern-based cache for entity extraction (15 minutes)
    # Note: Currently disabled in entity_extractor.py (specific values matter)
    'entity_cache': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'entity_cache_table',
        'TIMEOUT': 900,  # 15 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
        }
    }
}

print("Cache configuration: Database-backed (Phase 1 optimizations: >99% improvement)", file=sys.stderr)

# 14. Authentication URLs
LOGIN_URL = '/atp/login/'
LOGIN_REDIRECT_URL = '/atp/home/'
LOGOUT_REDIRECT_URL = '/'