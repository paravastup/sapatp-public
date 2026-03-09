#!/bin/bash

echo "===== Checking Docker Containers ====="
docker-compose ps

echo
echo "===== Checking Web Application Logs ====="
docker-compose logs --tail=20 web

echo
echo "===== Testing Web Application Accessibility ====="
echo "Attempting to connect to http://localhost:8000..."
if command -v curl &> /dev/null; then
    curl -I http://localhost:8000
elif command -v wget &> /dev/null; then
    wget --spider -S http://localhost:8000
else
    echo "Neither curl nor wget is installed. Please install one of them to test connectivity."
fi

echo
echo "===== Database Status ====="
docker-compose exec -T db mysqladmin -u root -p$MYSQL_ROOT_PASSWORD status

echo
echo "===== Check Complete ====="
echo "If all services are running and the web application is accessible, your setup is working correctly."
echo "If you encountered any errors, please check the troubleshooting section in the README.md file."