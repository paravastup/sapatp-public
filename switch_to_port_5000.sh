#!/bin/bash
#
# Script to switch ATP application to port 5000
#

echo "========================================"
echo "Switching ATP Application to Port 5000"
echo "========================================"
echo ""

# Stop current containers
echo "1. Stopping current Docker containers..."
docker-compose down

# Clean up any hanging containers
docker container prune -f

echo ""
echo "2. Applying fixed nginx configuration..."
cp nginx-fixed.conf nginx.conf

echo ""
echo "3. Starting services on port 5000..."
docker-compose -f docker-compose-port5000-fixed.yml up -d

echo ""
echo "4. Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "5. Checking service status..."
docker-compose -f docker-compose-port5000-fixed.yml ps

echo ""
echo "6. Testing application..."
sleep 5

# Test if the application is accessible
echo ""
if curl -s http://localhost:5000/ | grep -q "Product Availability"; then
    echo "✅ SUCCESS! Application is running on port 5000"
    echo ""
    echo "Access your application at:"
    echo "  http://localhost:5000/"
    echo "  http://localhost:5000/atp/login/"
    echo "  http://localhost:5000/atp/admin/"
else
    echo "⚠️  Application may still be starting up..."
    echo "Check logs with: docker-compose -f docker-compose-port5000-fixed.yml logs"
    echo ""
    echo "Try accessing manually:"
    echo "  http://localhost:5000/"
fi

echo ""
echo "========================================"
echo "Switch complete!"
echo "========================================"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose -f docker-compose-port5000-fixed.yml logs -f"
echo "  Stop: docker-compose -f docker-compose-port5000-fixed.yml down"
echo "  Restart: docker-compose -f docker-compose-port5000-fixed.yml restart"