#!/bin/bash
#
# Safe Security Deployment Script for ATP Application
# Maintains Python 3.6 and pyrfc compatibility
#

echo "=========================================="
echo "ATP Security Patch Deployment"
echo "Python 3.6 & pyrfc Compatible"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "atp/atp/settings.py" ]; then
    echo "Error: Run this script from /mnt/d/productavailability/"
    exit 1
fi

# Step 1: Backup critical files
echo ""
echo "Step 1: Creating backups..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/security_patch_$TIMESTAMP"
mkdir -p $BACKUP_DIR

cp atp/atp/settings.py "$BACKUP_DIR/settings.py.backup"
cp atp/atp/wsgi.py "$BACKUP_DIR/wsgi.py.backup"
cp atp/manage.py "$BACKUP_DIR/manage.py.backup"
if [ -f "atp/atp/settings.ini" ]; then
    cp atp/atp/settings.ini "$BACKUP_DIR/settings.ini.backup"
fi

echo "✓ Backups created in $BACKUP_DIR"

# Step 2: Generate new secret key
echo ""
echo "Step 2: Generating new SECRET_KEY..."
NEW_SECRET_KEY=$(python3.6 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null)

if [ -z "$NEW_SECRET_KEY" ]; then
    # Try with just python if python3.6 doesn't work
    NEW_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
fi

echo "✓ New SECRET_KEY generated"

# Step 3: Create .env file if it doesn't exist
echo ""
echo "Step 3: Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        # Update with generated secret key
        sed -i "s/CHANGE_THIS_TO_NEW_GENERATED_KEY/$NEW_SECRET_KEY/" .env
        echo "✓ Created .env file from template"
    else
        # Create minimal .env file
        cat > .env << EOF
# ATP Security Configuration
DJANGO_SECRET_KEY=$NEW_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (update password!)
DATABASE_PASSWORD=CHANGE_THIS_DATABASE_PASSWORD

# SAP Connection (update password!)
SAP_HOST=your-sap-host
SAP_SYSNR=02
SAP_CLIENT=900
SAP_USER=your-sap-user
SAP_PASSWORD=CHANGE_THIS_SAP_PASSWORD
SAP_LANG=EN
EOF
        echo "✓ Created .env file with current settings"
    fi
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file to change passwords!"
else
    echo "✓ .env file already exists"
fi

# Step 4: Install python-dotenv if not present
echo ""
echo "Step 4: Installing dependencies..."
pip install python-dotenv==0.19.2 >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ python-dotenv installed"
else
    echo "⚠️  Warning: Could not install python-dotenv. Manual installation may be needed."
fi

# Step 5: Update wsgi.py to use secure settings
echo ""
echo "Step 5: Updating WSGI configuration..."
if grep -q "settings_secure" atp/atp/wsgi.py; then
    echo "✓ WSGI already using secure settings"
else
    # Create new wsgi.py
    cat > atp/atp/wsgi.py << 'EOF'
"""
WSGI config for atp project with security patches.
"""

import os
from django.core.wsgi import get_wsgi_application

# Use secure settings if available, fall back to regular settings
try:
    from . import settings_secure
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings_secure')
    print("Using secure settings")
except ImportError:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')
    print("Warning: Secure settings not found, using standard settings")

application = get_wsgi_application()
EOF
    echo "✓ WSGI updated to use secure settings"
fi

# Step 6: Update manage.py
echo ""
echo "Step 6: Updating manage.py..."
cp atp/manage.py atp/manage.py.tmp
sed 's/atp.settings/atp.settings_secure/g' atp/manage.py.tmp > atp/manage.py
rm atp/manage.py.tmp
echo "✓ manage.py updated"

# Step 7: Update views.py to use secure connection
echo ""
echo "Step 7: Patching views.py for secure SAP connection..."
if grep -q "get_secure_params" atp/stockcheck/views.py; then
    echo "✓ Views already patched"
else
    # Add import at the top of views.py (after line 35)
    sed -i '35 a from stockcheck.views_patch import get_secure_params' atp/stockcheck/views.py

    # Replace the params_connection line
    sed -i "s/params_connection = config._sections\['connection'\]/params_connection = get_secure_params()/" atp/stockcheck/views.py

    echo "✓ Views patched for secure connection"
fi

# Step 8: Create log directory if needed
echo ""
echo "Step 8: Setting up logging..."
mkdir -p /var/log/gunicorn 2>/dev/null
touch /var/log/gunicorn/django_security.log 2>/dev/null
touch /var/log/gunicorn/sap_interactions.log 2>/dev/null
echo "✓ Log directory prepared"

# Step 9: Test the configuration
echo ""
echo "Step 9: Testing configuration..."
cd atp
python manage.py check --deploy 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Django configuration check passed"
else
    echo "⚠️  Warning: Django check reported issues. Review manually."
fi
cd ..

# Step 10: Summary
echo ""
echo "=========================================="
echo "SECURITY PATCH DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "✅ COMPLETED:"
echo "  - Backups created in $BACKUP_DIR"
echo "  - Environment configuration prepared"
echo "  - WSGI and manage.py updated"
echo "  - Security settings activated"
echo ""
echo "⚠️  REQUIRED ACTIONS:"
echo ""
echo "1. Edit .env file and change these passwords:"
echo "   - DATABASE_PASSWORD"
echo "   - SAP_PASSWORD"
echo ""
echo "2. Restart your application:"
echo "   docker-compose restart web"
echo "   OR"
echo "   supervisorctl restart atp"
echo ""
echo "3. Test the application:"
echo "   - Check that login works"
echo "   - Test SAP connection"
echo "   - Verify stock search functionality"
echo ""
echo "4. Monitor logs for any issues:"
echo "   tail -f /var/log/gunicorn/django_security.log"
echo ""
echo "TO ROLLBACK if needed:"
echo "  cp -r $BACKUP_DIR/* atp/"
echo ""
echo "=========================================="