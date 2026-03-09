@echo off
echo ===== Checking Docker Containers =====
docker-compose ps

echo.
echo ===== Checking Web Application Logs =====
docker-compose logs --tail=20 web

echo.
echo ===== Testing Web Application Accessibility =====
echo Attempting to connect to http://localhost:8000...
powershell -Command "try { $response = Invoke-WebRequest -Uri http://localhost:8000 -Method GET -TimeoutSec 5; Write-Host 'Connection successful! Status code:' $response.StatusCode } catch { Write-Host 'Connection failed:' $_.Exception.Message }"

echo.
echo ===== Database Status =====
docker-compose exec -T db mysqladmin -u root -p%MYSQL_ROOT_PASSWORD% status

echo.
echo ===== Check Complete =====
echo If all services are running and the web application is accessible, your setup is working correctly.
echo If you encountered any errors, please check the troubleshooting section in the README.md file.