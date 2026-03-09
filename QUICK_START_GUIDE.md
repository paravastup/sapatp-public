# ATP Application - Quick Start Guide

## What is ATP?

**ATP** (Available-to-Promise) is a Django-based web application that provides real-time product availability checking by integrating with SAP ERP systems. Users can search for product stock levels across multiple manufacturing plants and export results to Excel or email.

**Key Purpose:** Enable sales and supply chain teams to instantly check product availability without direct SAP access.

---

## Key Application Features

### 1. Product Availability Search
- Search by Arc SKU or Vendor SKU
- Support for multiple products (up to 100 per search)
- Multi-plant selection
- Real-time data from SAP

### 2. Stock Information Display
- Available stock (STOCK)
- Stock including orders (ACTUAL)
- Next delivery date and quantity
- Material type (Stock item, On demand, No planning)
- Origin, brand, vendor SKU, UPC/EAN

### 3. Data Export & Delivery
- Excel XLS file download (15 columns)
- Email delivery to user
- Formatted header with product details

### 4. User Management
- Self-service registration
- Admin approval workflow
- Plant-based access control
- User profiles (company, role, business entity)

### 5. Audit & Tracking
- Search history tracking
- Login/logout audit trail
- Admin interface for management

---

## Technology Stack Overview

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Django | 2.1.5 |
| Language | Python | 3.6 |
| Database | MySQL | 5.7 |
| Web Server | Gunicorn | 19.9.0 |
| Reverse Proxy | Nginx | 1.19 |
| Container | Docker | Latest |
| SAP Integration | pyrfc | 1.9.93 |
| Frontend | Bootstrap | 4.1.3 |

---

## Project Structure at a Glance

```
/opt/app/
├── atp/                          # Django project
│   ├── stockcheck/               # Product search app (MAIN)
│   │   ├── models.py            # Database models
│   │   ├── views.py             # Search logic (450 lines)
│   │   ├── forms.py             # Search form
│   │   └── templates/stockcheck/ # HTML templates
│   │
│   ├── docs/                     # Documentation app
│   │   ├── models.py            # Doc model
│   │   └── views.py             # CRUD views
│   │
│   ├── atp/settings.py          # Main configuration
│   ├── atp/urls.py              # URL routing
│   ├── atp/settings.ini         # SAP connection config
│   └── templates/               # Global templates
│
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Services orchestration
├── nginx.conf                    # Reverse proxy config
├── requirements.txt              # Python dependencies
└── test_sap_connection.py        # SAP test script
```

---

## Core Django Apps

### stockcheck (Main Application)
**Purpose:** Product search and availability checking

**Models:**
- `SearchHistory` - Track user searches
- `Plant` - Manufacturing facilities
- `Profile` - Extended user profile
- `AuditEntry` - Login/logout audit
- `Pattern`, `Universe` - Product classifications
- `HelpGuide` - Help documentation

**Views:**
- `SearchView` - Main search interface
- `download_data()` - Excel export/email
- `signup()` - User registration
- Various template views (About, Help, Home, etc.)

### docs (Documentation)
**Purpose:** Help documentation management

**Models:**
- `Doc` - Documentation articles

**Views:**
- CRUD views for docs
- Publish/draft workflow

---

## Database Models Overview

### Key Relationships

```
User (Django built-in)
  ├── Profile (1:1)
  ├── Plant (M:M) - determines search access
  ├── SearchHistory (1:M) - tracks searches
  └── AuditEntry (1:M) - tracks login/logout

Plant
  ├── code (e.g., "1000")
  ├── description (e.g., "Durand Glass")
  └── users (M:M)

SearchHistory
  ├── username (FK to User)
  ├── time (date)
  └── referencekey (search terms)

AuditEntry
  ├── user (FK to User)
  ├── session_key
  ├── host, ip
  ├── login_time
  └── logout_time

Profile
  ├── user (1:1 FK to User)
  ├── company
  ├── role
  ├── website
  └── business (AINA or Brand_D)
```

---

## SAP Integration

### RFC Functions Used

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| **Z_GET_MATERIAL_DETAILS** | Main stock lookup | Plant, Product, Mode | Stock data |
| **Z_PATTERN_PRODUCTS** | Get products by classification | Pattern/Universe | List of products |
| **BAPI_MATERIAL_GET_ALL** | Material master data | Plant, Material | Detailed product info |
| **RFC_SYSTEM_INFO** | Connection test | - | SAP version |
| **STFC_CONNECTION** | Echo test | Test text | Echo response |

### Connection Configuration

**File:** `atp/atp/settings.ini`
```ini
[connection]
ashost=DummyPass123!      # SAP host
sysnr=02               # System number
client=900             # Client/tenant
user=DummyPass123!            # RFC user
passwd=DummyPass123!     # Password
lang=EN                # Language
```

### Logging

All SAP interactions logged to `/var/log/gunicorn/sap_interactions.log`

Example log entries:
```
SAP Call - Z_GET_MATERIAL_DETAILS - Input: plant=1000, product=123456, mode=M
SAP Response - Z_GET_MATERIAL_DETAILS - Success - Product: 123456
Search initiated - User: john.doe, Plant: 1000, Type: Arc
```

---

## API Endpoints (URL Routes)

### Public (No Login)
```
GET  /                    → Landing page
GET  /atp/about/          → About page
GET  /atp/help/           → Help documentation
GET  /atp/login/          → Login form
POST /atp/login/          → Login submission
GET  /atp/signup/         → Registration form
POST /atp/signup/         → Registration submission
```

### Protected (Login Required)
```
GET  /atp/search/         → Search form
POST /atp/search/         → Search submission
GET  /atp/data_download/  → Download/Email results
POST /atp/data_download/  → Process export
GET  /atp/home/           → Dashboard
GET  /atp/feedback/       → Feedback form
GET  /atp/change-password/ → Change password
```

### Admin
```
GET  /atp/admin/          → Django admin interface
```

### Documentation
```
GET  /atp/help/docs/      → List docs
GET  /atp/help/docs/<id>/ → View doc
```

---

## Deployment & Running

### Using Docker Compose

**Start Application:**
```bash
cd /opt/app
docker-compose up -d
```

**Stop Application:**
```bash
docker-compose down
```

**View Logs:**
```bash
docker-compose logs -f web      # Django/Gunicorn logs
docker-compose logs -f db       # MySQL logs
docker-compose logs -f nginx    # Nginx logs
```

**Access Application:**
- Frontend: http://localhost
- Django Admin: http://localhost/atp/admin/
- Database: localhost:3306

### Database Credentials

```
Database: atp
User: djangoadmin
Password: DummyPass123!
Host: db (Docker) or localhost (direct)
Port: 3306
```

### Default Admin Account

Create using:
```bash
docker-compose exec web python manage.py createsuperuser
```

---

## User Access Flow

1. **User Registration**
   - Fill signup form (username, email, password, name)
   - Fill profile form (company, role, business entity)
   - Email sent to admin for approval

2. **Admin Approval**
   - Admin views pending users in Django admin
   - Admin assigns plants to user
   - Admin activates user (set is_active=True)

3. **User Login**
   - User logs in with username/password
   - Session created, login time recorded

4. **Product Search**
   - User selects plant from assigned plants
   - User selects search type (Arc/Vendor SKU)
   - User enters product numbers
   - Results displayed with stock info

5. **Export Results**
   - User downloads Excel file or emails to self
   - File contains 15 columns of product data

6. **Logout**
   - User clicks logout
   - Session ends, logout time recorded

---

## Configuration Files

### Django Settings
**File:** `atp/atp/settings.py`

Key settings:
- `DEBUG = True` (WARNING: False in production)
- `INSTALLED_APPS` - Registered apps
- `DATABASES` - MySQL connection
- `EMAIL_` - Gmail SMTP config
- `LOGGING` - Log configuration

### SAP Connection
**File:** `atp/atp/settings.ini`

SAP connection parameters (host, client, user, etc.)

### Docker Services
**File:** `docker-compose.yml`

- **web:** Django app on port 8000
- **db:** MySQL 5.7 on port 3306
- **nginx:** Reverse proxy on port 80

### Nginx Config
**File:** `nginx.conf`

Reverse proxy rules and static file serving

---

## Common Tasks

### Run Django Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic
```

### Test SAP Connection
```bash
docker-compose exec web python test_sap_connection.py
```

### View Application Logs
```bash
# SAP interactions log
docker-compose exec web tail -f /var/log/gunicorn/sap_interactions.log

# Container logs
docker-compose logs -f web
```

### Access Database
```bash
docker-compose exec db mysql -u djangoadmin -pDummyPass123! atp
```

---

## Security Notes

### Current Issues
1. **Hardcoded secrets** in settings files (should use env vars)
2. **DEBUG = True** (exposes sensitive info)
3. **No HTTPS** configured
4. **Credentials in source** (SAP, database, email)

### Recommendations
1. Move secrets to `.env` file
2. Set DEBUG = False in production
3. Configure HTTPS/SSL
4. Use environment variables for all credentials
5. Implement rate limiting
6. Add input validation for SAP calls

---

## Key Business Logic

### SearchView Flow
1. User submits: plant + search_type + product_numbers
2. Split products by comma/space
3. Chunk into groups of 100
4. For each product:
   - Call SAP RFC Z_GET_MATERIAL_DETAILS
   - Get: stock, vendor SKU, description, brand, origin, etc.
5. Format data:
   - Convert dates from YYYYMMDD to MM/DD/YYYY
   - Map DISMM codes to descriptions
   - Convert ACTUAL to float
6. Store in session
7. Save SearchHistory record
8. Render details.html with results

### Download Data Flow
1. Get data from session
2. Create XLS workbook with xlwt
3. Add header row (bold)
4. Add data rows (15 columns)
5. Option A: Download - return as HTTP attachment
6. Option B: Email - send via SMTP to user's email

---

## File Organization Summary

**Configuration:**
- `atp/atp/settings.py` - Django settings
- `atp/atp/urls.py` - URL routes
- `atp/atp/settings.ini` - SAP connection
- `atp/atp/wsgi.py` - WSGI entry point

**Application Code:**
- `atp/stockcheck/models.py` - Data models
- `atp/stockcheck/views.py` - Business logic (450 lines)
- `atp/stockcheck/forms.py` - Form definitions
- `atp/stockcheck/admin.py` - Admin customization
- `atp/docs/models.py` - Doc model
- `atp/docs/views.py` - Doc CRUD views

**Frontend:**
- `atp/templates/stockcheck/*.html` - Product templates
- `atp/templates/registration/*.html` - Auth templates
- `atp/templates/docs/*.html` - Doc templates
- `atp/static/` - CSS, JS, images

**Infrastructure:**
- `Dockerfile` - Container image
- `docker-compose.yml` - Service orchestration
- `nginx.conf` - Reverse proxy
- `requirements.txt` - Python dependencies

---

## Typical Use Case Scenario

1. **Sales Manager** logs in to ATP application
2. **Selects Plant**: "ACME Corp (1000)"
3. **Selects Search Type**: "Arc SKU"
4. **Enters Products**: "001234, 001235, 001236"
5. **Clicks Search**
   - System fetches data from SAP
   - Displays 3 products with stock info
6. **Reviews Results**
   - Product A: 1500 in stock, available
   - Product B: 0 in stock, on demand
   - Product C: 2000 in stock, available
7. **Exports Results**
   - Downloads Excel with full product details
   - Or emails to self
8. **Uses Data**
   - Provides availability info to customer
   - Makes sales decision based on stock

---

## Troubleshooting

### Application won't start
1. Check Docker is running: `docker ps`
2. Check logs: `docker-compose logs web`
3. Check MySQL is ready: `docker-compose logs db`
4. Check ports are available: `lsof -i :80 :3306 :8000`

### SAP connection failing
1. Test connection: `docker-compose exec web python test_sap_connection.py`
2. Check settings.ini has correct credentials
3. Check SAP host is reachable
4. Check RFC user/password
5. Check SAP RFC SDK is installed

### Database issues
1. Check MySQL is running: `docker-compose ps`
2. Check credentials in settings.py
3. Run migrations: `docker-compose exec web python manage.py migrate`
4. Check logs: `docker-compose logs db`

### Static files not loading
1. Collect static files: `docker-compose exec web python manage.py collectstatic`
2. Check nginx config: `cat nginx.conf`
3. Check file permissions: `docker-compose exec web ls -la /app/static/`

---

## Performance Considerations

### Current Limitations
- No pagination on result lists (could have 100+ rows)
- No caching of SAP results
- No async task processing (email is blocking)
- No query optimization

### Recommendations
1. Add pagination (limit results to 20-50 per page)
2. Cache results for 5-10 minutes
3. Use Celery for async email delivery
4. Add database indexes on frequently queried fields
5. Use select_related/prefetch_related for queries

---

## Next Steps for Enhancement

1. **Security:** Move secrets to .env, enable HTTPS
2. **Performance:** Add caching, pagination, async tasks
3. **Testing:** Add unit tests, integration tests
4. **Monitoring:** Add health checks, metrics, alerting
5. **Upgrade:** Update Django, Python, dependencies
6. **Documentation:** Add API docs, user guide, admin guide
7. **Features:** Add filters, saved searches, reports
8. **Accessibility:** Improve mobile experience, WCAG compliance

---

## Support Contacts

**Application Admin:** DummyPass123! (configured email)
**SAP Connection:** Check settings.ini for SAP system details
**Database:** MySQL 5.7, user: djangoadmin

---

## Document Information

**Created:** 2025-10-31
**Application Location:** /opt/app/
**Project Type:** Django Web Application
**Deployment:** Docker + Docker Compose
**Production Ready:** Yes (with security hardening needed)

