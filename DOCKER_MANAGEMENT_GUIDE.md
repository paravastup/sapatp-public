# Docker Management Guide - ATP Application

**Complete Guide to Managing ATP with Docker & Docker Compose**

**For developers with NO Docker experience**

**Version**: 1.0
**Last Updated**: November 1, 2025

---

## Table of Contents

1. [What is Docker?](#what-is-docker)
2. [What is Docker Compose?](#what-is-docker-compose)
3. [Understanding Dockerfile](#understanding-dockerfile)
4. [Understanding docker-compose.yml](#understanding-docker-composeyml)
5. [Essential Docker Commands](#essential-docker-commands)
6. [Essential Docker Compose Commands](#essential-docker-compose-commands)
7. [Container Management](#container-management)
8. [Volume Management](#volume-management)
9. [Network Management](#network-management)
10. [Logs & Debugging](#logs--debugging)
11. [Building & Rebuilding](#building--rebuilding)
12. [Environment Variables](#environment-variables)
13. [Troubleshooting Docker Issues](#troubleshooting-docker-issues)
14. [Docker Best Practices](#docker-best-practices)
15. [Backup & Restore](#backup--restore)
16. [Advanced Operations](#advanced-operations)

---

## What is Docker?

### Simple Explanation

**Docker** = A way to package your application with everything it needs to run

**Analogy**:
- **Without Docker**: Like giving someone ingredients and a recipe - they need to have a kitchen, right tools, right temperature
- **With Docker**: Like giving someone a ready-to-eat meal in a microwave-safe container - just heat and serve

### Why Docker?

**Problem**: "It works on my machine!"
- Different operating systems (Windows, Mac, Linux)
- Different Python versions
- Different library versions
- Different configurations

**Solution**: Docker container
- Same environment everywhere
- All dependencies included
- Works identically on any machine with Docker

### Key Concepts

#### 1. **Image** = Blueprint
- Like a recipe or template
- Contains: OS, Python, libraries, your code
- Read-only
- Can be shared and reused

**Example**: `ubuntu:18.04` image contains Ubuntu 18.04 operating system

#### 2. **Container** = Running instance
- Like a running program created from an image
- Has its own filesystem, processes, network
- Can be started, stopped, deleted
- Multiple containers can run from same image

**Example**: `atp_web` container running from our custom ATP image

#### 3. **Volume** = Persistent storage
- Data that survives container restarts
- Like a shared folder between container and host
- Database data, logs, uploaded files

**Example**: `db_data` volume stores MySQL database files

#### 4. **Network** = Container communication
- Containers can talk to each other
- Isolated from host network by default

**Example**: `atp_network` allows web, db, nginx containers to communicate

### Docker vs Virtual Machines

```
Virtual Machine:
┌─────────────────────────┐
│   Your App              │
│   ├─ Python             │
│   └─ Libraries          │
├─────────────────────────┤
│   Guest OS (Full)       │  ← Heavy (GBs)
├─────────────────────────┤
│   Hypervisor            │
├─────────────────────────┤
│   Host OS               │
└─────────────────────────┘

Docker Container:
┌─────────────────────────┐
│   Your App              │
│   ├─ Python             │
│   └─ Libraries          │
├─────────────────────────┤
│   Container Runtime     │  ← Lightweight (MBs)
├─────────────────────────┤
│   Host OS               │
└─────────────────────────┘
```

**Docker is faster and uses less resources!**

---

## What is Docker Compose?

### Simple Explanation

**Docker Compose** = Tool to manage multiple Docker containers together

**Analogy**:
- **Docker**: Managing one person
- **Docker Compose**: Managing an entire team

### Why Docker Compose?

**Problem**: ATP application needs multiple services:
- Web application (Django + Gunicorn)
- Database (MySQL)
- Reverse proxy (Nginx)

**Without Compose**: Run 3 separate `docker run` commands with lots of flags
**With Compose**: One `docker-compose up` command

### How It Works

1. **Define** services in `docker-compose.yml` file
2. **Run** `docker-compose up`
3. **Docker Compose**:
   - Creates network
   - Creates volumes
   - Starts all containers
   - Connects them together

---

## Understanding Dockerfile

### What is a Dockerfile?

**Dockerfile** = Instructions to build a Docker image

**Like**: A recipe with step-by-step instructions

### ATP Dockerfile Explained

**File**: `/opt/app/Dockerfile`

```dockerfile
# 1. BASE IMAGE - Starting point
FROM ubuntu:18.04
# Like: "Start with a fresh Ubuntu 18.04 installation"

# 2. ENVIRONMENT VARIABLE
ENV DEBIAN_FRONTEND=noninteractive
# Prevents prompts during installation

# 3. INSTALL DEPENDENCIES
RUN apt-get update && apt-get install -y \
    python3.6 \
    python3-pip \
    build-essential \
    libmysqlclient-dev \
    netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Like: "Install Python 3.6, pip, and other tools"
# The && chains commands together
# apt-get clean removes cached files to reduce image size

# 4. CREATE SYMBOLIC LINKS
RUN ln -sf /usr/bin/python3.6 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip
# Makes 'python' command point to python3.6

# 5. SET WORKING DIRECTORY
WORKDIR /app
# All subsequent commands run from /app directory

# 6. COPY FILES
COPY nwrfcsdk /usr/nwrfcsdk
# Copy SAP RFC SDK to container

COPY atp /app
# Copy Django application code

COPY requirements.txt /app/
# Copy Python dependencies list

COPY pyrfc-1.9.93-cp36-cp36m-linux_x86_64.whl /app/
# Copy SAP RFC Python library

# 7. SET ENVIRONMENT VARIABLES
ENV LD_LIBRARY_PATH=/usr/nwrfcsdk/lib:$LD_LIBRARY_PATH
ENV SAPNWRFC_HOME=/usr/nwrfcsdk
# Tell system where to find SAP libraries

# 8. INSTALL PYTHON PACKAGES
RUN pip install --upgrade pip \
    && pip install /app/pyrfc-1.9.93-cp36-cp36m-linux_x86_64.whl \
    && pip install -r requirements.txt \
    && pip install mysqlclient gunicorn djangorestframework djangorestframework-jwt
# Install all Python dependencies

# 9. CREATE DIRECTORIES
RUN mkdir -p /app/sock /var/log/gunicorn \
    && chmod 777 /app/sock /var/log/gunicorn
# Create folders for Unix socket and logs
# chmod 777 gives full permissions

# 10. EXPOSE PORT
EXPOSE 8000
# Tells Docker this container listens on port 8000
# (Doesn't actually publish the port - that's done in docker-compose.yml)

# 11. STARTUP COMMAND
CMD bash -c "echo 'Waiting for MySQL...' && \
    while ! nc -z db 3306; do sleep 1; done && \
    echo 'MySQL started' && \
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn --bind 0.0.0.0:8000 --timeout 120 --workers 2 atp.wsgi:application"
# What happens when container starts:
# 1. Wait for MySQL to be ready (nc -z db 3306 checks connection)
# 2. Run database migrations
# 3. Collect static files (CSS, JS)
# 4. Start Gunicorn web server on port 8000
```

### Dockerfile Commands Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `FROM` | Set base image | `FROM ubuntu:18.04` |
| `RUN` | Execute command during build | `RUN apt-get install python3` |
| `COPY` | Copy files from host to container | `COPY app /app` |
| `ADD` | Like COPY but can extract archives | `ADD file.tar.gz /app` |
| `WORKDIR` | Set working directory | `WORKDIR /app` |
| `ENV` | Set environment variable | `ENV DEBUG=False` |
| `EXPOSE` | Document which port is used | `EXPOSE 8000` |
| `CMD` | Default command when container starts | `CMD ["python", "app.py"]` |
| `ENTRYPOINT` | Configure container as executable | `ENTRYPOINT ["python"]` |

### Building an Image from Dockerfile

```bash
# Build image with tag 'atp-web'
docker build -t atp-web .

# Build without cache (force rebuild)
docker build --no-cache -t atp-web .

# Build with build arguments
docker build --build-arg PYTHON_VERSION=3.6 -t atp-web .
```

---

## Understanding docker-compose.yml

### What is docker-compose.yml?

**docker-compose.yml** = Configuration file that defines:
- All services (containers)
- Networks
- Volumes
- Environment variables
- Dependencies

### ATP docker-compose.yml Explained

**File**: `/opt/app/docker-compose-port5000-secure.yml`

```yaml
# VERSION (optional)
version: '3.8'  # Docker Compose file format version

# SERVICES - Define containers
services:

  # ============================================
  # WEB SERVICE (Django Application)
  # ============================================
  web:
    # How to build this container
    build: .
    # Looks for Dockerfile in current directory

    # Container name
    container_name: atp_web
    # Without this, name would be auto-generated like "sapatp_web_1"

    # Ports to expose (but not publish to host)
    expose:
      - "8000"
    # Makes port 8000 available to other containers
    # NOT accessible from host machine

    # Volumes - Map host folders to container folders
    volumes:
      - ./atp:/app
      # Host: ./atp → Container: /app
      # Changes to code on host reflect in container immediately

      - ./nwrfcsdk:/usr/nwrfcsdk
      # SAP SDK files

      - log_data:/var/log/gunicorn
      # Named volume for logs (persists across restarts)

      - static_volume:/app/static
      # Named volume for static files (CSS, JS, images)

    # Environment variables
    environment:
      - PYTHONUNBUFFERED=1
        # Print output immediately (don't buffer)

      - DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-atp.settings_secure}
        # Use environment variable or default to atp.settings_secure

      - RUNNING_IN_DOCKER=1
        # Tell Django it's running in Docker

      - OLLAMA_BASE_URL=http://192.168.1.101:11434
        # AI model server URL (Windows host)

      - OLLAMA_MODEL=atp-chatbot
        # Custom trained model name

      - OLLAMA_TIMEOUT=90
        # Timeout for AI requests (seconds)

    # Dependencies - Start these services first
    depends_on:
      - db
    # Ensures MySQL starts before web application

    # Restart policy
    restart: unless-stopped
    # Restart container if it crashes (unless manually stopped)

    # Network
    networks:
      - atp_network
    # Connect to custom network

    # Extra hosts (add to /etc/hosts in container)
    extra_hosts:
      - "host.wsl.internal:192.168.1.101"
    # Maps hostname to IP for WSL2 Windows host access

  # ============================================
  # DATABASE SERVICE (MySQL)
  # ============================================
  db:
    # Use pre-built image from Docker Hub
    image: mysql:5.7
    # Instead of building, pull from registry

    # Container name
    container_name: atp_db

    # Volumes for persistent data
    volumes:
      - db_data:/var/lib/mysql
      # MySQL data files stored in named volume
      # Survives container deletion!

    # Environment variables for MySQL
    environment:
      - MYSQL_DATABASE=${DATABASE_NAME:-atp}
        # Create database named 'atp'

      - MYSQL_USER=${DATABASE_USER:-djangoadmin}
        # Create user 'djangoadmin'

      - MYSQL_PASSWORD=${DATABASE_PASSWORD:-DummyPass123!}
        # Set user password

      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-DummyPass123!}
        # Set root password

    # Publish ports to host
    ports:
      - "3306:3306"
    # Host:3306 → Container:3306
    # Allows direct MySQL access from host

    # Restart policy
    restart: unless-stopped

    # Network
    networks:
      - atp_network

    # Health check
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      # Check if MySQL is responding

      interval: 10s
      # Check every 10 seconds

      timeout: 5s
      # Give up if check takes > 5 seconds

      retries: 5
      # Retry 5 times before marking unhealthy

  # ============================================
  # NGINX SERVICE (Reverse Proxy)
  # ============================================
  nginx:
    # Pre-built image
    image: nginx:1.19

    # Container name
    container_name: atp_nginx

    # Volumes
    volumes:
      - ./nginx-fixed.conf:/etc/nginx/conf.d/default.conf:ro
      # Mount config file as read-only (:ro)

      - static_volume:/static:ro
      # Mount static files as read-only

    # Publish ports
    ports:
      - "5000:80"
      # Host:5000 → Container:80
      # Access app at http://localhost:5000

    # Dependencies
    depends_on:
      - web
    # Start after web service

    # Restart policy
    restart: unless-stopped

    # Network
    networks:
      - atp_network

# ============================================
# NETWORKS - Define custom networks
# ============================================
networks:
  atp_network:
    driver: bridge
    # Bridge network allows container-to-container communication

# ============================================
# VOLUMES - Define named volumes
# ============================================
volumes:
  db_data:
    # MySQL database files
    # Persists across container restarts/deletions

  log_data:
    # Application logs

  static_volume:
    # Static files (CSS, JS, images)
```

### YAML Syntax Basics

```yaml
# Comments start with #

# Key-value pairs
key: value

# Nested structures (use indentation)
parent:
  child: value
  another_child: value2

# Lists
items:
  - item1
  - item2
  - item3

# Or inline
items: [item1, item2, item3]

# Multi-line strings
description: |
  This is a
  multi-line
  string

# Environment variable substitution
value: ${ENV_VAR}
value: ${ENV_VAR:-default}  # With default
```

### Common docker-compose.yml Sections

| Section | Purpose | Example |
|---------|---------|---------|
| `version` | Compose file version | `version: '3.8'` |
| `services` | Define containers | `services:` |
| `build` | Build from Dockerfile | `build: .` |
| `image` | Use pre-built image | `image: mysql:5.7` |
| `container_name` | Custom container name | `container_name: atp_web` |
| `ports` | Publish ports to host | `ports: ["5000:80"]` |
| `expose` | Expose to other containers | `expose: ["8000"]` |
| `volumes` | Mount volumes | `volumes: ["./app:/app"]` |
| `environment` | Set env variables | `environment: ["DEBUG=False"]` |
| `depends_on` | Service dependencies | `depends_on: [db]` |
| `networks` | Connect to networks | `networks: [atp_network]` |
| `restart` | Restart policy | `restart: unless-stopped` |

---

## Essential Docker Commands

### Container Lifecycle

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List with specific format
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Start a container
docker start atp_web

# Stop a container
docker stop atp_web

# Restart a container
docker restart atp_web

# Pause a container (freeze processes)
docker pause atp_web

# Unpause
docker unpause atp_web

# Remove a container
docker rm atp_web

# Remove a running container (force)
docker rm -f atp_web

# Remove all stopped containers
docker container prune
```

### Running Containers

```bash
# Run container from image
docker run ubuntu:18.04

# Run with name
docker run --name my-container ubuntu:18.04

# Run in background (-d = detached)
docker run -d ubuntu:18.04

# Run with port mapping
docker run -p 8000:8000 my-image

# Run with volume
docker run -v /host/path:/container/path my-image

# Run with environment variable
docker run -e DEBUG=True my-image

# Run and remove after exit (--rm)
docker run --rm ubuntu:18.04 echo "Hello"

# Run interactive terminal (-it)
docker run -it ubuntu:18.04 bash

# Run with restart policy
docker run --restart unless-stopped my-image
```

### Executing Commands in Containers

```bash
# Execute command in running container
docker exec atp_web ls -la

# Open interactive shell
docker exec -it atp_web bash

# Execute as different user
docker exec -u root atp_web whoami

# Execute with working directory
docker exec -w /app atp_web python manage.py shell

# ATP Examples:
# Django shell
docker exec -it atp_web python manage.py shell

# Django migrations
docker exec atp_web python manage.py migrate

# Create superuser
docker exec -it atp_web python manage.py createsuperuser

# Check logs
docker exec atp_web cat /var/log/gunicorn/access.log
```

### Logs

```bash
# View logs
docker logs atp_web

# Follow logs (like tail -f)
docker logs -f atp_web

# Show last 100 lines
docker logs --tail 100 atp_web

# Show logs since timestamp
docker logs --since 2025-11-01T10:00:00 atp_web

# Show logs with timestamps
docker logs -t atp_web
```

### Images

```bash
# List images
docker images

# Pull image from registry
docker pull ubuntu:18.04

# Build image from Dockerfile
docker build -t my-image .

# Build without cache
docker build --no-cache -t my-image .

# Tag an image
docker tag my-image my-image:v1.0

# Remove image
docker rmi my-image

# Remove unused images
docker image prune

# Remove all images (dangerous!)
docker image prune -a
```

### System Information

```bash
# Show Docker version
docker version

# Show system info
docker info

# Show disk usage
docker system df

# Show detailed disk usage
docker system df -v

# Show resource usage (live)
docker stats

# Show resource usage for specific container
docker stats atp_web

# Inspect container details (JSON)
docker inspect atp_web

# Inspect specific field
docker inspect --format='{{.State.Status}}' atp_web
```

---

## Essential Docker Compose Commands

### Basic Operations

```bash
# Start all services
docker-compose up

# Start in background (-d = detached)
docker-compose up -d

# Start specific service
docker-compose up web

# Start with specific file
docker-compose -f docker-compose-port5000-secure.yml up -d

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data!)
docker-compose down -v

# Stop services but keep containers
docker-compose stop

# Start stopped services
docker-compose start

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart web
```

### Building

```bash
# Build images
docker-compose build

# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build web

# Build and start
docker-compose up --build

# Force recreate containers
docker-compose up -d --force-recreate
```

### Viewing Status

```bash
# List running services
docker-compose ps

# Show logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Show logs for specific service
docker-compose logs -f web

# Show last 100 lines
docker-compose logs --tail=100

# Show logs with timestamps
docker-compose logs -t
```

### Executing Commands

```bash
# Execute command in service
docker-compose exec web ls -la

# Open shell in service
docker-compose exec web bash

# Execute without interactive TTY (-T)
docker-compose exec -T web python manage.py migrate

# ATP Examples:
# Django shell
docker-compose exec web python manage.py shell

# Database migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access MySQL
docker-compose exec db mysql -uroot -p atp
```

### Advanced Operations

```bash
# Validate docker-compose.yml
docker-compose config

# Show config with resolved variables
docker-compose config --resolve-image-digests

# Pull images without starting
docker-compose pull

# Scale service (run multiple instances)
docker-compose up -d --scale web=3

# Show running processes in containers
docker-compose top

# Pause services
docker-compose pause

# Unpause services
docker-compose unpause

# Show events from containers
docker-compose events
```

---

## Container Management

### Starting the ATP Application

```bash
# Method 1: Simple (uses docker-compose.yml)
cd /opt/app
docker-compose up -d

# Method 2: Specific file (PRODUCTION)
cd /opt/app
docker-compose -f docker-compose-port5000-secure.yml up -d

# What happens:
# 1. Creates network: atp_network
# 2. Creates volumes: db_data, log_data, static_volume
# 3. Pulls/builds images
# 4. Starts containers: db → web → nginx (in order)
```

### Stopping the Application

```bash
# Stop all containers (keeps containers and data)
docker-compose -f docker-compose-port5000-secure.yml stop

# Stop and remove containers (keeps data)
docker-compose -f docker-compose-port5000-secure.yml down

# Stop, remove containers AND volumes (⚠️ DELETES DATABASE!)
docker-compose -f docker-compose-port5000-secure.yml down -v
```

### Restarting Services

```bash
# Restart all services
docker-compose -f docker-compose-port5000-secure.yml restart

# Restart specific service
docker-compose -f docker-compose-port5000-secure.yml restart web

# Restart with rebuild
docker-compose -f docker-compose-port5000-secure.yml up -d --build

# Force recreate
docker-compose -f docker-compose-port5000-secure.yml up -d --force-recreate
```

### Checking Status

```bash
# Show running containers
docker-compose -f docker-compose-port5000-secure.yml ps

# Show all containers (including stopped)
docker-compose -f docker-compose-port5000-secure.yml ps -a

# Check health status
docker-compose -f docker-compose-port5000-secure.yml ps
# Look for "Up (healthy)" status

# Show resource usage
docker stats atp_web atp_db atp_nginx
```

---

## Volume Management

### What are Volumes?

**Volumes** = Persistent storage that survives container deletion

**ATP uses 3 volumes**:
1. `db_data` - MySQL database files
2. `log_data` - Application logs
3. `static_volume` - Static files (CSS, JS, images)

### Volume Commands

```bash
# List all volumes
docker volume ls

# Inspect volume
docker volume inspect db_data

# Create volume
docker volume create my_volume

# Remove volume
docker volume rm db_data

# Remove all unused volumes
docker volume prune

# Remove specific volume (with confirmation)
docker volume rm db_data
```

### ATP Volume Locations

```bash
# Find where volumes are stored on host
docker volume inspect db_data
# Look for "Mountpoint" field

# Example output:
# "Mountpoint": "/var/lib/docker/volumes/db_data/_data"

# Access volume data (need sudo)
sudo ls -la /var/lib/docker/volumes/db_data/_data
```

### Backing Up Volumes

```bash
# Backup database volume
docker run --rm \
  -v db_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/db_backup.tar.gz /data

# Restore database volume
docker run --rm \
  -v db_data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/db_backup.tar.gz -C /
```

### ATP-Specific Volume Operations

```bash
# Backup MySQL database (preferred method)
docker-compose -f docker-compose-port5000-secure.yml exec db \
  mysqldump -uroot -p atp > backup_$(date +%Y%m%d).sql

# Restore MySQL database
cat backup_20251101.sql | docker-compose -f docker-compose-port5000-secure.yml exec -T db \
  mysql -uroot -p atp

# Clear logs volume
docker volume rm log_data
docker volume create log_data
docker-compose -f docker-compose-port5000-secure.yml restart web
```

---

## Network Management

### What are Docker Networks?

**Networks** = Allow containers to communicate

**ATP uses bridge network**: `atp_network`
- Containers can reach each other by service name
- Example: web container can connect to `db:3306`

### Network Commands

```bash
# List networks
docker network ls

# Inspect network
docker network inspect atp_network

# Create network
docker network create my_network

# Remove network
docker network rm atp_network

# Connect container to network
docker network connect atp_network my_container

# Disconnect
docker network disconnect atp_network my_container
```

### ATP Network Details

```bash
# See all containers on atp_network
docker network inspect atp_network

# Output shows:
# - atp_web (172.22.0.3)
# - atp_db (172.22.0.2)
# - atp_nginx (172.22.0.4)

# Test connectivity between containers
docker exec atp_web ping atp_db
docker exec atp_web nc -zv db 3306
```

---

## Logs & Debugging

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose-port5000-secure.yml logs

# Follow logs (live)
docker-compose -f docker-compose-port5000-secure.yml logs -f

# Specific service
docker-compose -f docker-compose-port5000-secure.yml logs web
docker-compose -f docker-compose-port5000-secure.yml logs db
docker-compose -f docker-compose-port5000-secure.yml logs nginx

# Last 100 lines
docker-compose -f docker-compose-port5000-secure.yml logs --tail=100

# Since timestamp
docker-compose -f docker-compose-port5000-secure.yml logs --since 2025-11-01T10:00:00

# Grep for errors
docker-compose -f docker-compose-port5000-secure.yml logs web | grep -i error
```

### Debugging Containers

```bash
# Check if container is running
docker ps | grep atp_web

# Check container logs
docker logs atp_web

# Check container processes
docker top atp_web

# Check resource usage
docker stats atp_web

# Inspect container configuration
docker inspect atp_web

# Check container exit code
docker inspect --format='{{.State.ExitCode}}' atp_web

# Open shell in container
docker exec -it atp_web bash

# Check environment variables
docker exec atp_web env

# Check Django configuration
docker exec atp_web python manage.py check

# Test SAP connection
docker exec atp_web python -c "from stockcheck.sap_utils import get_sap_connection; print(get_sap_connection().ping())"

# Test Ollama connection
docker exec atp_web curl http://192.168.1.101:11434/api/tags
```

### Common Debug Scenarios

#### Container Won't Start

```bash
# Check logs for error
docker-compose -f docker-compose-port5000-secure.yml logs web

# Check previous container instance
docker logs atp_web

# Inspect container
docker inspect atp_web

# Common issues:
# - Port already in use
# - Volume permission issues
# - Missing environment variables
```

#### Container Exits Immediately

```bash
# Check exit code
docker inspect --format='{{.State.ExitCode}}' atp_web

# Common exit codes:
# 0 = Success (intentional exit)
# 1 = Application error
# 137 = Killed by system (out of memory)
# 139 = Segmentation fault
# 143 = Terminated by SIGTERM

# Check logs
docker logs atp_web
```

#### Network Issues

```bash
# Check container can reach database
docker exec atp_web ping atp_db

# Check port is open
docker exec atp_web nc -zv db 3306

# Check network
docker network inspect atp_network

# Check DNS resolution
docker exec atp_web nslookup db
```

---

## Building & Rebuilding

### When to Rebuild

**Rebuild when**:
- Dockerfile changed
- Code changed (if not using volumes)
- Dependencies changed (requirements.txt)
- Base image updated

### Building Images

```bash
# Build all images
docker-compose -f docker-compose-port5000-secure.yml build

# Build specific service
docker-compose -f docker-compose-port5000-secure.yml build web

# Build without cache (force full rebuild)
docker-compose -f docker-compose-port5000-secure.yml build --no-cache

# Build with pull (get latest base images)
docker-compose -f docker-compose-port5000-secure.yml build --pull
```

### Rebuilding After Changes

```bash
# Rebuild and restart
docker-compose -f docker-compose-port5000-secure.yml up -d --build

# Force recreate containers
docker-compose -f docker-compose-port5000-secure.yml up -d --force-recreate

# Complete rebuild (nuclear option)
docker-compose -f docker-compose-port5000-secure.yml down
docker-compose -f docker-compose-port5000-secure.yml build --no-cache
docker-compose -f docker-compose-port5000-secure.yml up -d
```

### Updating Dependencies

```bash
# After changing requirements.txt:

# Method 1: Rebuild image
docker-compose -f docker-compose-port5000-secure.yml build --no-cache web
docker-compose -f docker-compose-port5000-secure.yml up -d

# Method 2: Install in running container (temporary)
docker exec atp_web pip install new-package

# For permanent changes, always update requirements.txt and rebuild
```

---

## Environment Variables

### Where Environment Variables Come From

1. **docker-compose.yml** - Defined in `environment:` section
2. **.env file** - Automatically loaded by docker-compose
3. **Host environment** - `${VAR}` substitution
4. **Command line** - `docker-compose up -e VAR=value`

### Using .env File

**File**: `/opt/app/.env`

```bash
# Database
DATABASE_NAME=atp
DATABASE_USER=djangoadmin
DATABASE_PASSWORD=SecurePassword123
MYSQL_ROOT_PASSWORD=RootPassword456

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False

# SAP
SAP_HOST=sap.company.com
SAP_USER=sapuser
SAP_PASSWORD=sappass

# Ollama
OLLAMA_MODEL=atp-chatbot
OLLAMA_TIMEOUT=90
```

**Then in docker-compose.yml**:
```yaml
environment:
  - DATABASE_PASSWORD=${DATABASE_PASSWORD}
  - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
```

### Viewing Environment Variables

```bash
# In container
docker exec atp_web env

# Specific variable
docker exec atp_web printenv DATABASE_NAME

# From docker-compose
docker-compose -f docker-compose-port5000-secure.yml config
```

### Overriding Environment Variables

```bash
# Command line
docker-compose -f docker-compose-port5000-secure.yml up -d \
  -e DEBUG=True

# .env file (preferred for secrets)
echo "DATABASE_PASSWORD=NewPassword" >> .env
docker-compose -f docker-compose-port5000-secure.yml up -d
```

---

## Troubleshooting Docker Issues

### Container Won't Start

**Symptom**: `docker ps` doesn't show container

**Solution**:
```bash
# 1. Check logs
docker-compose -f docker-compose-port5000-secure.yml logs web

# 2. Check previous instance
docker logs atp_web

# 3. Try starting manually
docker start atp_web

# 4. Check for port conflicts
netstat -tuln | grep 5000  # Linux
netstat -an | findstr 5000  # Windows

# 5. Remove and recreate
docker rm atp_web
docker-compose -f docker-compose-port5000-secure.yml up -d
```

### Port Already in Use

**Error**: `Bind for 0.0.0.0:5000 failed: port is already allocated`

**Solution**:
```bash
# Find what's using the port
# Linux:
sudo lsof -i :5000
sudo netstat -tuln | grep 5000

# Windows:
netstat -ano | findstr :5000

# Kill the process or change port in docker-compose.yml
ports:
  - "5001:80"  # Use port 5001 instead
```

### Permission Denied Errors

**Error**: `Permission denied` when accessing volumes

**Solution**:
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./atp
sudo chmod -R 755 ./atp

# Or run container as your user
docker-compose exec -u $(id -u):$(id -g) web bash
```

### Out of Disk Space

**Symptom**: Build fails with "no space left on device"

**Solution**:
```bash
# Check disk usage
docker system df

# Clean up
docker system prune  # Remove unused data
docker image prune -a  # Remove all unused images
docker volume prune  # Remove unused volumes

# Nuclear option (removes EVERYTHING)
docker system prune -a --volumes
```

### Database Connection Errors

**Error**: `Can't connect to MySQL server`

**Solution**:
```bash
# 1. Check database is running
docker ps | grep atp_db

# 2. Check database health
docker inspect atp_db | grep Health

# 3. Check web can reach database
docker exec atp_web ping atp_db
docker exec atp_web nc -zv db 3306

# 4. Check database logs
docker logs atp_db

# 5. Restart database
docker restart atp_db
```

### Docker Daemon Not Running

**Error**: `Cannot connect to the Docker daemon`

**Solution**:
```bash
# Linux:
sudo systemctl start docker
sudo systemctl enable docker

# Windows/Mac:
# Start Docker Desktop application

# Check status
docker version
```

---

## Docker Best Practices

### 1. Use .dockerignore

**File**: `.dockerignore`
```
__pycache__
*.pyc
*.pyo
*.log
.git
.env
*.md
node_modules
```

**Why**: Reduces build context size, faster builds

### 2. Layer Caching

```dockerfile
# ❌ BAD - Reinstalls dependencies every code change
COPY . /app
RUN pip install -r requirements.txt

# ✅ GOOD - Caches dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
```

### 3. Multi-Stage Builds

```dockerfile
# Build stage
FROM python:3.6 AS builder
RUN pip install -r requirements.txt

# Production stage
FROM python:3.6-slim
COPY --from=builder /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY . /app
```

### 4. Use Specific Tags

```yaml
# ❌ BAD
image: mysql:latest

# ✅ GOOD
image: mysql:5.7
```

### 5. Minimize Layers

```dockerfile
# ❌ BAD - 3 layers
RUN apt-get update
RUN apt-get install python3
RUN apt-get clean

# ✅ GOOD - 1 layer
RUN apt-get update && \
    apt-get install python3 && \
    apt-get clean
```

### 6. Don't Run as Root

```dockerfile
# Create non-root user
RUN useradd -m appuser
USER appuser
```

### 7. Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import sys; sys.exit(0)"
```

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000"]
  interval: 30s
  timeout: 3s
  retries: 3
```

---

## Backup & Restore

### Backup Everything

```bash
#!/bin/bash
# backup_atp.sh

BACKUP_DIR="/backups/atp_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 1. Backup database
docker-compose -f docker-compose-port5000-secure.yml exec -T db \
  mysqldump -uroot -p$MYSQL_ROOT_PASSWORD atp > $BACKUP_DIR/database.sql

# 2. Backup volumes
docker run --rm \
  -v db_data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/db_data.tar.gz /data

# 3. Backup code
tar czf $BACKUP_DIR/atp_code.tar.gz ./atp

# 4. Backup docker-compose files
cp docker-compose-port5000-secure.yml $BACKUP_DIR/
cp Dockerfile $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

### Restore from Backup

```bash
#!/bin/bash
# restore_atp.sh

BACKUP_DIR=$1

# 1. Stop application
docker-compose -f docker-compose-port5000-secure.yml down

# 2. Restore database volume
docker run --rm \
  -v db_data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar xzf /backup/db_data.tar.gz -C /

# 3. Restore code
tar xzf $BACKUP_DIR/atp_code.tar.gz

# 4. Start application
docker-compose -f docker-compose-port5000-secure.yml up -d

# 5. Verify
docker-compose -f docker-compose-port5000-secure.yml ps
```

---

## Advanced Operations

### Scaling Services

```bash
# Run 3 instances of web service
docker-compose -f docker-compose-port5000-secure.yml up -d --scale web=3

# Check running instances
docker-compose -f docker-compose-port5000-secure.yml ps

# Note: Need load balancer (nginx) to distribute traffic
```

### Custom Networks

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  web:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend  # Only accessible from backend network
```

### Resource Limits

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.5'      # Max 50% of one CPU
          memory: 512M     # Max 512 MB RAM
        reservations:
          cpus: '0.25'     # Reserved CPU
          memory: 256M     # Reserved RAM
```

### Secrets Management

```yaml
# docker-compose.yml (v3.1+)
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  db:
    secrets:
      - db_password
    environment:
      MYSQL_PASSWORD_FILE: /run/secrets/db_password
```

### Docker Registry

```bash
# Tag image for registry
docker tag atp-web myregistry.com/atp-web:1.0

# Push to registry
docker push myregistry.com/atp-web:1.0

# Pull from registry
docker pull myregistry.com/atp-web:1.0
```

---

## Quick Reference Card

### Most Used Commands

```bash
# START APPLICATION
docker-compose -f docker-compose-port5000-secure.yml up -d

# STOP APPLICATION
docker-compose -f docker-compose-port5000-secure.yml down

# RESTART
docker-compose -f docker-compose-port5000-secure.yml restart

# VIEW LOGS
docker-compose -f docker-compose-port5000-secure.yml logs -f

# CHECK STATUS
docker-compose -f docker-compose-port5000-secure.yml ps

# REBUILD
docker-compose -f docker-compose-port5000-secure.yml up -d --build

# EXECUTE COMMAND
docker-compose -f docker-compose-port5000-secure.yml exec web bash

# DATABASE BACKUP
docker-compose -f docker-compose-port5000-secure.yml exec db \
  mysqldump -uroot -p atp > backup.sql

# CLEAN UP
docker system prune
```

---

## Summary

This guide covered:
- ✅ What Docker and Docker Compose are
- ✅ Understanding Dockerfile (line-by-line)
- ✅ Understanding docker-compose.yml (complete breakdown)
- ✅ All essential Docker commands
- ✅ All essential Docker Compose commands
- ✅ Container management
- ✅ Volume management (persistent storage)
- ✅ Network management
- ✅ Logs and debugging
- ✅ Building and rebuilding
- ✅ Environment variables
- ✅ Troubleshooting common issues
- ✅ Docker best practices
- ✅ Backup and restore procedures
- ✅ Advanced operations

**For More Help**:
- Docker docs: https://docs.docker.com/
- Docker Compose docs: https://docs.docker.com/compose/
- ATP-specific: See DEVELOPER_GUIDE.md

---

**Last Updated**: November 1, 2025
**Version**: 1.0
