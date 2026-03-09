# ATP SAP Middleware Application - Comprehensive Codebase Overview

## Executive Summary

The ATP (Available-to-Promise) application is a Django-based web application that provides real-time product availability information by integrating with SAP ERP systems. It allows authorized users to search for product stock availability across multiple manufacturing plants, with results exported to Excel files or emailed directly.

**Technology Stack:**
- Backend: Django 2.1.5 with Python 3.6
- Database: MySQL 5.7
- SAP Integration: pyrfc 1.9.93 (SAP NetWeaver RFC SDK)
- Frontend: Bootstrap 4, DataTables, jQuery
- Deployment: Docker + Docker Compose + Nginx
- Web Server: Gunicorn

---

## 1. PROJECT STRUCTURE & FILE ORGANIZATION

```
/mnt/d/demoproject/
├── README.md                          # Project documentation
├── DEPLOY.md                          # Deployment guide
├── Dockerfile                         # Container image definition
├── docker-compose.yml                 # Multi-container orchestration
├── requirements.txt                   # Python dependencies
├── nginx.conf                         # Nginx reverse proxy configuration
├── test_sap_connection.py            # SAP connectivity test script
├── add_plants.py                      # Utility to add plant data
├── pyrfc.whl                          # SAP RFC Python wheel
├── nwrfcsdk/                         # SAP NetWeaver RFC SDK libraries
│   └── lib/                           # RFC connection libraries
├── atp/                              # Django project root
│   ├── manage.py                     # Django management script
│   ├── db.sqlite3                    # SQLite database (dev)
│   ├── Users.csv                     # User data export
│   ├── atp/                          # Django configuration package
│   │   ├── __init__.py
│   │   ├── settings.py               # Main Django settings
│   │   ├── settings.ini              # SAP connection config
│   │   ├── urls.py                   # URL routing (main)
│   │   └── wsgi.py                   # WSGI application entry
│   ├── stockcheck/                   # Main Django app (product search)
│   │   ├── models.py                 # Database models
│   │   ├── views.py                  # View logic (450 lines)
│   │   ├── forms.py                  # Form definitions
│   │   ├── admin.py                  # Admin interface config
│   │   ├── apps.py
│   │   ├── tests.py
│   │   ├── migrations/               # Database migrations
│   │   ├── management/commands/      # CLI commands
│   │   │   ├── find_duplicate_emails.py
│   │   │   └── resolve_duplicate_emails.py
│   │   ├── static/                   # Static assets
│   │   │   ├── css/
│   │   │   └── js/
│   │   └── templates/stockcheck/     # HTML templates
│   │       ├── base.html
│   │       ├── index.html
│   │       ├── search.html
│   │       ├── details.html
│   │       ├── about.html
│   │       ├── help.html
│   │       └── home.html
│   ├── docs/                         # Documentation app
│   │   ├── models.py                 # Doc model
│   │   ├── views.py                  # Doc views (CRUD)
│   │   ├── forms.py
│   │   ├── admin.py
│   │   ├── migrations/
│   │   ├── static/docs/              # Doc styling
│   │   └── templates/docs/           # Doc templates
│   │       ├── doc_list.html
│   │       ├── doc_detail.html
│   │       ├── doc_form.html
│   │       └── doc_confirm_delete.html
│   ├── middleware/                   # Custom middleware
│   │   └── audit_middleware.py       # User login/logout audit
│   ├── templates/                    # Global templates
│   │   ├── registration/             # Auth templates
│   │   │   ├── login.html
│   │   │   ├── signup.html
│   │   │   ├── password_reset_form.html
│   │   │   ├── password_reset_done.html
│   │   │   ├── password_reset_confirm.html
│   │   │   ├── password_change.html
│   │   │   ├── feedback.html
│   │   │   └── thanks.html
│   │   ├── stockcheck/               # Product templates
│   │   └── docs/                     # Doc templates
│   ├── static/                       # Compiled static files
│   │   ├── admin/                    # Django admin assets
│   │   ├── css/
│   │   ├── js/
│   │   └── rest_framework/           # DRF assets
│   ├── find_duplicate_emails.py      # Email deduplication utility
│   ├── Dockerfile                    # App-specific Dockerfile
│   └── dev_rfc.trc                   # RFC debug trace file
└── atpvenv/                          # Python virtual environment (3.6)
```

**Key Statistics:**
- ~25 HTML templates
- ~40 Python modules
- ~2,400 compiled Python cache files
- ~15 CSS/JS libraries (Bootstrap, DataTables, jQuery, etc.)

---

## 2. DJANGO APPLICATION ARCHITECTURE

### 2.1 Applications (Apps)

#### A. **stockcheck** - Core Product Search Application
Primary application providing product availability search functionality.

**Models:**
```python
SearchHistory         # Track user searches (username, time, referencekey)
HelpGuide            # Help documentation items
Plant                # Manufacturing facilities (code, description, users M2M)
Pattern              # Pattern classifications
Universe             # Universe classifications
Profile              # Extended user profile (company, role, website, business)
AuditEntry           # User login/logout audit trail
```

**Key Features:**
- Product search by Demo SKU or Vendor SKU
- Multi-plant selection
- Supports up to 100 products per search (chunked processing)
- Real-time SAP data fetching
- Excel export with formatted columns
- Email delivery of results

#### B. **docs** - Documentation Management Application
Simple CMS for help documentation.

**Models:**
```python
Doc                  # Documentation articles (title, text, author, dates)
```

**Features:**
- Create/update/delete documentation
- Publish/draft workflow
- Author tracking
- Chronological ordering

### 2.2 Settings Configuration

**File:** `/mnt/d/demoproject/atp/atp/settings.py`

**Key Settings:**
```python
BASE_DIR = /mnt/d/demoproject/atp
TEMPLATE_DIR = /mnt/d/demoproject/atp/templates
SECRET_KEY = '[REDACTED]'
DEBUG = True
ALLOWED_HOSTS = ['[REDACTED]', '[REDACTED]', '[REDACTED]',
                 '[REDACTED]', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'stockcheck',
    'django.contrib.admin',
    'docs',
    'rest_framework',
    'rest_framework_jwt'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'atp',
        'USER': 'dbuser',
        'PASSWORD': '[REDACTED]',
        'HOST': 'db',
        'PORT': '3306'
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"
TIME_ZONE = 'EST'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = '[REDACTED]'
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = '[REDACTED]'

# Logging
LOG_DIR = '/var/log/gunicorn'
# Logs to sap_interactions.log
```

**SAP Connection Config File:** `/mnt/d/demoproject/atp/atp/settings.ini`
```ini
[connection]
ashost=[REDACTED]
sysnr=02
client=900
user=[REDACTED]
passwd=[REDACTED]
lang=EN
```

### 2.3 URL Routing

**Main URL Config:** `/mnt/d/demoproject/atp/atp/urls.py`

```python
# Authentication paths
/atp/login/                      -> Django LoginView
/atp/logout/                     -> Django LogoutView
/atp/signup/                     -> Custom signup view
/atp/password_reset/             -> Django password reset
/atp/reset/<uidb64>/<token>/     -> Password reset confirm

# Main application paths
/                                -> IndexView (index.html)
/atp/home/                       -> HomeView (home.html)
/atp/about/                      -> AboutView (about.html)
/atp/search/                     -> SearchView (product search form)
/atp/data_download/              -> download_data (Excel export)
/atp/feedback/                   -> FeedbackView (feedback form)
/thanks/                         -> ThankView (success page)

# Documentation paths
/atp/help/                       -> Included from docs.urls
  /docs/                         -> DocListView
  /docs/<pk>/                    -> DocDetailView
  /docs/<pk>/edit/               -> DocUpdateView
  /docs/<pk>/remove/             -> DocDeleteView
  /docs/<pk>/publish/            -> doc_publish action

# Admin paths
/atp/admin/                      -> Django admin interface
/atp/admin/doc/                  -> Admin docs
```

---

## 3. SAP INTEGRATION COMPONENTS

### 3.1 SAP RFC Connection

The application uses **pyrfc** library (version 1.9.93) to communicate with SAP systems via Remote Function Calls (RFC).

**SAP RFC Functions Called:**

1. **Z_PATTERN_PRODUCTS** - Get product list by pattern or universe
   - Input: PATTERN or UNIVERSE code
   - Output: ET_MAT_DETAILS (array of material details)
   - Used: For product listing by classification

2. **Z_GET_MATERIAL_DETAILS** - Get detailed product information
   - Inputs:
     - IV_WERKS: Plant code (e.g., "1001")
     - IV_MATNR: Material/Product number
     - IV_MODE: Mode ("M" for Demo SKU, "O" for Vendor SKU)
   - Output: ES_OUTPUT (product details object)
   - Returns: Stock levels, vendor SKU, description, origin, etc.

3. **BAPI_MATERIAL_GET_ALL** - Get material master data from SAP
   - Inputs: PLANT, MATERIAL
   - Returns: PLANTDATA, CLIENTDATA, FORECASTPARAMETERS
   - Used: Additional product details (OLD_MAT_NO, FORE_MODEL)

4. **RFC_SYSTEM_INFO** - Test SAP connection
   - Returns: SAP system version information
   - Used: Connection testing

5. **STFC_CONNECTION** - Simple connection test
   - Input: REQUTEXT (echo text)
   - Output: ECHOTEXT
   - Used: Basic connectivity verification

### 3.2 Key SAP Functions in Code

**File:** `/mnt/d/demoproject/atp/stockcheck/views.py`

```python
# Function: product_details(reftype, value)
# Calls Z_PATTERN_PRODUCTS RFC
# Returns: Array of product material numbers

# Function: stock_info(plant, product, mode)
# Calls Z_GET_MATERIAL_DETAILS RFC
# Returns: JSON with stock information
# Fields: MATNR, BISMT, MAKTX, ZBRDES, HERKL, STOCK, ACTUAL, EEIND, etc.

# Function: product_info(plant, product)
# Calls BAPI_MATERIAL_GET_ALL RFC
# Returns: Plant-specific product data with forecasting info
```

### 3.3 Connection Parameters

Configuration read from:
1. `atp/atp/settings.ini` file (primary)
2. Environment variables (fallback)

**Environment Variables:**
- SAP_HOST
- SAP_SYSNR
- SAP_CLIENT
- SAP_USER
- SAP_PASSWORD

### 3.4 SAP Test Script

**File:** `/mnt/d/demoproject/test_sap_connection.py`

Tests SAP connectivity by:
1. Reading connection parameters from settings.ini or env vars
2. Attempting connection with pyrfc.Connection
3. Calling RFC_SYSTEM_INFO
4. Calling STFC_CONNECTION
5. Reporting success/failure

---

## 4. API ENDPOINTS & FUNCTIONALITY

### 4.1 Public Views (No Login Required)

| URL | View | Purpose | Template |
|-----|------|---------|----------|
| `/` | IndexView | Landing page | index.html |
| `/atp/about/` | AboutView | About page | about.html |
| `/atp/help/` | DocListView | Help documentation | doc_list.html |
| `/atp/login/` | LoginView | User authentication | login.html |
| `/atp/signup/` | signup() | User registration | signup.html |
| `/thanks/` | ThankView | Signup success | thanks.html |

### 4.2 Protected Views (Login Required)

| URL | View | Purpose | Key Features |
|-----|------|---------|--------------|
| `/atp/home/` | HomeView | Dashboard | - |
| `/atp/search/` | SearchView | Product search | Form with plant/product inputs, SAP calls |
| `/atp/data_download/` | download_data() | Export results | Excel XLS generation, email delivery |
| `/atp/feedback/` | FeedbackView | User feedback | Contact form |
| `/atp/change-password/` | PasswordChangeView | Change password | Django auth |
| `/atp/password_reset/` | PasswordResetView | Reset password | Email-based reset flow |

### 4.3 Admin Views

| URL | Purpose |
|-----|---------|
| `/atp/admin/` | Django admin interface |
| `/atp/admin/` User mgmt | Create/edit users, activate/deactivate |
| `/atp/admin/` Plant mgmt | Assign plants to users |
| `/atp/admin/` Search history | View user search history |
| `/atp/admin/` Audit logs | User login/logout tracking |

---

## 5. DATABASE SCHEMA & MODELS

### 5.1 Core Models (stockcheck app)

```python
class Plant(models.Model):
    code = CharField(max_length=15)              # e.g., "1001"
    description = CharField(max_length=30)      # e.g., "Plant A"
    users = ManyToManyField(User)                # Plant-to-User relationship

class Pattern(models.Model):
    code = CharField(max_length=15)
    description = CharField(max_length=30)

class Universe(models.Model):
    code = CharField(max_length=15)
    description = CharField(max_length=30)

class Profile(models.Model):  # Extended User profile
    user = OneToOneField(User, primary_key=True)
    company = CharField(max_length=30, blank=True)
    role = CharField(max_length=30, blank=True)
    website = URLField(max_length=50, blank=True)
    business = CharField(max_length=10, blank=True)  # BU_A or Brand_Delta

class SearchHistory(models.Model):
    username = ForeignKey(User)
    time = DateField(auto_now_add=True)
    referencekey = CharField(max_length=5000)   # Search terms
    __str__: "{username} - {time} - {referencekey}"

class AuditEntry(models.Model):
    user = ForeignKey(User)
    session_key = CharField(max_length=100)
    host = CharField(max_length=100)            # HTTP_HOST
    login_time = DateTimeField(null=True)
    logout_time = DateTimeField(null=True)
    ip = GenericIPAddressField(null=True)
    __str__: "{user} - {login_time} - {logout_time} - {ip}"

class HelpGuide(models.Model):
    username = ForeignKey(User)
    time = DateField(auto_now_add=True)
    title = CharField(max_length=150)
    description = CharField(max_length=150)
```

### 5.2 Documentation Model

```python
class Doc(models.Model):  # docs app
    author = ForeignKey(User, blank=True)
    title = CharField(max_length=200)
    text = TextField()
    created_date = DateTimeField(default=timezone.now)
    published_date = DateTimeField(blank=True, null=True)
    
    def publish(self):
        self.published_date = timezone.now()
        self.save()
```

### 5.3 Signal Handlers

**User Post-Save Signal** (Auto-create Profile):
```python
@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
```

**User Pre-Save Signal** (Account Activation Email):
```python
@receiver(pre_save, sender=User)
def active(sender, instance, **kwargs):
    if instance.is_active and get_user_model().objects.filter(
        pk=instance.pk, is_active=False).exists():
        # Send account activation email via EmailMultiAlternatives
```

**Login/Logout Signals** (Audit Tracking):
```python
@receiver(user_logged_in)
def log_user_logged_in(sender, user, request, **kwargs):
    # Create AuditEntry with login_time

@receiver(user_logged_out)
def log_user_logged_out(sender, user, request, **kwargs):
    # Update AuditEntry with logout_time
```

---

## 6. FORMS & INPUT VALIDATION

### 6.1 ProductForm

```python
class ProductForm(forms.Form):
    attr_type = ChoiceField(
        choices=[
            ('Arc', 'Demo SKU'),
            ('Old', 'Vendor SKU')
        ],
        widget=Select(attrs={'class': 'form-control'})
    )
    
    plant_option = ModelChoiceField(
        queryset=Plant.objects.filter(users__username=current_user),
        empty_label='Select a plant',
        widget=Select(attrs={'class': 'form-control'})
    )
    
    product_number = CharField(
        widget=Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter product numbers separated by commas'
        })
    )
```

**Processing:**
- Accepts comma or space-separated product numbers
- Chunks into batches of 100 for processing
- Supports two search modes: Demo SKU (mode='M') or Vendor SKU (mode='O')

### 6.2 SignUpForm

```python
class SignUpForm(UserCreationForm):
    first_name = CharField(max_length=30, required=True)
    last_name = CharField(max_length=30, required=True)
    email = EmailField(max_length=254, required=True)
    password1 = CharField(widget=PasswordInput)
    password2 = CharField(widget=PasswordInput)
    username = CharField(max_length=30, required=True)
```

### 6.3 ProfileForm

```python
class ProfileForm(forms.ModelForm):
    BUSINESS_CHOICES = (
        (' ', 'Select the business entity...'),
        ('BU_A', 'Business Unit A'),
        ('Brand_Delta', 'Brand_Delta International')
    )
    
    company = CharField(max_length=30, required=True)
    role = CharField(max_length=75, required=True)
    website = URLField(max_length=75, required=False)
    business = ChoiceField(choices=BUSINESS_CHOICES, required=True)
```

---

## 7. VIEWS & BUSINESS LOGIC

### 7.1 SearchView (Main Feature)

**Class:** `SearchView(LoginRequiredMixin, FormView)`
**Template:** `stockcheck/search.html`

**Flow:**
1. User selects plant and search type (Arc/Vendor SKU)
2. Submits product numbers (comma or space-separated)
3. Form chunks products into groups of 100
4. For each product, calls `stock_info(plant, product, mode)`
5. Transforms SAP data:
   - Converts ACTUAL to float
   - Formats EEIND date from YYYYMMDD to MM/DD/YYYY
   - Maps DISMM codes to descriptions (Stock item, On demand, No planning)
6. Stores results in session: `request.session['data'] = data_list`
7. Logs search history to database
8. Renders `details.html` with results

**Output Data Structure:**
```python
{
    'MATNR': '123456',                          # Product number
    'BISMT': 'OLD-SKU-001',                    # Vendor SKU
    'MAKTX': 'Product Description',             # Text
    'ZBRDES': 'Brand Name',                    # Brand
    'HERKL': 'Country of Origin',              # Origin
    'STOCK': 1500,                              # Available stock
    'ACTUAL': 2000.0,                          # Including orders
    'EEIND': '12/15/2024',                     # Next delivery date
    'MNG01': 500,                              # Next delivery qty
    'ZMENG': 300,                              # In transit
    'ZKWMENG': 200,                            # Supplier open qty
    'DISMM': 'Stock item',                     # Type
    'UMREZ': 12,                               # Case pack
    'EAN11': '5901234567890',                 # UPC/EAN
    'BRGEW': 2.5                               # Case weight
}
```

### 7.2 download_data() - Excel Export

**Location:** `stockcheck/views.py`
**Requires:** Login, session data

**Features:**
- Generates XLS file using xlwt library
- Creates formatted header row (bold)
- Exports 15 columns of product data
- Two delivery options:
  1. Direct download (response attachment)
  2. Email delivery via SMTP

**Email Delivery:**
- Uses EmailMultiAlternatives
- Subject includes username and timestamp
- Attachment: XLS file with email-safe MIME type
- From: [REDACTED]

### 7.3 signup() - User Registration

**Location:** `stockcheck/views.py`

**Flow:**
1. Display SignUpForm + ProfileForm
2. Validate both forms
3. Create user (initially is_active=False)
4. Create associated Profile
5. Send notification email to admin
6. Redirect to thanks page

**Admin Notification Email:**
- Lists: Username, Company, Business Entity
- Sent to: [REDACTED]
- Admin must manually activate user

### 7.4 Documentation Views (docs app)

**DocListView:** List all published docs
**DocDetailView:** Display single doc
**CreateDocView/DocUpdateView:** Create/edit docs (login required)
**DocDeleteView:** Delete docs with confirm
**doc_publish():** Change draft to published

---

## 8. CONFIGURATION & SETTINGS

### 8.1 Settings.py Configuration

**Key Parameters:**
```python
BASE_DIR = /mnt/d/demoproject/atp
TEMPLATE_DIR = BASE_DIR/templates
STATIC_URL = /static/
STATIC_ROOT = BASE_DIR/static
DEBUG = True  # WARNING: Should be False in production
SECRET_KEY = hardcoded (SECURITY ISSUE)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'stockcheck',
    'django.contrib.admin',
    'docs',
    'rest_framework',
    'rest_framework_jwt'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CSRF_TRUSTED_ORIGINS = [
    '[REDACTED]',
    '[REDACTED]/atp/login/'
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SECURE = True
```

### 8.2 Logging Configuration

**Output:** `/var/log/gunicorn/sap_interactions.log`

**Format:** `{timestamp} - {logger_name} - {level} - {message}`

**Loggers:**
- stockcheck: DEBUG level, logs to file and console

**SAP Call Logging Examples:**
```
SAP Call - Z_PATTERN_PRODUCTS - Input: reftype=P, value=pattern001
SAP Response - Z_PATTERN_PRODUCTS - Success - Products count: 42
SAP Response Details: {...}
SAP Call Failed - Z_GET_MATERIAL_DETAILS - Error: Connection timeout
Search initiated - User: demo.user, Plant: 1001, Type: Arc
Processing 5 chunks of reference numbers
Successfully retrieved data for 15 products
Search history saved for user: demo.user
```

### 8.3 Email Configuration

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = '[REDACTED]'
EMAIL_HOST_PASSWORD = '[REDACTED]'  # App password for Gmail
EMAIL_USE_TLS = True
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = '[REDACTED]'
SERVER_EMAIL = '[REDACTED]'
```

**Used For:**
- Account activation emails
- Password reset emails
- Search results email delivery
- New user signup notifications

---

## 9. DOCKER & DEPLOYMENT SETUP

### 9.1 Dockerfile

**Location:** `/mnt/d/demoproject/Dockerfile`

**Base Image:** ubuntu:18.04

**Key Components:**
```dockerfile
# Python 3.6 setup
RUN apt-get install -y python3.6 python3-pip python3-setuptools

# Build dependencies
RUN apt-get install -y build-essential libssl-dev libffi-dev \
    default-libmysqlclient-dev libpq-dev netcat

# SAP RFC SDK
COPY nwrfcsdk /usr/nwrfcsdk
ENV LD_LIBRARY_PATH=/usr/nwrfcsdk/lib:$LD_LIBRARY_PATH
ENV SAPNWRFC_HOME=/usr/nwrfcsdk

# Application setup
COPY atp /app
COPY pyrfc-1.9.93-cp36-cp36m-linux_x86_64.whl /app/
RUN pip install /app/pyrfc-1.9.93-cp36-cp36m-linux_x86_64.whl
RUN pip install -r /app/requirements.txt
RUN pip install mysqlclient gunicorn djangorestframework djangorestframework-jwt

# Initialization
RUN mkdir -p /app/sock /var/log/gunicorn
EXPOSE 8000

# Startup
CMD bash -c "
  echo 'Waiting for MySQL...' && 
  while ! nc -z db 3306; do sleep 1; done && 
  echo 'MySQL started' && 
  python manage.py migrate --noinput && 
  python manage.py collectstatic --noinput && 
  gunicorn --bind 0.0.0.0:8000 atp.wsgi:application
"
```

### 9.2 Docker Compose Configuration

**Location:** `/mnt/d/demoproject/docker-compose.yml`

**Services:**

**1. Web Service**
```yaml
web:
  build: .
  expose:
    - "8000"
  volumes:
    - ./atp:/app
    - ./nwrfcsdk:/usr/nwrfcsdk
    - log_data:/var/log/gunicorn
    - static_volume:/app/static
  environment:
    - DJANGO_SETTINGS_MODULE=atp.settings
    - PYTHONUNBUFFERED=1
    - DATABASE_HOST=db
    - DATABASE_NAME=atp
    - DATABASE_USER=dbuser
    - DATABASE_PASSWORD=[REDACTED]
    - SAP_HOST=your-sap-host
    - SAP_SYSNR=00
    - SAP_CLIENT=100
    - SAP_USER=your-sap-user
    - SAP_PASSWORD=your-sap-password
  depends_on:
    - db
  restart: unless-stopped
```

**2. Database Service (MySQL 5.7)**
```yaml
db:
  image: mysql:5.7
  volumes:
    - db_data:/var/lib/mysql
  environment:
    - MYSQL_DATABASE=atp
    - MYSQL_USER=dbuser
    - MYSQL_PASSWORD=[REDACTED]
    - MYSQL_ROOT_PASSWORD=[REDACTED]
  ports:
    - "3306:3306"
  restart: unless-stopped
```

**3. Nginx Service**
```yaml
nginx:
  image: nginx:1.19
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf
    - static_volume:/static
  ports:
    - "80:80"
  depends_on:
    - web
  restart: unless-stopped
```

**Volumes:**
- `db_data`: MySQL data persistence
- `log_data`: Application logs
- `static_volume`: Compiled static files

### 9.3 Nginx Configuration

**Location:** `/mnt/d/demoproject/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;

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

**Purpose:** Reverse proxy to Gunicorn, serves static files, handles HTTP requests.

---

## 10. TESTING INFRASTRUCTURE

### 10.1 Test SAP Connection Script

**File:** `/mnt/d/demoproject/test_sap_connection.py`

**Functions:**
- `get_connection_params()`: Read from settings.ini or env vars
- `test_connection()`: Connect and test RFC calls

**RFC Functions Tested:**
1. RFC_SYSTEM_INFO: Get SAP version
2. STFC_CONNECTION: Echo test

### 10.2 Database Migrations

**Migration Files:**
```
0001_initial.py         # Create initial models
0002_profile_business.py # Add business field to Profile
0003_auto_20190306_0915.py
0004_user.py            # User model changes
0005_auto_20230711_2155.py
```

### 10.3 Django Test Framework

**Test Files:** `stockcheck/tests.py`, `docs/tests.py`

(Note: Test files exist but content not extensively populated in current codebase)

---

## 11. CUSTOM MIDDLEWARE & UTILITIES

### 11.1 Audit Middleware

**File:** `/mnt/d/demoproject/atp/middleware/audit_middleware.py`

```python
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Get or create AuditEntry for session/user
            audit_entry, created = AuditEntry.objects.get_or_create(
                session_key=request.session.session_key,
                user=request.user.id,
                defaults={'host': request.META['HTTP_HOST']}
            )
            
            # Record login time if new
            if created:
                audit_entry.login_time = datetime.datetime.now()
                audit_entry.save()
            
            # Record logout if logging out
            if request.path == '/accounts/logout/':
                audit_entry.logout_time = datetime.datetime.now()
                audit_entry.save()
        
        response = self.get_response(request)
        return response
```

**Purpose:** Track user sessions and login/logout times in AuditEntry model.

### 11.2 Utility Scripts

**add_plants.py**
- Loads plant master data into database

**find_duplicate_emails.py**
- Identifies duplicate email addresses in user database
- Located in both root and stockcheck/

**resolve_duplicate_emails.py**
- Management command to resolve duplicate emails
- Located in stockcheck/management/commands/

---

## 12. FRONTEND COMPONENTS

### 12.1 Template Hierarchy

```
base.html (minimal structure, block content)
├── stockcheck/
│   ├── base.html (extended base with navbar, static links)
│   ├── index.html (landing page with typed.js animation)
│   ├── search.html (product search form)
│   ├── details.html (results table with export options)
│   ├── about.html
│   ├── help.html
│   ├── home.html
│   └── account_activation_email.html
├── registration/
│   ├── base.html
│   ├── login.html (Django auth form)
│   ├── signup.html (custom registration with Profile)
│   ├── password_reset_form.html
│   ├── password_reset_done.html
│   ├── password_reset_confirm.html
│   ├── password_reset_complete.html
│   ├── password_change.html
│   ├── feedback.html
│   └── thanks.html
└── docs/
    ├── doc_list.html (published docs)
    ├── doc_detail.html (single doc view)
    ├── doc_form.html (create/edit)
    └── doc_confirm_delete.html

```

### 12.2 Frontend Libraries

**CSS:**
- Bootstrap 4.1.3
- Font Awesome 5.15.4
- DataTables 1.10.19 (Bootstrap 4 theme)
- Custom cover.css (Demo branding)

**JavaScript:**
- jQuery 3.3.1
- Popper.js 1.14.3 (Bootstrap dependency)
- Bootstrap 4.1.3 JS
- DataTables 1.10.19 (with buttons, export, column visibility)
- PDF generation: pdfmake
- Typed.js 2.0.11 (typing animation)
- Custom blog.js

**Key Features:**
- Responsive Bootstrap grid
- DataTable with:
  - Column visibility toggle
  - Export to Excel/CSV/PDF
  - Print functionality
  - Responsive column reordering
  - Search and filtering
- Dynamic form behavior (show/hide pattern/universe fields)
- Email integration for results delivery

### 12.3 Search Results Display (details.html)

**Table Columns:**
1. Product Details (MATNR, Vendor SKU)
2. Description & Origin (MAKTX, Brand, Origin)
3. Stock Status (STOCK, ACTUAL with conditional coloring)
4. Supplier Delivery Info (EEIND, MNG01, ZMENG, ZKWMENG)
5. Additional Details (Type badge, Case pack, UPC, Weight)

**Visual Elements:**
- Badge for type (Stock item=green, On demand=red, No planning=blue)
- Negative ACTUAL shown in red
- Table hover effect
- Card-based layout with shadow
- Responsive table with horizontal scroll on mobile

### 12.4 Export Functionality

**Excel Download:**
- Filename: "Product stock info - {username} - {date}.xls"
- Format: XLS (xlwt library)
- 15 columns with bold header
- Includes all stock data

**Email Delivery:**
- Generates same XLS file
- Attaches with proper MIME type
- Sends via SMTP to user's email
- Subject includes timestamp
- HTML email template included

---

## 13. SECURITY ANALYSIS

### 13.1 Security Issues (Current)

**CRITICAL:**
1. **Hardcoded Secrets** - SECRET_KEY, database password, SAP credentials in source
   - `settings.py`: SECRET_KEY visible
   - `settings.ini`: SAP credentials in plain text
   - `settings.py`: Database password hardcoded
   - Email password: [REDACTED] in settings

2. **DEBUG = True** - Exposes sensitive information in error pages

3. **CSRF_TRUSTED_ORIGINS** - Hardcoded IP addresses

**HIGH:**
4. **No HTTPS** - Cookies sent over HTTP despite SESSION_COOKIE_SECURE=True

5. **No rate limiting** - Vulnerable to brute force attacks

6. **SQL Injection potential** - ConfigParser usage in settings.ini parsing

7. **No input validation** - Product numbers not sanitized before SAP calls

8. **Email password in settings** - Should use OAuth or app-specific passwords

**MEDIUM:**
9. **No password complexity requirements** - Only minimum length

10. **User creation doesn't auto-activate** - But admin email notification could be exploited

11. **No audit logging for sensitive actions** - Only login/logout tracked

12. **Sessions in database** - No cleanup of old sessions

### 13.2 CSRF Protection

**Configuration:**
```python
CSRF_TRUSTED_ORIGINS = ['[REDACTED]', '[REDACTED]/atp/login/']
MIDDLEWARE includes CsrfViewMiddleware
```

**All forms include:** `{% csrf_token %}`

### 13.3 Authentication

- Django auth backend (database)
- LoginRequiredMixin on protected views
- Custom login_url = '/login/' or '/atp/login/'
- Password reset via email token

---

## 14. KEY FEATURES SUMMARY

| Feature | Status | Description |
|---------|--------|-------------|
| **Product Search** | Implemented | Search by Arc/Vendor SKU, multiple plants |
| **SAP Integration** | Implemented | Real-time RFC calls, 3 main functions |
| **Stock Lookup** | Implemented | Display availability, delivery info |
| **Excel Export** | Implemented | 15-column formatted export |
| **Email Delivery** | Implemented | Send results to user email |
| **User Management** | Implemented | Registration, profile, role assignment |
| **Plant Assignment** | Implemented | Admin assigns plants to users |
| **Search History** | Implemented | Track user searches by date/product |
| **Audit Logging** | Implemented | Login/logout tracking |
| **Documentation** | Implemented | Publish help docs, CRUD interface |
| **Admin Interface** | Implemented | Full Django admin with custom actions |
| **Password Reset** | Implemented | Email-based token reset |
| **Feedback System** | Partially | Form template present, no backend handler |

---

## 15. DEPENDENCIES & REQUIREMENTS

**File:** `/mnt/d/demoproject/requirements.txt`

```
certifi==2018.11.29
chardet==3.0.4
Django==2.1.5
django-model-changes==0.15
gunicorn==19.9.0
idna==2.8
mysqlclient==1.4.1
numpy==1.16.1
psycopg2==2.7.7          # PostgreSQL (not used)
pyrfc==1.9.93            # SAP RFC integration
pytz==2018.9
requests==2.21.0
urllib3==1.24.1
XlsxWriter==1.1.2        # Excel file generation
xlwt==1.3.0              # Legacy XLS generation
```

**Additional (Docker):**
- djangorestframework
- djangorestframework-jwt
- mysqlclient (MySQL)
- gunicorn (WSGI server)

---

## 16. DEPLOYMENT FLOW

### Startup Sequence (Docker):

1. Build image from Dockerfile
2. Start MySQL service
3. Start web service (depends_on db)
4. Wait for MySQL to be ready (netcat check)
5. Run migrations: `python manage.py migrate --noinput`
6. Collect static files: `python manage.py collectstatic --noinput`
7. Start Gunicorn on port 8000
8. Start Nginx (depends_on web)
9. Nginx proxies HTTP to Gunicorn

### Accessing Application:

- **URL:** http://localhost
- **Nginx:** http://localhost:80
- **Gunicorn:** http://localhost:8000 (internal)
- **MySQL:** localhost:3306 (exposed for development)

### Database:

- **Type:** MySQL 5.7
- **Name:** atp
- **User:** dbuser
- **Password:** [REDACTED]
- **Persistence:** Docker volume db_data

---

## 17. KEY PATTERNS & BEST PRACTICES

### 17.1 Implemented

1. **Model Signals** - Auto-create Profile on User creation
2. **Django Forms** - ModelForm for Profile, custom Form for product search
3. **LoginRequiredMixin** - Protect views requiring authentication
4. **Template Inheritance** - base.html -> app-specific base.html
5. **Logging** - Structured logging to file for SAP interactions
6. **Configuration** - settings.ini for external configuration
7. **Management Commands** - CLI utilities in management/commands/
8. **Admin Customization** - Custom admin actions, inline models
9. **Email Integration** - EmailMultiAlternatives for HTML emails
10. **Session Storage** - Database-backed sessions

### 17.2 Missing/Incomplete

1. **Unit Tests** - test.py files exist but minimal content
2. **API Endpoints** - REST framework installed but no API views
3. **Caching** - No cache_page decorators used despite CACHE_TTL setting
4. **Async Tasks** - Celery not implemented (broker URL defined but unused)
5. **Pagination** - No pagination on large result sets
6. **Rate Limiting** - No throttling on search/export
7. **Documentation** - No docstrings in complex functions
8. **Error Handling** - Generic exception catching, not specific errors
9. **Input Validation** - Minimal validation before SAP calls
10. **Performance Optimization** - No query optimization (N+1 queries possible)

---

## 18. DATA FLOW DIAGRAMS

### Product Search Flow:

```
User Input (Search Form)
    ↓
SearchView.form_valid()
    ↓
Parse product numbers (split by comma/space)
    ↓
Chunk into groups of 100
    ↓
For each product → stock_info(plant, product, mode)
    ↓
Call Z_GET_MATERIAL_DETAILS RFC
    ↓
Transform data (date format, DISMM codes)
    ↓
Store in session['data']
    ↓
Save SearchHistory
    ↓
Render details.html with results
    ↓
User can:
  A) Download Excel
  B) Email Excel
  C) View in table
```

### Email Export Flow:

```
Results displayed in details.html
    ↓
User clicks "Download" or "Email"
    ↓
download_data() called
    ↓
Fetch session['data']
    ↓
Generate XLS via xlwt.Workbook
    ↓
If Download: Return HttpResponse with attachment
If Email:
    ↓
Create EmailMultiAlternatives
    ↓
Attach XLS file
    ↓
Send via SMTP (smtp.gmail.com:587)
    ↓
Redirect to product_details
```

### User Registration Flow:

```
User fills SignUpForm + ProfileForm
    ↓
Validate both forms
    ↓
Create User (is_active=False)
    ↓
Create Profile (via signal)
    ↓
Signal sends activation email to user
    ↓
Send notification email to admin
    ↓
Redirect to /thanks/
    ↓
Admin manually activates user
    ↓
User can login
```

---

## 19. POTENTIAL ISSUES & RECOMMENDATIONS

### 19.1 Known Issues

1. **Deprecated Library** - xlwt is deprecated, should use openpyxl/xlsxwriter
2. **Python 3.6 EOL** - Python 3.6 reached end-of-life, upgrade to 3.10+
3. **Django 2.1 Outdated** - Released 2018, no security updates
4. **SAP RFC SDK** - Requires system libraries, may have compatibility issues
5. **MySQL 5.7 EOL** - Released 2013, should upgrade to 5.7 LTS or 8.0
6. **No Input Sanitization** - Product numbers sent directly to SAP RFC

### 19.2 Recommendations

1. **Upgrade Technology Stack:**
   - Django 4.2 LTS
   - Python 3.10+
   - MySQL 8.0
   - DRF 3.14+

2. **Security Hardening:**
   - Move secrets to environment variables or .env
   - Set DEBUG=False in production
   - Use HTTPS/SSL everywhere
   - Implement rate limiting (Django-ratelimit)
   - Add input validation/sanitization

3. **Code Quality:**
   - Add pytest with coverage reporting
   - Implement pre-commit hooks (black, flake8, mypy)
   - Add docstrings to all functions
   - Use type hints

4. **Performance:**
   - Implement caching for search results
   - Use async/Celery for email delivery
   - Add pagination for large result sets
   - Database indexes on frequently queried fields

5. **Operations:**
   - Add health checks in docker-compose
   - Implement log rotation
   - Add monitoring/alerting
   - Create backup strategy

---

## 20. QUICK REFERENCE

### Important File Locations

| File | Purpose |
|------|---------|
| `/mnt/d/demoproject/atp/atp/settings.py` | Main Django settings |
| `/mnt/d/demoproject/atp/atp/urls.py` | Main URL routing |
| `/mnt/d/demoproject/atp/atp/settings.ini` | SAP connection config |
| `/mnt/d/demoproject/atp/stockcheck/models.py` | Database models |
| `/mnt/d/demoproject/atp/stockcheck/views.py` | Business logic (450 lines) |
| `/mnt/d/demoproject/atp/stockcheck/forms.py` | Form definitions |
| `/mnt/d/demoproject/atp/stockcheck/admin.py` | Admin customization |
| `/mnt/d/demoproject/atp/templates/stockcheck/` | HTML templates |
| `/mnt/d/demoproject/Dockerfile` | Container definition |
| `/mnt/d/demoproject/docker-compose.yml` | Service orchestration |
| `/mnt/d/demoproject/nginx.conf` | Reverse proxy config |
| `/mnt/d/demoproject/test_sap_connection.py` | SAP test script |

### Key Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f web

# Enter container shell
docker-compose exec web bash

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Test SAP connection
docker-compose exec web python test_sap_connection.py

# Run management commands
docker-compose exec web python manage.py <command>
```

### Default Credentials

| Service | Username | Password | Note |
|---------|----------|----------|------|
| MySQL | dbuser | [REDACTED] | Container env var |
| MySQL Root | root | [REDACTED] | Container env var |
| Email | [REDACTED] | [REDACTED] | Gmail app password |
| SAP | [REDACTED] | [REDACTED] | From settings.ini |
| Django Admin | (create with createsuperuser) | | |

---

## CONCLUSION

The ATP application is a full-featured Django web application that seamlessly integrates with SAP systems to provide real-time product availability checking. It implements modern web technologies (Bootstrap, DataTables, REST framework) with a comprehensive admin interface and audit logging. While the application is functional and production-deployed, it would benefit significantly from security hardening, technology stack upgrades, and comprehensive test coverage.

**Estimated Lines of Code:** ~5,000 (excluding dependencies and migrations)
**Database Tables:** 8 (+ Django auth/sessions tables)
**API Endpoints:** ~20 HTTP paths
**SAP RFC Functions:** 5 main functions integrated
**Templates:** ~25 HTML files
**Frontend Libraries:** 10+ JavaScript/CSS libraries

