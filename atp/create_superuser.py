#!/usr/bin/env python
"""
Create Django superuser script
Set DJANGO_ADMIN_PASSWORD environment variable before running.
"""

import os
import django
import sys

# Add the project to path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User

admin_password = os.environ.get('DJANGO_ADMIN_PASSWORD')
if not admin_password:
    print("ERROR: Set DJANGO_ADMIN_PASSWORD environment variable first!")
    sys.exit(1)

admin_user = os.environ.get('DJANGO_ADMIN_USER', 'admin')
admin_email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')

# Check if admin user already exists
if User.objects.filter(username=admin_user).exists():
    print("Admin user already exists. Updating password...")
    user = User.objects.get(username=admin_user)
    user.set_password(admin_password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save()
    print("Admin password updated successfully!")
else:
    print("Creating new admin user...")
    user = User.objects.create_superuser(
        username=admin_user,
        email=admin_email,
        password=admin_password
    )
    print("Admin user created successfully!")

print(f"\nAdmin username: {admin_user}")
print("Login at: http://localhost:5000/atp/admin/")
