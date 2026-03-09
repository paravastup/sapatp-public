# ATP Application - Complete Developer Guide

**Version**: 1.0
**Last Updated**: November 1, 2025
**Maintainer**: System Administrator

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Getting Started](#getting-started)
5. [Application Components](#application-components)
6. [AI Chatbot System](#ai-chatbot-system)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Deployment](#deployment)
10. [Maintenance Tasks](#maintenance-tasks)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)

---

## Overview

ATP (Available to Promise) is a Django-based web middleware application that connects to SAP systems to provide real-time product availability checking across multiple manufacturing plants. The application features an AI-powered conversational chatbot for natural language queries.

### Key Features
- Real-time SAP integration via RFC (Remote Function Call)
- Multi-plant product availability checking
- AI-powered conversational chatbot with context awareness
- Excel/CSV export functionality
- Search history tracking
- User authentication and session management

### Business Purpose
Allows users to quickly check product stock, delivery dates, and product information across manufacturing plants without directly accessing SAP systems.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                     (Port 5000/HTTP)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Nginx Container                           │
│              (Reverse Proxy - Port 80)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Django Application                          │
│             (Gunicorn + Python 3.6)                          │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Stock Check Module (Traditional UI)               │     │
│  │  - SAP RFC Integration                             │     │
│  │  - Product Search                                  │     │
│  │  - Multi-table Queries (M01, ARC, EL1)            │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  AI Chatbot Module (Conversational Interface)      │     │
│  │  - Natural Language Processing                     │     │
│  │  - Context-Aware Conversations                     │     │
│  │  - Ollama Integration (gemma3:4b)                 │     │
│  │  - Custom Trained Model (618 examples)            │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────┬───────────────────────┬─────────────────────┘
               │                       │
     ┌─────────▼────────┐    ┌────────▼────────────────┐
     │  MySQL Database  │    │  Ollama AI Server       │
     │   (Port 3306)    │    │  (Windows Host:11434)   │
     │                  │    │  Model: atp-chatbot     │
     │  - Users         │    │  Base: gemma3:4b        │
     │  - Conversations │    │  Training: 618 examples │
     │  - Search History│    └─────────────────────────┘
     └──────────────────┘
               │
     ┌─────────▼────────┐
     │   SAP System     │
     │   (RFC/BAPI)     │
     │                  │
     │  - MARA (M01)    │
     │  - MARC (ARC)    │
     │  - EKET (EL1)    │
     └──────────────────┘
```

### Network Architecture
- **External**: Port 5000 → Nginx → Gunicorn (port 8000)
- **Internal Docker Network**: `atp_network` (bridge mode)
- **SAP Connection**: pyrfc library over RFC protocol
- **AI Model**: HTTP API to Ollama on Windows host (192.168.1.101:11434)

---

## Technology Stack

### Backend
- **Framework**: Django 2.1.5 (Python 3.6)
- **WSGI Server**: Gunicorn 19.9.0 (2 workers, 120s timeout)
- **Database**: MySQL 5.7
- **SAP Integration**: pyrfc 1.9.93 (SAP NetWeaver RFC SDK)

### AI/ML Components
- **LLM Server**: Ollama (running on Windows host)
- **Base Model**: gemma3:4b (4 billion parameters)
- **Custom Model**: atp-chatbot (trained with 618 examples)
- **Training Method**: Few-shot learning via Modelfile

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Bootstrap 4.1.3
- **JavaScript**: jQuery 3.3.1, vanilla JS
- **AJAX**: Real-time chat communication

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx 1.19
- **Operating System**: Ubuntu 18.04 (container), WSL2 (host)

### Python Packages (Key Dependencies)
```
Django==2.1.5
mysqlclient==1.4.1
gunicorn==19.9.0
pyrfc==1.9.93
requests==2.21.0
numpy==1.16.1
XlsxWriter==1.1.2
```

---

## Getting Started

### Prerequisites
1. **Docker & Docker Compose** installed
2. **Ollama** installed on Windows host (with atp-chatbot model)
3. **SAP Access** credentials and network connectivity
4. **MySQL** client (optional, for database management)

### Quick Start

#### 1. Clone the Repository
```bash
cd /opt/app
git pull origin security-improvements-oct31
```

#### 2. Environment Configuration
**Important**: Never commit sensitive credentials to git!

Create environment variables (already configured in docker-compose.yml):
- `DATABASE_NAME`: atp
- `DATABASE_USER`: djangoadmin
- `DATABASE_PASSWORD`: DummyPass123! (CHANGE IN PRODUCTION!)
- `OLLAMA_BASE_URL`: http://192.168.1.101:11434
- `OLLAMA_MODEL`: atp-chatbot
- `OLLAMA_TIMEOUT`: 90

#### 3. Start the Application
```bash
cd /opt/app
docker-compose -f docker-compose-port5000-secure.yml up -d
```

Wait 30 seconds for database initialization, then check:
```bash
docker-compose -f docker-compose-port5000-secure.yml logs -f
```

#### 4. Access the Application
- **Main Page**: http://localhost:5000/
- **Login Page**: http://localhost:5000/atp/login/
- **Admin Panel**: http://localhost:5000/atp/admin/ (admin/DummyPass123!)
- **AI Chat**: http://localhost:5000/atp/chat/

#### 5. First Login
Default superuser:
- Username: `admin`
- Password: `DummyPass123!`

**CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!**

---

## Application Components

### 1. Stock Check Module (`stockcheck/`)

**Purpose**: Traditional form-based product search interface

**Key Files**:
- `models.py`: User, Plant, SearchHistory models
- `views.py`: Search, results, export views
- `forms.py`: Product search form with validation
- `sap_utils.py`: SAP RFC connection and data retrieval
- `templates/stockcheck/`: HTML templates

**SAP Tables Used**:
- **MARA (M01)**: Material Master (product details)
  - Fields: MATNR (product #), MAKTX (description), EAN11 (UPC), BISMT (vendor SKU), ZBRDES (brand), HERKL (origin), BRGEW (weight), UMREZ (case pack)

- **MARC (ARC)**: Plant Data (stock levels)
  - Fields: MATNR, WERKS (plant), LABST (stock quantity)

- **EKET (EL1)**: Delivery Schedule
  - Fields: MATNR, WERKS, EINDT (delivery date), MENGE (quantity)

**Workflow**:
1. User enters product number(s) in search form
2. Django validates input (prevents SQL injection, command injection)
3. pyrfc connects to SAP and executes RFC_READ_TABLE
4. Results fetched from M01, ARC, EL1 tables
5. Data formatted and displayed in results page
6. User can export to Excel/CSV
7. Search saved to history

### 2. AI Chatbot Module (`chatbot/`)

**Purpose**: Natural language conversational interface to SAP data

**Architecture**:
```
User Message → Django View → Intent Classification (Ollama)
                            ↓
                     Entity Extraction (Ollama)
                            ↓
                     Context Management (Database)
                            ↓
                     Query Execution (SAP RFC)
                            ↓
                     Response Generation (Template-based)
                            ↓
                     User Response (JSON)
```

**Key Components**:

#### a. Intent Classifier (`services/intent_classifier.py`)
**Purpose**: Determine what the user wants to do

**Supported Intents**:
- `greeting`: "Hello", "Hi", "Good morning"
- `help`: "What can you do?", "Help me"
- `stock_query`: "Check stock for 10001", "How many units?"
- `delivery_query`: "When is 10001 arriving?", "ETA?"
- `product_info`: "What's the UPC?", "Show brand", "Origin?"
- `plant_selection`: "Switch to plant 1000", "Change plant"
- `export_request`: "Export to Excel", "Download as PDF"
- `farewell`: "Goodbye", "Thanks", "Bye"
- `unknown`: Unrelated queries

**How It Works**:
1. Calls Ollama API with user message
2. LLM returns JSON: `{"intent": "stock_query", "confidence": 0.92}`
3. Falls back to keyword matching if API fails

#### b. Entity Extractor (`services/entity_extractor.py`)
**Purpose**: Extract structured data from user message

**Extracts**:
- `product_numbers`: ["10001", "10002"]
- `plant_code`: "1000"
- `vendor_skus`: ["ABC123"]
- `field_requested`: "upc", "brand", "origin"
- `from_context`: true (inferred from conversation)
- `action_repeat`: true (user said "do the same")

**Context-Aware Features**:
- Remembers previously mentioned products
- Detects follow-up questions ("What's the UPC?" → uses last product)
- Recognizes action repeat phrases ("do the same with 10001")

#### c. Conversation Manager (`services/conversation_manager.py`)
**Purpose**: Maintain conversation state across messages

**Database Schema**:
```python
class Conversation(models.Model):
    user = ForeignKey(User)
    started_at = DateTimeField(auto_now_add=True)
    last_activity = DateTimeField(auto_now=True)
    is_active = BooleanField(default=True)
    context = JSONField()  # Stores: products, plant, last_intent, last_field
```

**Context Tracking**:
- **Product Context**: Remembers last 10 products queried
- **Intent Context**: Tracks last action (for "do the same")
- **Field Context**: Remembers last field requested (UPC, brand, etc.)
- **Plant Context**: Current plant selection (default: 1000)

**Example Context**:
```json
{
  "products": ["10001", "10002"],
  "current_plant": "1000",
  "last_intent": "product_info",
  "last_field_requested": "upc",
  "last_action_time": "2025-11-01T18:30:00Z"
}
```

#### d. Ollama Client (`services/ollama_client.py`)
**Purpose**: Interface with Ollama AI server

**Configuration**:
- **URL**: http://192.168.1.101:11434 (Windows host WSL bridge IP)
- **Model**: atp-chatbot (custom trained gemma3:4b)
- **Timeout**: 90 seconds
- **Retry Logic**: 3 attempts with exponential backoff

**API Calls**:
1. **Intent Classification**:
   ```python
   POST /api/generate
   {
     "model": "atp-chatbot",
     "prompt": "Classify: What's the stock of 10001?",
     "format": "json"
   }
   ```

2. **Entity Extraction**:
   ```python
   POST /api/generate
   {
     "model": "atp-chatbot",
     "prompt": "Extract entities: Check delivery for products 10001 and 10002",
     "format": "json"
   }
   ```

**Error Handling**:
- Connection timeout → Falls back to keyword matching
- Invalid JSON → Parses with regex
- Model loading → Waits and retries

#### e. Response Generator (`services/response_generator.py`)
**Purpose**: Create human-friendly responses from SAP data

**Response Types**:

1. **Stock Query Response**:
```
📦 Stock Information:

**Product 10001** - Premium Coffee Beans
• Plant 1000: 1,250 units
• Status: In Stock ✅

**Product 10002** - Organic Tea Leaves
• Plant 1000: 0 units
• Status: Out of Stock ❌
```

2. **Product Info Response (Field-Specific)**:
```
📋 UPC Information:

**10001** - Premium Coffee Beans
• UPC/EAN: 012345678901

**10002** - Organic Tea Leaves
• UPC/EAN: 987654321098
```

3. **Delivery Query Response**:
```
🚚 Delivery Schedule:

**Product 10001** - Premium Coffee Beans
• Next Delivery: 2025-11-15
• Quantity: 500 units
```

**Field Mapping** (SAP → Display):
```python
field_map = {
    'upc': ('EAN11', 'UPC/EAN'),
    'brand': ('ZBRDES', 'Brand'),
    'origin': ('HERKL', 'Origin'),
    'weight': ('BRGEW', 'Weight'),
    'case_pack': ('UMREZ', 'Case Pack'),
    'vendor_sku': ('BISMT', 'Vendor SKU')
}
```

#### f. Query Executor (`services/query_executor.py`)
**Purpose**: Execute SAP queries based on intent and entities

**Functions**:
- `execute_stock_query()`: Queries MARC table
- `execute_delivery_query()`: Queries EKET table
- `execute_product_info_query()`: Queries MARA table
- `execute_multi_table_query()`: Joins M01 + ARC + EL1

**Optimization**:
- Batch queries for multiple products
- Caches SAP connection
- Limits result sets (max 50 products)

### 3. Custom AI Model (`atp-chatbot`)

**Location**: Ollama model repository (Windows host)

**Model Details**:
- **Base Model**: gemma3:4b (Google's Gemma 3, 4 billion parameters)
- **Custom Training**: 618 domain-specific examples
- **Training Method**: Few-shot learning (embedded in system prompt)
- **Model Size**: ~3 GB
- **Response Time**: 10-15 seconds per query

**Training Data Sources**:
1. **Your SAP Field Mappings**: All examples use actual field names (EAN11, ZBRDES, HERKL, etc.)
2. **Your Product Numbers**: Training uses 10001, 10002 (real products)
3. **Your Plant Codes**: Default plant 1000 in examples
4. **Your Business Logic**: Stock queries, delivery queries, product info patterns
5. **Your Bug Reports**: Context loss and action repeat patterns

**Example Training Data**:
```
User: What's the stock of product 10001?
Expected: {"intent": "stock_query", "product_numbers": ["10001"], "confidence": 0.92}

User: What's the UPC?
Context: Previously asked about 10001
Expected: {"intent": "product_info", "product_numbers": ["10001"], "field_requested": "upc", "from_context": true}

User: Do the same with 10002
Context: Last action was "get UPC for 10001"
Expected: {"intent": "product_info", "product_numbers": ["10002"], "field_requested": "upc", "action_repeat": true}
```

**Rebuilding the Model**:
```bash
# Windows (where Ollama is installed)
cd D:\opt\app\atp
ollama create atp-chatbot -f Modelfile

# Or from WSL
cd /opt/app/atp
/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe create atp-chatbot -f Modelfile
```

**Testing the Model**:
```bash
echo "What's the stock of product 10001?" | ollama run atp-chatbot
# Should return JSON with intent, entities, confidence
```

---

## Database Schema

### Users Table (`stockcheck_user`)
```sql
CREATE TABLE stockcheck_user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254),
    password VARCHAR(128),  -- Django hashed
    first_name VARCHAR(30),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined DATETIME,
    last_login DATETIME
);
```

### Plants Table (`stockcheck_plant`)
```sql
CREATE TABLE stockcheck_plant (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(4) NOT NULL,  -- e.g., "1000"
    name VARCHAR(100),          -- e.g., "Main Distribution Center"
    is_active BOOLEAN DEFAULT TRUE
);
```

### Search History (`stockcheck_searchhistory`)
```sql
CREATE TABLE stockcheck_searchhistory (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    product_number VARCHAR(50),
    plant_code VARCHAR(4),
    search_date DATETIME,
    result_count INT,
    FOREIGN KEY (user_id) REFERENCES stockcheck_user(id)
);
```

### Conversations Table (`chatbot_conversation`)
```sql
CREATE TABLE chatbot_conversation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    started_at DATETIME NOT NULL,
    last_activity DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    context JSON,  -- Stores conversation state
    FOREIGN KEY (user_id) REFERENCES stockcheck_user(id)
);
```

**Context JSON Structure**:
```json
{
  "products": ["10001", "10002"],
  "current_plant": "1000",
  "last_intent": "product_info",
  "last_field_requested": "upc",
  "last_action_description": "get UPC for product",
  "last_action_time": "2025-11-01T18:30:00Z"
}
```

### Messages Table (`chatbot_message`)
```sql
CREATE TABLE chatbot_message (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender VARCHAR(10),  -- 'user' or 'bot'
    content TEXT,
    timestamp DATETIME,
    intent VARCHAR(50),
    entities JSON,
    FOREIGN KEY (conversation_id) REFERENCES chatbot_conversation(id)
);
```

---

## API Endpoints

### Public Endpoints (No Authentication Required)
- `GET /atp/login/` - Login page
- `POST /atp/login/` - Process login

### Authenticated Endpoints (Login Required)
- `GET /` or `GET /atp/` - Home page
- `GET /atp/search/` - Product search form
- `POST /atp/search/` - Execute product search
- `GET /atp/results/` - Display search results
- `GET /atp/export/excel/` - Export results to Excel
- `GET /atp/export/csv/` - Export results to CSV
- `GET /atp/history/` - View search history
- `GET /atp/logout/` - Logout

### Chatbot Endpoints (AJAX/JSON)
- `GET /atp/chat/` - Chat interface page
- `POST /atp/chat/send/` - Send message to chatbot
  - **Request**: `{"message": "What's the stock of 10001?"}`
  - **Response**: `{"response": "📦 Stock Info...", "intent": "stock_query"}`

### Admin Endpoints (Superuser Only)
- `GET /atp/admin/` - Django admin panel
- `GET /atp/admin/stockcheck/user/` - Manage users
- `GET /atp/admin/chatbot/conversation/` - View conversations

---

## Deployment

### Production Deployment Checklist

#### 1. Security Configuration
```bash
# Change default passwords
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py changepassword admin

# Generate new SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Update docker-compose.yml environment:
DJANGO_SECRET_KEY=<generated-key>
DATABASE_PASSWORD=<strong-password>
MYSQL_ROOT_PASSWORD=<strong-password>
```

#### 2. SAP Configuration
Update SAP credentials in settings:
```python
# atp/atp/settings_secure.py
SAP_CONFIG = {
    'ashost': os.getenv('SAP_HOST', 'sap.company.com'),
    'sysnr': os.getenv('SAP_SYSTEM_NUMBER', '00'),
    'client': os.getenv('SAP_CLIENT', '100'),
    'user': os.getenv('SAP_USER', 'your-user'),
    'passwd': os.getenv('SAP_PASSWORD', 'your-password'),
}
```

#### 3. Build and Start
```bash
# Build fresh images
docker-compose -f docker-compose-port5000-secure.yml build --no-cache

# Start in detached mode
docker-compose -f docker-compose-port5000-secure.yml up -d

# Check logs
docker-compose -f docker-compose-port5000-secure.yml logs -f web
```

#### 4. Database Migrations
```bash
# Run migrations
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py collectstatic --noinput
```

#### 5. Create Superuser
```bash
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py createsuperuser
```

### Environment-Specific Configuration

#### Development
```bash
# Use docker-compose.yml (default)
docker-compose up -d

# Enable DEBUG mode
export DJANGO_DEBUG=True
```

#### Production
```bash
# Use secure configuration
docker-compose -f docker-compose-port5000-secure.yml up -d

# Ensure DEBUG is False (default in settings_secure.py)
export DJANGO_DEBUG=False
```

### Scaling Considerations

#### Increase Gunicorn Workers
Edit `Dockerfile` line 55:
```bash
# Change from 2 to N workers (recommended: 2 * CPU cores + 1)
gunicorn --bind 0.0.0.0:8000 --timeout 120 --workers 4 atp.wsgi:application
```

#### Database Connection Pooling
Add to `settings_secure.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}
```

---

## Maintenance Tasks

### Daily Tasks
1. **Monitor Logs**:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml logs --tail=100 -f
   ```

2. **Check Container Health**:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml ps
   docker stats atp_web atp_db atp_nginx
   ```

### Weekly Tasks
1. **Database Backup**:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml exec db mysqldump -uroot -p atp > backup_$(date +%Y%m%d).sql
   ```

2. **Clean Old Conversations** (optional):
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py shell
   >>> from chatbot.models import Conversation
   >>> from datetime import timedelta
   >>> from django.utils import timezone
   >>> cutoff = timezone.now() - timedelta(days=30)
   >>> Conversation.objects.filter(last_activity__lt=cutoff).delete()
   ```

3. **Review Search History**:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py shell
   >>> from stockcheck.models import SearchHistory
   >>> SearchHistory.objects.values('product_number').annotate(count=Count('id')).order_by('-count')[:10]
   ```

### Monthly Tasks
1. **Update Dependencies**:
   ```bash
   # Check for security updates
   docker-compose -f docker-compose-port5000-secure.yml exec web pip list --outdated

   # Update requirements.txt if needed
   # Rebuild containers
   docker-compose -f docker-compose-port5000-secure.yml build web
   ```

2. **Model Performance Review**:
   ```bash
   # Test model accuracy
   cd /opt/app/atp
   python test_chatbot_simple.py
   ```

3. **Database Optimization**:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml exec db mysql -uroot -p -e "OPTIMIZE TABLE atp.stockcheck_searchhistory, atp.chatbot_conversation, atp.chatbot_message;"
   ```

### Quarterly Tasks
1. **Retrain AI Model** (if needed):
   ```bash
   # Update generate_training_data.py with new patterns
   cd /opt/app/atp
   python generate_training_data.py

   # Rebuild model
   /mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe create atp-chatbot -f Modelfile

   # Restart application
   docker-compose -f docker-compose-port5000-secure.yml restart web
   ```

2. **Security Audit**:
   - Review user permissions
   - Rotate passwords
   - Check for Django security updates
   - Review nginx logs for suspicious activity

---

## Troubleshooting

### Common Issues

#### 1. Chat Responses Timing Out
**Symptoms**: "Sorry, I'm having trouble connecting to my AI assistant"

**Causes**:
- Ollama not running on Windows host
- Model not loaded
- Network connectivity issues
- Model too slow (12B instead of 4B)

**Solutions**:
```bash
# Check Ollama is running (on Windows)
ollama list  # Should show atp-chatbot

# Test model directly
echo "Test query" | ollama run atp-chatbot

# Check network from container
docker-compose -f docker-compose-port5000-secure.yml exec web curl http://192.168.1.101:11434/api/tags

# Increase timeout if needed (docker-compose.yml)
OLLAMA_TIMEOUT=120

# Verify correct model is loaded
docker-compose -f docker-compose-port5000-secure.yml logs web | grep "Ollama configured"
# Should show: Ollama configured: http://192.168.1.101:11434 using model atp-chatbot
```

#### 2. SAP Connection Failures
**Symptoms**: "Error connecting to SAP" or "RFC_ERROR_COMMUNICATION"

**Causes**:
- SAP credentials invalid
- SAP system down
- Network firewall blocking RFC port
- pyrfc library issue

**Solutions**:
```bash
# Test SAP connection
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py shell
>>> from stockcheck.sap_utils import get_sap_connection
>>> conn = get_sap_connection()
>>> conn.ping()  # Should return True

# Check SAP credentials (don't commit these!)
cat atp/atp/settings_secure.py | grep SAP_CONFIG

# Test RFC library
docker-compose -f docker-compose-port5000-secure.yml exec web python -c "import pyrfc; print(pyrfc.__version__)"
```

#### 3. Database Connection Errors
**Symptoms**: "Can't connect to MySQL server" or "Access denied"

**Solutions**:
```bash
# Check MySQL is running
docker-compose -f docker-compose-port5000-secure.yml ps db

# Check database logs
docker-compose -f docker-compose-port5000-secure.yml logs db

# Test connection from web container
docker-compose -f docker-compose-port5000-secure.yml exec web nc -zv db 3306

# Verify credentials match
docker-compose -f docker-compose-port5000-secure.yml exec web env | grep DATABASE
docker-compose -f docker-compose-port5000-secure.yml exec db env | grep MYSQL

# Reset database (WARNING: Data loss!)
docker-compose -f docker-compose-port5000-secure.yml down -v
docker-compose -f docker-compose-port5000-secure.yml up -d
```

#### 4. Context Loss in Conversations
**Symptoms**: Bot forgets previous products or actions

**Causes**:
- Conversation not being saved to database
- Context not passed to entity extractor
- Session timeout

**Solutions**:
```bash
# Check conversation is created
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py shell
>>> from chatbot.models import Conversation
>>> Conversation.objects.filter(is_active=True).count()  # Should be > 0

# Check context is being saved
>>> conv = Conversation.objects.filter(is_active=True).first()
>>> print(conv.context)  # Should show products, intents, etc.

# Enable debug logging
# Edit atp/chatbot/services/conversation_manager.py
# Add print statements to track_action() and get_context()
```

#### 5. Static Files Not Loading
**Symptoms**: CSS/JS not working, broken layout

**Solutions**:
```bash
# Collect static files
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py collectstatic --noinput

# Check nginx volume
docker-compose -f docker-compose-port5000-secure.yml exec nginx ls -la /static/

# Restart nginx
docker-compose -f docker-compose-port5000-secure.yml restart nginx
```

#### 6. Gunicorn Worker Timeout
**Symptoms**: 502 Bad Gateway, worker timeout in logs

**Solutions**:
```bash
# Increase timeout (already set to 120s in Dockerfile)
# If still timing out, edit Dockerfile line 55:
CMD bash -c "... gunicorn --bind 0.0.0.0:8000 --timeout 180 --workers 2 ..."

# Rebuild
docker-compose -f docker-compose-port5000-secure.yml build web
docker-compose -f docker-compose-port5000-secure.yml up -d
```

### Debug Mode

#### Enable Django Debug Mode (Development Only!)
```python
# atp/atp/settings_secure.py
DEBUG = True  # Change from False

# Restart
docker-compose -f docker-compose-port5000-secure.yml restart web
```

#### View Detailed Logs
```bash
# Web application logs
docker-compose -f docker-compose-port5000-secure.yml logs -f web

# Database logs
docker-compose -f docker-compose-port5000-secure.yml logs -f db

# Nginx access logs
docker-compose -f docker-compose-port5000-secure.yml logs -f nginx

# All logs
docker-compose -f docker-compose-port5000-secure.yml logs -f
```

#### Access Django Shell
```bash
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py shell

# Example: Test chatbot services
>>> from chatbot.services.ollama_client import OllamaClient
>>> client = OllamaClient()
>>> result = client.classify_intent("What's the stock of 10001?", [])
>>> print(result)
```

---

## Security Considerations

### Current Security Measures
1. **Input Validation**: All user inputs validated and sanitized
2. **SQL Injection Prevention**: Django ORM, parameterized queries
3. **XSS Protection**: Django's auto-escaping, security headers
4. **CSRF Protection**: CSRF tokens on all POST requests
5. **Clickjacking Protection**: X-Frame-Options header
6. **Session Security**: HTTP-only cookies, 1-hour timeout
7. **Password Hashing**: Django's PBKDF2 algorithm

### Security Best Practices

#### Change Default Credentials
```bash
# Database
docker-compose -f docker-compose-port5000-secure.yml exec db mysql -uroot -p
ALTER USER 'djangoadmin'@'%' IDENTIFIED BY 'new-strong-password';
FLUSH PRIVILEGES;

# Django admin
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py changepassword admin
```

#### Generate New SECRET_KEY
```python
# Run this command:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Update settings_secure.py or environment:
SECRET_KEY = '<generated-key>'
```

#### Enable HTTPS (Production)
```nginx
# nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

#### Restrict Database Access
```yaml
# docker-compose.yml - Remove external port
db:
  # Comment out:
  # ports:
  #   - "3306:3306"
```

#### Regular Updates
```bash
# Update base image
docker pull ubuntu:18.04

# Rebuild containers
docker-compose -f docker-compose-port5000-secure.yml build --no-cache

# Update Python packages
docker-compose -f docker-compose-port5000-secure.yml exec web pip install --upgrade pip
```

### Audit Logging
Enable request logging in `settings_secure.py`:
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/gunicorn/django.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

---

## For PHP Developers

If you're coming from a PHP background, here are some Django equivalents:

| PHP Concept | Django Equivalent | Location |
|-------------|-------------------|----------|
| `index.php` | `urls.py` | `atp/atp/urls.py` |
| `include()` | `{% include %}` | Templates |
| `$_GET`, `$_POST` | `request.GET`, `request.POST` | Views |
| `mysqli_query()` | `Model.objects.filter()` | `models.py` |
| `header('Location:')` | `redirect()` | Views |
| `session_start()` | Automatic | Django sessions |
| `.htaccess` | `urls.py` patterns | URL routing |
| Composer | `pip` | `requirements.txt` |
| `var_dump()` | `print()` or `pdb` | Debugging |

**Key Differences**:
- Django uses **MVT** (Model-View-Template) instead of MVC
- **ORM** instead of raw SQL (but you can use raw SQL if needed)
- **Migration system** for database changes
- **WSGI** application server instead of mod_php
- **Virtual environments** instead of global PHP installation

---

## For Python Developers New to Django

### Project Structure
```
atp/
├── atp/              # Project configuration
│   ├── settings_secure.py   # Main settings
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI config
├── stockcheck/       # Traditional app
│   ├── models.py            # Database models
│   ├── views.py             # Request handlers
│   ├── forms.py             # Form validation
│   └── templates/           # HTML templates
├── chatbot/          # AI chatbot app
│   ├── models.py
│   ├── views.py
│   ├── services/            # Business logic
│   └── templates/
└── manage.py         # Django CLI

```

### Django Commands
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Open Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Common Patterns

**Query Database**:
```python
from stockcheck.models import User, SearchHistory

# Get all users
users = User.objects.all()

# Filter
active_users = User.objects.filter(is_active=True)

# Get single object
user = User.objects.get(username='admin')

# Create
history = SearchHistory.objects.create(
    user=user,
    product_number='10001',
    result_count=5
)
```

**Handle Requests**:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def my_view(request):
    if request.method == 'POST':
        # Handle form submission
        product = request.POST.get('product_number')
        # Process...
        return redirect('results')
    else:
        # Show form
        return render(request, 'mytemplate.html', context={})
```

---

## Quick Reference

### Restart Application
```bash
docker-compose -f docker-compose-port5000-secure.yml restart
```

### View Logs
```bash
docker-compose -f docker-compose-port5000-secure.yml logs -f web
```

### Access Database
```bash
docker-compose -f docker-compose-port5000-secure.yml exec db mysql -uroot -p atp
```

### Rebuild AI Model
```bash
cd /opt/app/atp
/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe create atp-chatbot -f Modelfile
```

### Run Tests
```bash
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test
```

### Emergency Rollback
```bash
# Stop current version
docker-compose -f docker-compose-port5000-secure.yml down

# Start previous version
git checkout <previous-commit>
docker-compose -f docker-compose-port5000-secure.yml up -d
```

---

## Support Contacts

**Repository**: https://github.com/yourcompany/atp-application
**Documentation**: `/opt/app/docs/`
**Backup Location**: `/backups/atp/`

---

**Last Updated**: November 1, 2025
**Version**: 1.0
**Changelog**: See `CHANGELOG.md`
