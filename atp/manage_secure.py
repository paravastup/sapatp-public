#!/usr/bin/env python
"""
Django management script with security settings.
This version uses the secure settings configuration.
"""

import os
import sys

if __name__ == '__main__':
    # Use secure settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Execute the command
    execute_from_command_line(sys.argv)