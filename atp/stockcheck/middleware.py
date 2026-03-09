"""
Security middleware for ATP application
Django 2.1.5 compatible
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.conf import settings
import logging
import re

logger = logging.getLogger('django.security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses."""

    def process_response(self, request, response):
        # Security headers to protect against common vulnerabilities
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Disabled CSP - it was blocking CDN resources
        # response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"

        # Remove server header to avoid exposing server info
        if 'Server' in response:
            del response['Server']

        # Add Strict-Transport-Security if using HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

class LoggingMiddleware(MiddlewareMixin):
    """Log security-relevant activities."""

    def process_request(self, request):
        client_ip = self.get_client_ip(request)

        # Log authentication attempts
        if request.path == '/atp/login/' and request.method == 'POST':
            logger.info(f"Login attempt from IP: {client_ip}, User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")

        # Log admin access attempts
        if request.path.startswith('/atp/admin/'):
            user_info = f"User: {request.user}" if request.user.is_authenticated else "Anonymous"
            logger.warning(f"Admin access attempt from IP: {client_ip}, {user_info}")

        # Log suspicious patterns (potential SQL injection, XSS attempts)
        if request.method in ['GET', 'POST']:
            params = request.GET.dict() if request.method == 'GET' else request.POST.dict()
            for key, value in params.items():
                if self.is_suspicious(value):
                    logger.warning(f"Suspicious input detected from IP: {client_ip}, Parameter: {key}, Value: {value[:100]}")
                    return HttpResponseForbidden("Invalid input detected")

    def process_response(self, request, response):
        # Log failed authentication
        if request.path == '/atp/login/' and response.status_code == 403:
            client_ip = self.get_client_ip(request)
            logger.warning(f"Failed login from IP: {client_ip}")

        return response

    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_suspicious(self, value):
        """Check if input contains suspicious patterns."""
        if not value:
            return False

        value_str = str(value).upper()

        # SQL injection patterns
        sql_patterns = [
            r'\bSELECT\b.*\bFROM\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bUPDATE\b.*\bSET\b',
            r'\bUNION\b.*\bSELECT\b',
            r'--',
            r'/\*.*\*/',
            r'\bOR\b.*=.*'
        ]

        # XSS patterns
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'onerror\s*=',
            r'onload\s*=',
            r'<iframe',
            r'document\.cookie',
            r'alert\s*\(',
            r'<img.*src.*=',
        ]

        all_patterns = sql_patterns + xss_patterns

        for pattern in all_patterns:
            if re.search(pattern, value_str):
                return True

        return False

class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}
        super().__init__(get_response)

    def process_request(self, request):
        import time
        from django.http import HttpResponseTooManyRequests

        # Get client IP
        client_ip = self.get_client_ip(request)
        current_time = time.time()

        # Clean old entries (older than 1 minute)
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if any(t > current_time - 60 for t in times)
        }

        # Check rate limit (100 requests per minute)
        if client_ip in self.requests:
            recent_requests = [t for t in self.requests[client_ip] if t > current_time - 60]
            if len(recent_requests) >= 100:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return HttpResponseTooManyRequests("Too many requests. Please try again later.")
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]

        return None

    def get_client_ip(self, request):
        """Get the real client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip