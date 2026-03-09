#!/bin/bash
#
# Quick deployment script for ATP security patches
# Maintains Python 3.6 and pyrfc compatibility
#

set -e  # Exit on error

echo "=================================================="
echo "ATP SECURITY DEPLOYMENT"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Creating .env from template..."
    cp .env.example .env

    # Generate new secret key
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || echo "PLEASE_GENERATE_NEW_KEY")
    sed -i "s/qz8n3p9v5t6y7u8i9o0p1a2s3d4f5g6h7j8k9l0z1x2c3v4b5n6m/$SECRET_KEY/" .env

    echo -e "${YELLOW}WARNING: .env created with default passwords!${NC}"
    echo -e "${YELLOW}EDIT .env NOW and change all passwords before continuing!${NC}"
    echo ""
    echo "Press Ctrl+C to exit and edit .env, or Enter to continue..."
    read
fi

# Verify critical settings
echo "Checking security settings..."

# Check DEBUG is False
if grep -q "DJANGO_DEBUG=True" .env; then
    echo -e "${RED}WARNING: DEBUG is set to True!${NC}"
    sed -i 's/DJANGO_DEBUG=True/DJANGO_DEBUG=False/' .env
    echo "DEBUG has been set to False"
fi

# Check for default passwords
if grep -q "P@ssword1234" .env; then
    echo -e "${RED}CRITICAL: Default database password detected!${NC}"
    echo "Please change DATABASE_PASSWORD in .env"
fi

if grep -q "Init1234567" .env; then
    echo -e "${RED}CRITICAL: Default SAP password detected!${NC}"
    echo "Please change SAP_PASSWORD in .env"
fi

# Backup current configuration
echo ""
echo "Creating backups..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup files if they exist
[ -f "docker-compose.yml" ] && cp docker-compose.yml "$BACKUP_DIR/"
[ -f "Dockerfile" ] && cp Dockerfile "$BACKUP_DIR/"
[ -f "nginx.conf" ] && cp nginx.conf "$BACKUP_DIR/"
[ -f "atp/atp/wsgi.py" ] && cp atp/atp/wsgi.py "$BACKUP_DIR/"
[ -f "atp/manage.py" ] && cp atp/manage.py "$BACKUP_DIR/"

echo -e "${GREEN}✓ Backups created in $BACKUP_DIR${NC}"

# Apply secure configurations
echo ""
echo "Applying security configurations..."

# Use secure Docker files
cp docker-compose-secure.yml docker-compose.yml
cp Dockerfile-secure Dockerfile
cp nginx-secure.conf nginx.conf

# Update WSGI and manage.py to use secure settings
cp atp/atp/wsgi_secure.py atp/atp/wsgi.py
cp atp/manage_secure.py atp/manage.py
chmod +x atp/manage.py

echo -e "${GREEN}✓ Security configurations applied${NC}"

# Set file permissions
echo ""
echo "Setting file permissions..."
chmod 600 .env
chmod 644 atp/atp/settings_secure.py
chmod 755 deploy_secure.sh

echo -e "${GREEN}✓ File permissions set${NC}"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if [ -f "requirements-secure.txt" ]; then
    docker-compose run --rm web pip install -r requirements-secure.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Docker deployment
echo ""
echo "Deploying with Docker..."
echo "1. Stopping existing containers..."
docker-compose down

echo "2. Building new image with security patches..."
docker-compose build --no-cache web

echo "3. Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Verify deployment
echo ""
echo "Verifying deployment..."

# Check if web service is running
if docker-compose ps | grep -q "web.*Up"; then
    echo -e "${GREEN}✓ Web service is running${NC}"
else
    echo -e "${RED}✗ Web service is not running${NC}"
fi

# Check if database is running
if docker-compose ps | grep -q "db.*Up"; then
    echo -e "${GREEN}✓ Database service is running${NC}"
else
    echo -e "${RED}✗ Database service is not running${NC}"
fi

# Check if nginx is running
if docker-compose ps | grep -q "nginx.*Up"; then
    echo -e "${GREEN}✓ Nginx service is running${NC}"
else
    echo -e "${RED}✗ Nginx service is not running${NC}"
fi

# Test security headers
echo ""
echo "Testing security headers..."
HEADERS=$(curl -s -I http://localhost/ 2>/dev/null)

if echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    echo -e "${GREEN}✓ Security headers are active${NC}"
else
    echo -e "${YELLOW}⚠ Security headers may not be active${NC}"
fi

# Show logs
echo ""
echo "Recent logs:"
docker-compose logs --tail=20 web

echo ""
echo "=================================================="
echo "DEPLOYMENT COMPLETE"
echo "=================================================="
echo ""
echo -e "${GREEN}Security patches have been deployed!${NC}"
echo ""
echo "NEXT STEPS:"
echo "1. Check application: http://localhost/"
echo "2. Monitor logs: docker-compose logs -f"
echo "3. Test login functionality"
echo "4. Verify SAP connection"
echo ""

if grep -q "P@ssword1234\|Init1234567" .env; then
    echo -e "${RED}⚠️  CRITICAL: Default passwords still in use!${NC}"
    echo -e "${RED}   Change them immediately in .env and restart:${NC}"
    echo -e "${RED}   docker-compose restart${NC}"
fi

echo ""
echo "To rollback if needed:"
echo "  cp -r $BACKUP_DIR/* ."
echo "  docker-compose restart"
echo ""
echo "Security deployment completed at $(date)"