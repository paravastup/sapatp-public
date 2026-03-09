# ATP Application Deployment Guide

This document provides step-by-step instructions for deploying the ATP application on a new Ubuntu server with domain setup.

## Prerequisites

- Ubuntu 18.04 or newer server
- Root or sudo access to the server
- A domain name pointing to your server's IP address
- Basic knowledge of Linux command line

## 1. Server Preparation

### 1.1 Update the System

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Install Required Packages

```bash
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git
```

### 1.3 Install Docker

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Update package lists
sudo apt update

# Install Docker CE
sudo apt install -y docker-ce

# Add your user to the docker group to run Docker without sudo
sudo usermod -aG docker $USER

# Apply the new group membership (or log out and back in)
newgrp docker
```

### 1.4 Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

## 2. Application Deployment

### 2.1 Clone or Copy the Application

#### Option 1: Clone from Git Repository

```bash
git clone https://your-repository-url.git /opt/atp
cd /opt/atp
```

#### Option 2: Copy from Local Machine

From your local machine:

```bash
scp -r /path/to/atp username@your-server-ip:/opt/
```

Then on the server:

```bash
cd /opt/atp
```

### 2.2 Configure SAP Connection

Edit the settings.ini file:

```bash
nano atp/atp/settings.ini
```

Update with your SAP connection parameters:

```ini
[connection]
ashost=your-sap-host
sysnr=your-sysnr
client=your-client
user=your-sap-user
passwd=your-sap-password
lang=EN
```

### 2.3 Configure Domain in Nginx

Create a new Nginx configuration file:

```bash
nano nginx-domain.conf
```

Add the following configuration, replacing `yourdomain.com` with your actual domain:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /static/;
        expires 30d;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2.4 Update Docker Compose for Domain Support

Edit the docker-compose.yml file:

```bash
nano docker-compose.yml
```

Update the nginx service to use your new configuration:

```yaml
nginx:
  image: nginx:1.19
  volumes:
    - ./nginx-domain.conf:/etc/nginx/conf.d/default.conf
    - static_volume:/static
  ports:
    - "80:80"
  depends_on:
    - web
  restart: unless-stopped
```

### 2.5 Start the Application

```bash
docker-compose up -d
```

### 2.6 Create a Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 2.7 Add Plant Data for the Superuser

```bash
docker-compose exec web python -c "
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atp.settings')
django.setup()

from django.contrib.auth.models import User
from stockcheck.models import Plant

def add_plants_to_user(username):
    try:
        user = User.objects.get(username=username)
        print(f'Found user: {user.username}')
        
        # Create plant objects if they don't exist
        plants_data = [
            {'code': '1001', 'description': 'Demo Corp'},
            {'code': '1002', 'description': 'Plant B'},
            {'code': '1003', 'description': 'Plant C'},
            {'code': '1004', 'description': 'Plant D'},
        ]
        
        for plant_data in plants_data:
            plant, created = Plant.objects.get_or_create(
                code=plant_data['code'],
                defaults={'description': plant_data['description']}
            )
            
            if created:
                print(f'Created plant: {plant.description}')
            else:
                print(f'Plant already exists: {plant.description}')
            
            # Associate plant with user
            if not plant.users.filter(id=user.id).exists():
                plant.users.add(user)
                print(f'Associated plant {plant.description} with user {user.username}')
            else:
                print(f'Plant {plant.description} already associated with user {user.username}')
        
        print('\nPlants associated with user:')
        for plant in user.plant.all():
            print(f'- {plant.code}: {plant.description}')
            
        return True
    except User.DoesNotExist:
        print(f'User {username} not found')
        return False
    except Exception as e:
        print(f'Error: {str(e)}')
        return False

# Call the function with your superuser username
add_plants_to_user('your_superuser_username')
"
```

Replace 'your_superuser_username' with the username you created in the previous step.

## 3. SSL Configuration (Optional)

### 3.1 Install Certbot

```bash
mkdir -p certbot/conf certbot/www
```

Update docker-compose.yml to add certbot:

```yaml
services:
  # ... existing services ...
  
  nginx:
    # ... existing configuration ...
    volumes:
      - ./nginx-domain.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/static
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    ports:
      - "80:80"
      - "443:443"
    
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

### 3.2 Obtain SSL Certificates

```bash
docker-compose up -d nginx
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email your-email@example.com --agree-tos --no-eff-email -d yourdomain.com -d www.yourdomain.com
```

### 3.3 Update Nginx Configuration for SSL

Edit the nginx-domain.conf file:

```bash
nano nginx-domain.conf
```

Replace the content with:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    location / {
        return 301 https://$host$request_uri;
    }
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location /static/ {
        alias /static/;
        expires 30d;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3.4 Restart Nginx

```bash
docker-compose restart nginx
```

## 4. Maintenance

### 4.1 Checking Logs

```bash
# All logs
docker-compose logs

# Web application logs
docker-compose logs web

# Database logs
docker-compose logs db

# Nginx logs
docker-compose logs nginx
```

### 4.2 Backing Up the Database

```bash
docker-compose exec db mysqldump -u root -p[REDACTED] atp > atp_backup_$(date +%Y%m%d).sql
```

### 4.3 Restoring the Database

```bash
docker-compose exec -T db mysql -u root -p[REDACTED] atp < atp_backup.sql
```

### 4.4 Updating the Application

```bash
# Pull the latest changes (if using Git)
git pull

# Rebuild and restart the containers
docker-compose down
docker-compose build
docker-compose up -d
```

### 4.5 Renewing SSL Certificates

SSL certificates from Let's Encrypt are valid for 90 days. The certbot container will automatically try to renew them when they're close to expiration. To manually renew:

```bash
docker-compose run --rm certbot renew
```

## 5. Troubleshooting

### 5.1 Container Issues

If containers are not starting properly:

```bash
# Check container status
docker-compose ps

# Check container logs
docker-compose logs

# Restart containers
docker-compose down
docker-compose up -d
```

### 5.2 SAP Connection Issues

If you're having trouble connecting to SAP:

```bash
# Test SAP connection
docker-compose exec web python test_sap_connection.py

# Check SAP connection parameters
docker-compose exec web cat atp/atp/settings.ini
```

### 5.3 Static Files Issues

If static files are not loading:

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Restart Nginx
docker-compose restart nginx
```

### 5.4 Database Issues

If you're having database issues:

```bash
# Check database connection
docker-compose exec web python -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"

# Check database migrations
docker-compose exec web python manage.py showmigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

## 6. Security Considerations

### 6.1 Firewall Configuration

Configure the firewall to allow only necessary ports:

```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 6.2 Regular Updates

Keep your system and Docker images up to date:

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose down
docker-compose up -d
```

### 6.3 Database Password

Change the default database password in docker-compose.yml:

```yaml
db:
  environment:
    - MYSQL_ROOT_PASSWORD=your-secure-password
    - MYSQL_PASSWORD=your-secure-password
```

## 7. Performance Optimization

### 7.1 Nginx Caching

For better performance, you can enable Nginx caching by adding the following to your nginx-domain.conf:

```nginx
# Add inside the http block
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=atp_cache:10m max_size=500m inactive=60m;

# Add inside the server block
location / {
    proxy_cache atp_cache;
    proxy_cache_valid 200 60m;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
    proxy_cache_lock on;
    # ... existing proxy settings ...
}
```

### 7.2 Database Optimization

For better database performance:

```bash
# Add database indexes
docker-compose exec web python manage.py dbshell
```

Then in the MySQL shell:

```sql
-- Example: Add index to frequently queried fields
ALTER TABLE stockcheck_searchhistory ADD INDEX (time);
```

## 8. Monitoring (Optional)

### 8.1 Set Up Prometheus and Grafana

Create a docker-compose.monitoring.yml file:

```yaml
version: '3'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

Start the monitoring services:

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

## 9. Conclusion

Your ATP application should now be successfully deployed on your Ubuntu server. If you encounter any issues not covered in this guide, please refer to the official documentation for Docker, Django, and Nginx.