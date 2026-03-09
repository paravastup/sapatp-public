"""
Alternative middleware with CSP that allows CDN resources
Use this file if you want CSP protection while allowing CDNs
"""

from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses, with CDN-friendly CSP."""

    def process_response(self, request, response):
        # Security headers to protect against common vulnerabilities
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # CDN-friendly Content Security Policy
        # This allows the specific CDNs your app uses
        csp_policy = (
            "default-src 'self' https:; "

            # Allow styles from specific CDNs
            "style-src 'self' 'unsafe-inline' "
            "https://stackpath.bootstrapcdn.com "
            "https://fonts.googleapis.com "
            "https://cdn.datatables.net "
            "https://cdnjs.cloudflare.com; "

            # Allow scripts from specific CDNs
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://code.jquery.com "
            "https://cdn.datatables.net "
            "https://stackpath.bootstrapcdn.com "
            "https://cdnjs.cloudflare.com "
            "https://cdn.jsdelivr.net "
            "https://unpkg.com "
            "https://buttons.github.io "
            "https://cdn.amcharts.com; "

            # Allow fonts from CDNs
            "font-src 'self' data: "
            "https://fonts.gstatic.com "
            "https://cdnjs.cloudflare.com "
            "https://stackpath.bootstrapcdn.com; "

            # Allow images from anywhere (for external APIs)
            "img-src 'self' data: https: http:; "

            # Allow connections to your API and SAP
            "connect-src 'self';"
        )

        # Uncomment this line to enable CDN-friendly CSP:
        # response['Content-Security-Policy'] = csp_policy

        # Remove server header to avoid exposing server info
        if 'Server' in response:
            del response['Server']

        # Add Strict-Transport-Security if using HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response