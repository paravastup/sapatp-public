"""
Input validators for security - Python 3.6 & Django 2.1.5 compatible
Prevents injection attacks and validates user input
"""

import re
import string
from django.core.exceptions import ValidationError
from django.utils.html import escape

def validate_plant_code(value):
    """
    Validate plant code to prevent injection.
    Plant codes should be 4-digit numbers or alphanumeric codes.
    """
    value_str = str(value).strip()

    if not value_str:
        raise ValidationError('Plant code cannot be empty')

    if len(value_str) > 10:
        raise ValidationError('Plant code too long')

    if not re.match(r'^[A-Z0-9]{1,10}$', value_str.upper()):
        raise ValidationError('Invalid plant code format. Use only letters and numbers.')

    return value_str

def validate_material_number(value):
    """
    Validate material number to prevent injection.
    Material numbers can contain letters, numbers, and hyphens.
    """
    value_str = str(value).strip()

    if not value_str:
        raise ValidationError('Material number cannot be empty')

    if len(value_str) > 40:
        raise ValidationError('Material number too long')

    if not re.match(r'^[A-Z0-9\-\_\.]{1,40}$', value_str.upper()):
        raise ValidationError('Invalid material number format. Use only letters, numbers, hyphens, underscores, and periods.')

    return value_str

def validate_search_pattern(value):
    """
    Validate search pattern to prevent injection attacks.
    Removes dangerous characters and SQL/SAP injection attempts.
    """
    if not value:
        return ''

    value_str = str(value).strip()

    # Check length
    if len(value_str) > 100:
        raise ValidationError('Search pattern too long (max 100 characters)')

    # List of dangerous SQL/SAP keywords to block
    dangerous_keywords = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'EXEC', 'EXECUTE',
        'CREATE', 'ALTER', 'TRUNCATE', 'MERGE', 'CALL',
        'UNION', 'SELECT', 'FROM', 'WHERE', '--', '/*', '*/',
        'SCRIPT', 'JAVASCRIPT', 'ONERROR', 'ONLOAD', 'ONCLICK'
    ]

    value_upper = value_str.upper()
    for keyword in dangerous_keywords:
        if keyword in value_upper:
            raise ValidationError(f'Invalid characters or keywords in search pattern')

    # Allow only safe characters
    if not re.match(r'^[A-Za-z0-9\s\-\_\.\*\%]+$', value_str):
        raise ValidationError('Search pattern contains invalid characters')

    return value_str

def sanitize_filename(filename):
    """
    Sanitize filename for safe file operations.
    Removes path traversal attempts and dangerous characters.
    """
    if not filename:
        return 'export'

    # Remove path traversal attempts
    filename = filename.replace('..', '')
    filename = filename.replace('/', '')
    filename = filename.replace('\\', '')

    # Keep only safe characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in filename if c in valid_chars)

    # Limit length
    filename = filename[:100]

    # Default if empty after sanitization
    if not filename:
        filename = 'export'

    return filename

def validate_email(value):
    """
    Validate email address format.
    """
    email_regex = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        re.IGNORECASE
    )

    if not email_regex.match(value):
        raise ValidationError('Invalid email address format')

    if len(value) > 254:
        raise ValidationError('Email address too long')

    return value.lower()

def validate_universe_code(value):
    """
    Validate universe code for SAP queries.
    """
    value_str = str(value).strip()

    if not value_str:
        raise ValidationError('Universe code cannot be empty')

    if len(value_str) > 20:
        raise ValidationError('Universe code too long')

    if not re.match(r'^[A-Z0-9\-]{1,20}$', value_str.upper()):
        raise ValidationError('Invalid universe code format')

    return value_str

def validate_mode(value):
    """
    Validate mode parameter for SAP calls.
    Mode should be a single letter.
    """
    value_str = str(value).strip().upper()

    if not value_str:
        raise ValidationError('Mode cannot be empty')

    if len(value_str) != 1:
        raise ValidationError('Mode should be a single character')

    if value_str not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        raise ValidationError('Mode should be a letter')

    return value_str

def sanitize_html_output(value):
    """
    Sanitize output to prevent XSS when displaying user-provided content.
    """
    if not value:
        return ''

    # Escape HTML characters
    return escape(str(value))

def validate_integer(value, min_val=None, max_val=None):
    """
    Validate integer input with optional range checking.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValidationError('Must be a valid integer')

    if min_val is not None and int_value < min_val:
        raise ValidationError(f'Value must be at least {min_val}')

    if max_val is not None and int_value > max_val:
        raise ValidationError(f'Value must be at most {max_val}')

    return int_value

def validate_date_format(value):
    """
    Validate date format (YYYY-MM-DD).
    """
    date_regex = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    if not date_regex.match(value):
        raise ValidationError('Date must be in YYYY-MM-DD format')

    return value

# Dictionary mapping field names to validators for easy use
FIELD_VALIDATORS = {
    'plant': validate_plant_code,
    'material': validate_material_number,
    'product': validate_material_number,
    'pattern': validate_search_pattern,
    'universe': validate_universe_code,
    'mode': validate_mode,
    'email': validate_email,
    'filename': sanitize_filename,
}

def validate_form_data(data, required_fields=None):
    """
    Validate a dictionary of form data using appropriate validators.

    Args:
        data: Dictionary of field names and values
        required_fields: List of required field names

    Returns:
        Dictionary of validated data

    Raises:
        ValidationError with details of all validation errors
    """
    errors = {}
    validated_data = {}

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = 'This field is required'

    # Validate each field
    for field_name, value in data.items():
        if field_name in FIELD_VALIDATORS:
            try:
                validated_data[field_name] = FIELD_VALIDATORS[field_name](value)
            except ValidationError as e:
                errors[field_name] = str(e)
        else:
            # For unknown fields, apply basic sanitization
            validated_data[field_name] = sanitize_html_output(value)

    if errors:
        raise ValidationError(errors)

    return validated_data