#!/usr/bin/env python3
"""Test what HTML is served to authenticated users"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from stockcheck.views import HomeView

User = get_user_model()

print("\n" + "="*70)
print("TESTING AUTHENTICATED HOME PAGE")
print("="*70)

# Get admin user
user = User.objects.get(username='admin')
print(f"\nUser: {user.username}")
print(f"Is authenticated: {user.is_authenticated}")
print(f"Is active: {user.is_active}")

# Create a proper request with authentication
factory = RequestFactory()
request = factory.get('/atp/home/')

# Add session
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

# Add user to request
request.user = user

# Get the view response
view = HomeView.as_view()
response = view(request)

# Check the response
print(f"\nResponse status: {response.status_code}")

# Render the response
response.render()
html_content = response.content.decode('utf-8')

# Check for AI Search
if 'AI Search' in html_content:
    print("✓ SUCCESS: 'AI Search' found in HTML!")

    # Count occurrences
    count = html_content.count('AI Search')
    print(f"  Found {count} occurrences of 'AI Search'")

    # Show context around AI Search
    import re
    matches = list(re.finditer(r'.{0,50}AI Search.{0,50}', html_content))
    print(f"\n  Context around 'AI Search':")
    for i, match in enumerate(matches, 1):
        print(f"    {i}. {match.group().strip()}")
else:
    print("✗ ERROR: 'AI Search' NOT found in HTML!")

# Check if user is in authenticated block
if 'user.is_authenticated' in html_content or user.username in html_content:
    print(f"\n✓ User '{user.username}' appears in the page")
else:
    print("\n✗ User information NOT in page")

# Check template path
print(f"\nTemplate used: {response.template_name}")

print("\n" + "="*70)
