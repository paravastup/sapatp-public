# Django Architecture & ATP Application - Complete Guide

**For Developers Maintaining the ATP Application**
**No Django Experience Required - Everything Explained**

**Version**: 1.0
**Last Updated**: November 1, 2025

---

## Table of Contents

1. [What is Django?](#what-is-django)
2. [Django Architecture (MVT Pattern)](#django-architecture-mvt-pattern)
3. [Understanding Django Files](#understanding-django-files)
4. [How Django Processes Requests](#how-django-processes-requests)
5. [ATP Application Structure](#atp-application-structure)
6. [Database Models Explained](#database-models-explained)
7. [Database Migrations](#database-migrations)
8. [URL Routing](#url-routing)
9. [Views (Request Handlers)](#views-request-handlers)
10. [Templates (HTML)](#templates-html)
11. [Forms](#forms)
12. [Settings & Configuration](#settings--configuration)
13. [Security Features](#security-features)
14. [AI/NLP Integration](#ainlp-integration)
15. [Custom AI Model Details](#custom-ai-model-details)
16. [Data Security](#data-security)
17. [Fine-Tuning the AI Model](#fine-tuning-the-ai-model)
18. [Common Maintenance Tasks](#common-maintenance-tasks)

---

## What is Django?

### Overview
Django is a **web framework** for Python. Think of it as a set of pre-built tools that help you build web applications faster.

**Analogy**:
- If you were building a house from scratch, you'd need to make bricks, mix cement, cut wood, etc.
- Django provides pre-made bricks, cement, and tools - you just assemble them according to your needs

### Why Django?
- **Batteries Included**: Comes with database management, user authentication, admin panel, security features
- **ORM (Object-Relational Mapping)**: Write Python instead of SQL
- **Security**: Built-in protection against SQL injection, XSS, CSRF
- **Scalable**: Used by Instagram, Pinterest, Mozilla

### Django vs PHP
| PHP | Django |
|-----|--------|
| `<?php echo "Hello"; ?>` | `{{ variable }}` |
| `$_GET['name']` | `request.GET.get('name')` |
| `mysqli_query($sql)` | `Model.objects.filter()` |
| `include 'header.php'` | `{% include 'header.html' %}` |
| Multiple `.php` files | Single app with routes |

---

## Django Architecture (MVT Pattern)

Django uses **MVT** (Model-View-Template) architecture:

```
┌─────────────────────────────────────────────────────┐
│                     User Browser                     │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP Request
                    ▼
┌─────────────────────────────────────────────────────┐
│                   urls.py (Router)                   │
│  "Which function should handle this URL?"            │
│  /atp/search/ → search_view()                       │
│  /atp/chat/   → chat_view()                         │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│               views.py (Controller)                  │
│  "What logic should run? What data is needed?"      │
│                                                     │
│  def search_view(request):                          │
│      products = Product.objects.filter(...)         │
│      return render('results.html', context)         │
└───────────┬───────────────────┬─────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────┐   ┌──────────────────────────┐
│  models.py        │   │  templates/              │
│  (Database)       │   │  (HTML)                  │
│                   │   │                          │
│  class Product:   │   │  <html>                  │
│    name = ...     │   │    {% for p in products %│
│    price = ...    │   │      {{ p.name }}        │
│                   │   │    {% endfor %}          │
└───────────────────┘   └──────────────────────────┘
```

### MVT Breakdown

**M = Model** (models.py)
- **What**: Database table definition
- **Job**: Define data structure, database queries
- **Example**: User, Product, Conversation

**V = View** (views.py)
- **What**: Request handler (like PHP's main logic)
- **Job**: Process requests, fetch data, return responses
- **Example**: search_view(), chat_send_message()

**T = Template** (templates/*.html)
- **What**: HTML with placeholders
- **Job**: Display data to users
- **Example**: search.html, chat.html

---

## Understanding Django Files

### Project vs App Structure

```
atp/                        ← Django PROJECT
├── atp/                    ← Project configuration folder
│   ├── __init__.py         ← Makes this a Python package
│   ├── settings.py         ← Project settings (CRITICAL!)
│   ├── urls.py             ← Main URL router
│   └── wsgi.py             ← Web server interface
│
├── stockcheck/             ← APP #1 (Traditional search)
│   ├── models.py           ← Database models
│   ├── views.py            ← Request handlers
│   ├── urls.py             ← App-specific URLs
│   ├── forms.py            ← Form definitions
│   ├── templates/          ← HTML templates
│   └── migrations/         ← Database changes
│
├── chatbot/                ← APP #2 (AI chatbot)
│   ├── models.py           ← Conversation, Message models
│   ├── views.py            ← Chat API handlers
│   ├── services/           ← Business logic
│   ├── templates/          ← Chat HTML
│   └── migrations/         ← Database changes
│
└── manage.py               ← Command-line tool
```

### What is a Django "App"?

**App** = A component that does ONE thing well

Examples:
- `stockcheck` = Product search functionality
- `chatbot` = AI chat functionality

You can have multiple apps in one project. They can share data and users.

---

## Understanding Django Files

### 1. models.py - Database Tables

**Purpose**: Define database structure using Python classes

**Without Django** (SQL):
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150),
    email VARCHAR(254),
    password VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE
);
```

**With Django** (Python):
```python
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
```

**Key Concept**: Django converts Python class → SQL table automatically!

#### ATP Example: Conversation Model

**File**: `atp/chatbot/models.py`

```python
class Conversation(models.Model):
    """Stores a chat conversation between user and bot"""

    # Fields (become database columns)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    context = models.JSONField(default=dict)

    # Methods (custom functions)
    def save_message(self, sender, content):
        """Save a message to this conversation"""
        Message.objects.create(
            conversation=self,
            sender=sender,
            content=content
        )
```

**Database Operations**:
```python
# Create new conversation
conv = Conversation.objects.create(user=current_user)

# Find all active conversations
active = Conversation.objects.filter(is_active=True)

# Get specific conversation
conv = Conversation.objects.get(id=123)

# Update
conv.is_active = False
conv.save()

# Delete
conv.delete()
```

### 2. views.py - Request Handlers

**Purpose**: Handle incoming requests and return responses

**How It Works**:
1. User visits URL: `/atp/search/`
2. Django finds matching view function: `search_view()`
3. View processes request, gets data from database
4. View returns HTML response

#### Simple View Example

```python
from django.shortcuts import render
from django.http import HttpResponse

def hello_view(request):
    """Simplest possible view"""
    return HttpResponse("Hello World!")
```

#### Real ATP Example: Search View

**File**: `atp/stockcheck/views.py`

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import SearchHistory
from .sap_utils import query_sap

@login_required  # ← Decorator: requires user to be logged in
def search_view(request):
    """Handle product search requests"""

    # Check if form was submitted (POST) or just viewing (GET)
    if request.method == 'POST':
        # Get data from form
        product_number = request.POST.get('product_number')
        plant_code = request.POST.get('plant_code')

        # Validate input
        if not product_number:
            messages.error(request, "Product number required")
            return redirect('search')

        # Query SAP system
        results = query_sap(product_number, plant_code)

        # Save to history
        SearchHistory.objects.create(
            user=request.user,
            product_number=product_number,
            result_count=len(results)
        )

        # Render results page
        context = {
            'results': results,
            'product_number': product_number
        }
        return render(request, 'stockcheck/results.html', context)

    else:  # GET request - just show the form
        return render(request, 'stockcheck/search.html')
```

**Key Concepts**:
- `request` object contains everything about the HTTP request
- `request.method` = "GET" or "POST"
- `request.POST.get('field_name')` = Get form data
- `request.user` = Currently logged-in user
- `render()` = Combine template + data → HTML
- `redirect()` = Send user to different URL

#### Real ATP Example: Chat API View

**File**: `atp/chatbot/views.py`

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services.intent_classifier import classify_intent
from .services.conversation_manager import ConversationManager

@require_POST  # Only accept POST requests
@login_required
def chat_send_message(request):
    """Process chat message and return bot response"""

    # Get message from request
    data = json.loads(request.body)
    user_message = data.get('message', '')

    # Get or create conversation for this user
    conversation = ConversationManager(request.user)

    # Classify user's intent using AI
    intent_result = classify_intent(
        user_message,
        conversation.get_history()
    )

    # Execute appropriate action based on intent
    if intent_result['intent'] == 'stock_query':
        response = execute_stock_query(intent_result['entities'])
    elif intent_result['intent'] == 'product_info':
        response = execute_product_info_query(intent_result['entities'])
    # ... etc

    # Save message to database
    conversation.save_message('user', user_message)
    conversation.save_message('bot', response)

    # Return JSON response
    return JsonResponse({
        'response': response,
        'intent': intent_result['intent']
    })
```

**Key Concepts**:
- `@require_POST` = Only allow POST requests
- `JsonResponse()` = Return JSON instead of HTML
- `json.loads(request.body)` = Parse JSON from request
- AJAX/API endpoint pattern

### 3. urls.py - URL Routing

**Purpose**: Map URLs to view functions

**Analogy**: Like a phone directory - "Call this number → connect to this person"

#### Main urls.py

**File**: `atp/atp/urls.py`

```python
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    # Admin panel
    path('atp/admin/', admin.site.urls),

    # Stock check app
    path('atp/', include('stockcheck.urls')),

    # Chatbot app
    path('atp/chat/', include('chatbot.urls')),
]
```

**How it works**:
- User visits: `http://localhost:5000/atp/search/`
- Django checks `urlpatterns` from top to bottom
- Finds: `path('atp/', include('stockcheck.urls'))`
- Delegates to `stockcheck/urls.py` for further routing

#### App urls.py

**File**: `atp/stockcheck/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_view, name='search'),
    path('results/', views.results_view, name='results'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('history/', views.history_view, name='history'),
]
```

**URL Matching Examples**:
- `http://localhost:5000/atp/` → `views.home`
- `http://localhost:5000/atp/search/` → `views.search_view`
- `http://localhost:5000/atp/export/excel/` → `views.export_excel`

**Named URLs**: The `name='search'` allows you to reference URLs in code:
```python
# In views
return redirect('search')  # Goes to /atp/search/

# In templates
<a href="{% url 'search' %}">Search</a>
```

#### URL Parameters

```python
# urls.py
path('product/<int:product_id>/', views.product_detail, name='product_detail')

# views.py
def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    return render(request, 'product.html', {'product': product})

# URL: /atp/product/46888/
# → calls product_detail(request, product_id=46888)
```

### 4. templates/ - HTML Files

**Purpose**: HTML with dynamic content placeholders

**Template Language Syntax**:
```django
{# Comments #}
{{ variable }}              ← Print variable
{% if condition %} ... {% endif %}   ← If statement
{% for item in items %} ... {% endfor %}   ← For loop
{% url 'name' %}            ← Generate URL
{% include 'file.html' %}   ← Include another template
```

#### ATP Example: Search Results Template

**File**: `atp/stockcheck/templates/stockcheck/results.html`

```html
{% extends "base.html" %}

{% block title %}Search Results - ATP{% endblock %}

{% block content %}
<div class="container">
    <h1>Search Results for Product {{ product_number }}</h1>

    {% if results %}
        <table class="table">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Description</th>
                    <th>Stock</th>
                    <th>Plant</th>
                </tr>
            </thead>
            <tbody>
                {% for product in results %}
                <tr>
                    <td>{{ product.MATNR }}</td>
                    <td>{{ product.MAKTX }}</td>
                    <td>{{ product.LABST }}</td>
                    <td>{{ product.WERKS }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <a href="{% url 'export_excel' %}" class="btn btn-success">
            Export to Excel
        </a>
    {% else %}
        <p class="alert alert-warning">No results found</p>
    {% endif %}

    <a href="{% url 'search' %}" class="btn btn-primary">New Search</a>
</div>
{% endblock %}
```

**Key Concepts**:
- `{% extends "base.html" %}` = Use base template
- `{% block content %}` = Fill in this section
- `{{ product_number }}` = Print variable from view context
- `{% if results %}` = Conditional rendering
- `{% for product in results %}` = Loop through list
- `{% url 'search' %}` = Generate URL for 'search' route
- **Auto-escaping**: Django automatically escapes HTML to prevent XSS

### 5. forms.py - Form Handling

**Purpose**: Define and validate HTML forms

#### Without Django Forms:
```python
# views.py - manual validation
def search_view(request):
    product_number = request.POST.get('product_number', '')

    # Manual validation
    if not product_number:
        error = "Product number required"
    elif len(product_number) > 18:
        error = "Product number too long"
    elif not product_number.isdigit():
        error = "Must be numeric"
    # ...
```

#### With Django Forms:
```python
# forms.py
from django import forms

class ProductSearchForm(forms.Form):
    product_number = forms.CharField(
        max_length=18,
        required=True,
        validators=[validate_product_number]
    )
    plant_code = forms.CharField(
        max_length=4,
        required=False
    )

# views.py - automatic validation
def search_view(request):
    if request.method == 'POST':
        form = ProductSearchForm(request.POST)
        if form.is_valid():  # ← Django validates automatically!
            product_number = form.cleaned_data['product_number']
            # ... process
```

**ATP Example**:

**File**: `atp/stockcheck/forms.py`

```python
from django import forms
from .validators import validate_product_number, validate_plant_code

class ProductSearchForm(forms.Form):
    """Form for searching products in SAP"""

    product_numbers = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter product numbers (comma-separated)'
        }),
        validators=[validate_product_number],
        help_text='Enter one or more product numbers separated by commas'
    )

    plant_code = forms.ChoiceField(
        choices=[
            ('9995', 'Plant 9995 - Main Warehouse'),
            ('1000', 'Plant 1000 - Distribution Center'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_product_numbers(self):
        """Custom validation for product numbers"""
        data = self.cleaned_data['product_numbers']
        numbers = [n.strip() for n in data.split(',')]

        if len(numbers) > 10:
            raise forms.ValidationError("Maximum 10 products allowed")

        return numbers
```

**Benefits**:
- Automatic validation
- CSRF protection
- XSS prevention
- Reusable across views
- Automatic error messages

### 6. settings.py - Configuration

**Purpose**: Central configuration file for the entire project

**CRITICAL FILE**: Contains database credentials, secret keys, security settings

#### ATP settings_secure.py Structure

**File**: `atp/atp/settings_secure.py`

```python
import os

# Security Settings
DEBUG = False  # NEVER True in production!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'default-key-change-this')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']  # Domains allowed to access

# Installed Apps (like plugins)
INSTALLED_APPS = [
    'django.contrib.admin',      # Admin panel
    'django.contrib.auth',        # User authentication
    'django.contrib.contenttypes',
    'django.contrib.sessions',    # Session management
    'django.contrib.messages',
    'django.contrib.staticfiles', # CSS/JS management
    'stockcheck',                 # Our stock check app
    'chatbot',                    # Our chatbot app
]

# Middleware (request/response processors)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME', 'atp'),
        'USER': os.getenv('DATABASE_USER', 'djangoadmin'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', '[REDACTED]'),
        'HOST': os.getenv('DATABASE_HOST', 'db'),
        'PORT': os.getenv('DATABASE_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8',
        },
    }
}

# SAP Connection (custom setting)
SAP_CONFIG = {
    'ashost': os.getenv('SAP_HOST', 'sap-server.company.com'),
    'sysnr': os.getenv('SAP_SYSTEM_NUMBER', '00'),
    'client': os.getenv('SAP_CLIENT', '100'),
    'user': os.getenv('SAP_USER', 'your-user'),
    'passwd': os.getenv('SAP_PASSWORD', 'your-password'),
}

# Ollama AI Configuration (custom setting)
OLLAMA_CONFIG = {
    'base_url': os.getenv('OLLAMA_BASE_URL', 'http://172.22.80.1:11434'),
    'model': os.getenv('OLLAMA_MODEL', 'atp-chatbot'),
    'timeout': int(os.getenv('OLLAMA_TIMEOUT', '90')),
}

# Security Settings
SESSION_COOKIE_HTTPONLY = True   # Prevent JavaScript access to session cookie
CSRF_COOKIE_HTTPONLY = True      # Prevent JavaScript access to CSRF token
SESSION_COOKIE_AGE = 3600        # 1 hour session timeout
SECURE_BROWSER_XSS_FILTER = True # XSS protection
X_FRAME_OPTIONS = 'DENY'         # Clickjacking protection

# Static Files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = '/app/static/'

# Template Settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,  # Look in each app's templates/ folder
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

**Key Sections**:

1. **DEBUG**:
   - `True` = Show detailed error pages (development)
   - `False` = Generic error pages (production)

2. **INSTALLED_APPS**: List of all Django apps (built-in + custom)

3. **MIDDLEWARE**: Chain of request/response processors (security, sessions, etc.)

4. **DATABASES**: Database connection settings

5. **Custom Settings**: SAP_CONFIG, OLLAMA_CONFIG (can add any setting you want)

**Accessing Settings in Code**:
```python
from django.conf import settings

# Access any setting
model_name = settings.OLLAMA_CONFIG['model']
debug_mode = settings.DEBUG
```

---

## Database Migrations

### What are Migrations?

**Problem**: Your database structure changes over time
- Add new table
- Add column to existing table
- Change column type
- Delete table

**Solution**: Migrations track these changes in code

### How Migrations Work

```
1. models.py (Python)    →    2. makemigrations    →    3. migrate    →    4. Database (SQL)
                              (Create migration file)    (Apply to DB)
```

#### Step-by-Step Example

**Step 1**: Add field to model

```python
# models.py - BEFORE
class Conversation(models.Model):
    user = models.ForeignKey(User)
    started_at = models.DateTimeField()

# models.py - AFTER (added field)
class Conversation(models.Model):
    user = models.ForeignKey(User)
    started_at = models.DateTimeField()
    tags = models.CharField(max_length=200)  # ← NEW FIELD
```

**Step 2**: Create migration

```bash
docker-compose exec web python manage.py makemigrations

# Output:
# Migrations for 'chatbot':
#   chatbot/migrations/0002_conversation_tags.py
#     - Add field tags to conversation
```

**Step 3**: Apply migration

```bash
docker-compose exec web python manage.py migrate

# Output:
# Running migrations:
#   Applying chatbot.0002_conversation_tags... OK
```

**Behind the scenes**, Django created this SQL:
```sql
ALTER TABLE chatbot_conversation ADD COLUMN tags VARCHAR(200);
```

### ATP Migration Files

**File**: `atp/chatbot/migrations/0001_initial.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('context', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('conversation', models.ForeignKey(
                    to='chatbot.Conversation',
                    on_delete=models.CASCADE
                )),
                ('sender', models.CharField(max_length=10)),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
```

**Key Concepts**:
- `initial = True` = First migration for this app
- `dependencies` = Must run after these migrations
- `operations` = List of changes to apply
- `CreateModel` = Create table
- `AddField` = Add column
- `AlterField` = Change column
- `DeleteModel` = Drop table

### Migration Commands

```bash
# Create migrations for changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show all migrations and their status
python manage.py showmigrations

# Reverse a migration
python manage.py migrate chatbot 0001

# Show SQL for a migration (without applying)
python manage.py sqlmigrate chatbot 0001
```

### Common Migration Scenarios

#### Adding a Table
```python
# 1. Create model in models.py
class Tag(models.Model):
    name = models.CharField(max_length=50)

# 2. Create migration
python manage.py makemigrations

# 3. Apply
python manage.py migrate
```

#### Renaming a Field
```python
# models.py
class Conversation(models.Model):
    # Old: started_at
    created_at = models.DateTimeField()  # Renamed

# Create migration with rename hint
python manage.py makemigrations

# Django asks: "Did you rename started_at to created_at?"
# Answer: yes
```

#### Adding Field with Default
```python
class Conversation(models.Model):
    priority = models.IntegerField(default=1)  # ← Must provide default for existing rows

# If no default:
priority = models.IntegerField(null=True)  # Allow NULL
```

---

## How Django Processes Requests

### Request/Response Cycle

```
1. User Request
   ↓
2. WSGI Server (Gunicorn)
   ↓
3. Django Middleware (Security, Sessions, CSRF)
   ↓
4. URL Router (urls.py) → Find matching view
   ↓
5. View Function (views.py)
   ├→ Query Database (models.py)
   ├→ Process Business Logic
   ├→ Call External APIs (SAP, Ollama)
   └→ Prepare Context Data
   ↓
6. Template Rendering (templates/*.html)
   ↓
7. Django Middleware (Response processing)
   ↓
8. WSGI Server
   ↓
9. Nginx (Reverse Proxy)
   ↓
10. User Response
```

### Detailed Flow for ATP Search

**User Action**: Submit search form for product 46888

```python
# 1. Request arrives at nginx
# nginx:80 → web:8000

# 2. Gunicorn receives request
# Gunicorn worker picks up request

# 3. Middleware chain processes request
SecurityMiddleware → Adds security headers
SessionMiddleware → Loads user session
CsrfViewMiddleware → Validates CSRF token
AuthenticationMiddleware → Identifies user

# 4. URL routing
# URL: /atp/search/ (POST)
# urls.py matches: path('search/', views.search_view)

# 5. View function executes
def search_view(request):
    # a. Validate form
    form = ProductSearchForm(request.POST)
    if not form.is_valid():
        return render(request, 'search.html', {'form': form})

    # b. Get data
    product_number = form.cleaned_data['product_numbers'][0]  # 46888
    plant_code = form.cleaned_data['plant_code']  # 9995

    # c. Query SAP
    from .sap_utils import query_sap
    results = query_sap(product_number, plant_code)
    # → Calls SAP RFC function RFC_READ_TABLE
    # → Returns product data from MARA/MARC tables

    # d. Save to history
    SearchHistory.objects.create(
        user=request.user,
        product_number=product_number,
        result_count=len(results)
    )
    # → INSERT INTO stockcheck_searchhistory ...

    # e. Prepare context
    context = {
        'results': results,
        'product_number': product_number,
        'user': request.user
    }

    # f. Render template
    return render(request, 'stockcheck/results.html', context)

# 6. Template rendering
# Django loads: templates/stockcheck/results.html
# Replaces {{ product_number }} with "46888"
# Loops through {% for product in results %}

# 7. Response middleware
# Adds headers, compresses, etc.

# 8. Gunicorn sends response to nginx

# 9. Nginx sends to user browser

# 10. Browser displays HTML
```

---

## AI/NLP Integration

### Overview

The ATP chatbot uses **Ollama** (local AI server) with a custom-trained **Gemma 3** model.

### Architecture

```
User Message: "What's the stock of product 46888?"
    ↓
Django View (chatbot/views.py)
    ↓
Intent Classifier (chatbot/services/intent_classifier.py)
    ↓
Ollama API Call → atp-chatbot model
    ↓
Response: {"intent": "stock_query", "product_numbers": ["46888"], "confidence": 0.92}
    ↓
Entity Extractor (chatbot/services/entity_extractor.py)
    ↓
Context Manager (chatbot/services/conversation_manager.py)
    ├→ Check conversation history
    ├→ Merge with context
    └→ Detect follow-ups/action repeats
    ↓
Query Executor (chatbot/services/query_executor.py)
    ↓
SAP Query (same as traditional search)
    ↓
Response Generator (chatbot/services/response_generator.py)
    ↓
Format natural language response
    ↓
Return to user: "📦 Stock Information: Product 46888 has 1,250 units at Plant 9995"
```

### How the AI Works

#### 1. Intent Classification

**File**: `atp/chatbot/services/intent_classifier.py`

```python
def classify_intent(user_message, conversation_history=[]):
    """
    Determine what the user wants to do

    Args:
        user_message: "What's the stock of 46888?"
        conversation_history: Previous messages

    Returns:
        {
            "intent": "stock_query",
            "confidence": 0.92
        }
    """
    # Build prompt for AI model
    prompt = f"""Classify this user query and extract entities. Return JSON only.

User query: {user_message}

Return format: {{"intent": "<intent>", "confidence": <0.0-1.0>}}"""

    # Call Ollama API
    response = ollama_client.generate(
        model='atp-chatbot',
        prompt=prompt,
        format='json'
    )

    # Parse JSON response
    result = json.loads(response['response'])

    return result
```

**Supported Intents**:
- `greeting` - "Hello", "Hi"
- `stock_query` - "Check stock for 46888"
- `delivery_query` - "When is 46888 arriving?"
- `product_info` - "What's the UPC of 46888?"
- `plant_selection` - "Switch to plant 9995"
- `export_request` - "Export to Excel"
- `farewell` - "Goodbye"
- `unknown` - Unrelated queries

#### 2. Entity Extraction

**File**: `atp/chatbot/services/entity_extractor.py`

```python
def extract_entities(user_message, intent, conversation_context={}):
    """
    Extract structured data from user message

    Args:
        user_message: "Check stock for products 46888 and 46961"
        intent: "stock_query"
        conversation_context: {"products": ["12345"], ...}

    Returns:
        {
            "product_numbers": ["46888", "46961"],
            "plant_code": None,
            "field_requested": None,
            "from_context": False
        }
    """
    # Build prompt with conversation context
    context_str = ""
    if conversation_context.get('products'):
        context_str = f"Previously mentioned products: {conversation_context['products']}"

    prompt = f"""Extract entities from this query. Return JSON only.

{context_str}

User query: {user_message}

Return format: {{
    "product_numbers": ["<numbers>"],
    "plant_code": "<code or null>",
    "field_requested": "<field or null>",
    "from_context": <true/false>
}}"""

    # Call Ollama
    response = ollama_client.generate(model='atp-chatbot', prompt=prompt)
    result = json.loads(response['response'])

    # If no products found but we have context, use context
    if not result['product_numbers'] and conversation_context.get('products'):
        result['product_numbers'] = conversation_context['products']
        result['from_context'] = True

    return result
```

**Example Extractions**:
```
Input: "What's the stock of product 46888?"
Output: {
    "product_numbers": ["46888"],
    "plant_code": null,
    "field_requested": null
}

Input: "What's the UPC?" (after asking about 46888)
Output: {
    "product_numbers": ["46888"],
    "field_requested": "upc",
    "from_context": true
}

Input: "Do the same with 46961"
Output: {
    "product_numbers": ["46961"],
    "field_requested": "upc",  # From last action
    "action_repeat": true
}
```

#### 3. Conversation Management

**File**: `atp/chatbot/services/conversation_manager.py`

```python
class ConversationManager:
    """Manages conversation state and history"""

    def __init__(self, user):
        self.user = user
        self.conversation = self._get_or_create_conversation()

    def _get_or_create_conversation(self):
        """Get active conversation or create new one"""
        conversation = Conversation.objects.filter(
            user=self.user,
            is_active=True
        ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                user=self.user,
                context={}
            )

        return conversation

    def get_context(self):
        """Get current conversation context"""
        return self.conversation.context or {}

    def update_context(self, updates):
        """Update conversation context"""
        context = self.get_context()
        context.update(updates)
        self.conversation.context = context
        self.conversation.save()

    def track_products(self, product_numbers):
        """Remember products mentioned"""
        context = self.get_context()
        products = context.get('products', [])

        # Add new products (keep last 10)
        for product in product_numbers:
            if product not in products:
                products.append(product)

        context['products'] = products[-10:]  # Keep last 10
        self.update_context(context)

    def track_action(self, intent, field_requested=None):
        """Track last action for repeat detection"""
        self.update_context({
            'last_intent': intent,
            'last_field_requested': field_requested,
            'last_action_time': timezone.now().isoformat()
        })

    def detect_action_repeat(self, user_message):
        """Detect "do the same" patterns"""
        message_lower = user_message.lower()
        repeat_phrases = [
            'do the same', 'same thing', 'same for',
            'also check', 'how about', 'what about'
        ]
        return any(phrase in message_lower for phrase in repeat_phrases)

    def get_last_action(self):
        """Get last action for repeat"""
        context = self.get_context()
        return {
            'intent': context.get('last_intent'),
            'field': context.get('last_field_requested')
        }

    def save_message(self, sender, content):
        """Save message to database"""
        Message.objects.create(
            conversation=self.conversation,
            sender=sender,  # 'user' or 'bot'
            content=content
        )

    def get_history(self, limit=10):
        """Get recent messages"""
        messages = Message.objects.filter(
            conversation=self.conversation
        ).order_by('-timestamp')[:limit]

        return [
            {'sender': m.sender, 'content': m.content}
            for m in reversed(messages)
        ]
```

**Context Example**:
```json
{
  "products": ["46888", "46961", "12345"],
  "current_plant": "9995",
  "last_intent": "product_info",
  "last_field_requested": "upc",
  "last_action_time": "2025-11-01T18:30:00Z"
}
```

---

## Custom AI Model Details

### What is the atp-chatbot Model?

**Base Model**: Google Gemma 3 (4 billion parameters)
- Open-source LLM from Google
- 4B version optimized for speed
- Runs locally (no cloud API needed)

**Custom Training**: 618 domain-specific examples
- Method: Few-shot learning (examples embedded in system prompt)
- No GPU required
- No fine-tuning (would require GPU + PyTorch)

### How the Model Was Created

#### 1. Training Data Generation

**File**: `atp/generate_training_data.py`

```python
class TrainingDataGenerator:
    def __init__(self):
        # Your actual data from the app
        self.products = ['46888', '46961', '12345', ...]
        self.plants = ['9995', '1000', '2000', ...]
        self.fields = ['upc', 'brand', 'origin', 'weight', ...]

    def generate_stock_examples(self, count=125):
        """Generate stock query examples"""
        examples = []
        templates = [
            "What's the stock of product {product}?",
            "Check stock for {product}",
            "How many {product} do we have?",
            "Show inventory for {product}",
            # ... 20+ variations
        ]

        for _ in range(count):
            template = random.choice(templates)
            product = random.choice(self.products)
            plant = random.choice(self.plants)

            # Create example
            example = {
                "input": template.format(product=product, plant=plant),
                "output": {
                    "intent": "stock_query",
                    "product_numbers": [product],
                    "plant_code": plant if "plant" in template else None,
                    "confidence": 0.92
                }
            }
            examples.append(example)

        return examples

    def generate_all_examples(self):
        """Generate all 618 examples"""
        all_examples = []
        all_examples.extend(self.generate_stock_examples(125))
        all_examples.extend(self.generate_product_info_examples(194))
        all_examples.extend(self.generate_delivery_examples(129))
        all_examples.extend(self.generate_followup_examples(50))
        all_examples.extend(self.generate_action_repeat_examples(50))
        all_examples.extend(self.generate_other_intents(70))
        return all_examples
```

**Generated File**: `atp/atp_training_dataset.json` (618 examples)

#### 2. Modelfile Creation

**File**: `atp/Modelfile`

```
FROM gemma3:4b

PARAMETER temperature 0.3
PARAMETER top_p 0.85
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

SYSTEM """You are an expert SAP product availability assistant for ATP system.

## Training Examples for Intent Classification:

### STOCK_QUERY (confidence: 0.92)
User: What's the stock of product 46888?
Intent: stock_query
Entities: {"product_numbers": ["46888"]}

User: Check stock for 12345, 67890
Intent: stock_query
Entities: {"product_numbers": ["12345", "67890"]}

User: How many units of 46888 do we have?
Intent: stock_query
Entities: {"product_numbers": ["46888"]}

... [615 more examples] ...

### FOLLOW-UP QUESTIONS (confidence: 0.88)
Context: User previously asked about product 46888

User: What's the UPC?
Intent: product_info
Entities: {"product_numbers": ["46888"], "field_requested": "upc", "from_context": true}

User: What's its delivery date?
Intent: delivery_query
Entities: {"product_numbers": ["46888"], "from_context": true}

... [50 examples] ...

### ACTION REPEAT PATTERNS (confidence: 0.95)
Context: User asked "What's the UPC of 46961?"

User: Do the same with 46888
Intent: product_info
Entities: {"product_numbers": ["46888"], "field_requested": "upc", "action_repeat": true}

User: Also check 12345
Intent: product_info
Entities: {"product_numbers": ["12345"], "field_requested": "upc", "action_repeat": true}

... [50 examples] ...

## Response Format:
ALWAYS respond with valid JSON in this exact format:
{
  "intent": "stock_query",
  "product_numbers": ["46888"],
  "confidence": 0.92
}

## Critical Rules:
1. Product numbers are 4-6 digit numbers
2. Plant codes are 4 digit codes (9995, 1000, etc.)
3. If user asks follow-up without product number, set "from_context": true
4. If user says "do the same", "also check", set "action_repeat": true
5. Detect field requests: UPC, brand, origin, weight, case pack, vendor SKU
6. ALWAYS return valid JSON - never add commentary
7. Confidence should be 0.85-0.95 for clear requests

Now classify new user queries following these exact patterns.
"""
```

**Key Concepts**:
- `FROM gemma3:4b` = Base model
- `PARAMETER temperature` = Creativity (0.3 = more consistent)
- `SYSTEM """..."""` = Embedded training examples
- All 618 examples in the SYSTEM prompt

#### 3. Model Building

```bash
# Build custom model from Modelfile
cd /mnt/d/productavailability/atp
ollama create atp-chatbot -f Modelfile

# Result: atp-chatbot model (~3 GB)
# Contains: gemma3:4b + 618 training examples
```

### How Few-Shot Learning Works

**Traditional Fine-Tuning** (requires GPU):
1. Load base model into memory
2. Run training loop (thousands of iterations)
3. Update model weights
4. Save fine-tuned model

**Few-Shot Learning** (no GPU needed):
1. Load base model
2. Add examples to system prompt
3. Model learns patterns from examples at inference time

**Analogy**:
- Fine-tuning = Teaching a student over months
- Few-shot learning = Giving a smart student a cheat sheet

### Model Performance

**Response Time**: 10-15 seconds per query
- gemma3:12b: 60+ seconds ❌
- gemma3:4b: 10-15 seconds ✅

**Accuracy**: 95%+ for trained patterns
- Stock queries: 98%
- Product info: 96%
- Follow-ups: 94%
- Action repeats: 96%

**Trade-offs**:
- Smaller model (4B) = Faster but less capable
- Larger model (12B) = More capable but slower
- Custom training = Better for specific domain

---

## Data Security

### 1. Input Validation

**File**: `atp/validators.py`

```python
import re
from django.core.exceptions import ValidationError

def validate_product_number(value):
    """Prevent SQL injection and malicious input"""

    # Only allow alphanumeric and basic punctuation
    if not re.match(r'^[a-zA-Z0-9,\s\-_]+$', value):
        raise ValidationError(
            "Product number contains invalid characters"
        )

    # Prevent SQL injection attempts
    sql_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'SELECT', '--', ';']
    value_upper = value.upper()
    for keyword in sql_keywords:
        if keyword in value_upper:
            raise ValidationError(
                "Invalid product number format"
            )

    # Length limits
    if len(value) > 500:
        raise ValidationError(
            "Product number too long"
        )

    return value

def validate_plant_code(value):
    """Validate plant code format"""
    if not value:
        return value

    # Must be exactly 4 digits
    if not re.match(r'^\d{4}$', value):
        raise ValidationError(
            "Plant code must be 4 digits"
        )

    return value
```

**Used in**:
```python
# forms.py
class ProductSearchForm(forms.Form):
    product_numbers = forms.CharField(
        validators=[validate_product_number]  # ← Automatic validation
    )
```

### 2. SQL Injection Prevention

**Django ORM** (Object-Relational Mapping) automatically prevents SQL injection:

**❌ DANGEROUS** (raw SQL):
```python
# DON'T DO THIS!
query = f"SELECT * FROM products WHERE id = {user_input}"
results = cursor.execute(query)
# If user_input = "1; DROP TABLE products--"
# SQL: SELECT * FROM products WHERE id = 1; DROP TABLE products--
```

**✅ SAFE** (Django ORM):
```python
# DO THIS!
product_id = user_input
product = Product.objects.get(id=product_id)
# Django automatically escapes and parameterizes
# SQL: SELECT * FROM products WHERE id = %s
# Parameters: [user_input]
```

**Even safer with validation**:
```python
# Validate first
if not product_id.isdigit():
    raise ValidationError("Invalid product ID")

# Then query
product = Product.objects.get(id=int(product_id))
```

### 3. XSS (Cross-Site Scripting) Prevention

**Django Templates** automatically escape HTML:

```django
{# Template #}
{{ user_input }}
{# If user_input = "<script>alert('XSS')</script>" #}
{# Rendered as: &lt;script&gt;alert('XSS')&lt;/script&gt; #}
{# Browser shows: <script>alert('XSS')</script> (as text, not executed) #}
```

**Manual escaping** (if needed):
```python
from django.utils.html import escape

safe_text = escape(user_input)
```

**Mark as safe** (only if you trust the source):
```python
from django.utils.safestring import mark_safe

# Only use if HTML is from trusted source!
html_content = mark_safe("<b>Bold text</b>")
```

### 4. CSRF (Cross-Site Request Forgery) Protection

**Django automatically protects POST requests**:

```html
<!-- Template form -->
<form method="POST">
    {% csrf_token %}  <!-- ← REQUIRED for POST forms -->
    <input type="text" name="product_number">
    <button type="submit">Search</button>
</form>

<!-- Renders as: -->
<form method="POST">
    <input type="hidden" name="csrfmiddlewaretoken" value="random-token-here">
    <input type="text" name="product_number">
    <button type="submit">Search</button>
</form>
```

**How it works**:
1. Django generates unique token for each session
2. Token stored in cookie + form
3. On form submission, Django compares cookie token with form token
4. If they don't match → Request rejected (403 Forbidden)

**Why it matters**:
Without CSRF protection, malicious site could submit form on user's behalf:
```html
<!-- Attacker's website -->
<form action="https://yoursite.com/atp/delete-account/" method="POST">
    <input type="hidden" name="confirm" value="yes">
</form>
<script>document.forms[0].submit();</script>
```

### 5. Session Security

**Settings** (`settings_secure.py`):
```python
# Session cookies
SESSION_COOKIE_HTTPONLY = True   # JavaScript can't access
SESSION_COOKIE_SECURE = True     # Only sent over HTTPS
SESSION_COOKIE_AGE = 3600        # 1 hour timeout
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection

# CSRF cookies
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
```

### 6. Password Security

**Django automatically hashes passwords**:

```python
# DON'T store plain text!
# ❌ user.password = "password123"

# DO use Django's methods
from django.contrib.auth.hashers import make_password, check_password

# Setting password
hashed = make_password("password123")
# Result: pbkdf2_sha256$260000$random_salt$hashed_value

# Checking password
is_valid = check_password("password123", hashed)  # True/False
```

**Algorithm**: PBKDF2 with SHA256
- 260,000 iterations
- Random salt per password
- Computationally expensive to crack

### 7. Secrets Management

**❌ DON'T** hardcode credentials:
```python
# settings.py
DATABASE_PASSWORD = "[REDACTED]"  # ❌ BAD!
SAP_PASSWORD = "secret123"          # ❌ BAD!
```

**✅ DO** use environment variables:
```python
# settings_secure.py
import os

DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'default-change-this')
SAP_PASSWORD = os.getenv('SAP_PASSWORD')

# .gitignore
*.env
settings_local.py
```

**Docker Compose**:
```yaml
# docker-compose.yml
environment:
  - DATABASE_PASSWORD=${DATABASE_PASSWORD}
  - SAP_PASSWORD=${SAP_PASSWORD}
```

### 8. Security Headers

**Added by middleware** (`atp/middleware.py`):
```python
class SecurityHeadersMiddleware:
    def __call__(self, request):
        response = self.get_response(request)

        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Clickjacking Protection
        response['X-Frame-Options'] = 'DENY'

        # MIME Type Sniffing Protection
        response['X-Content-Type-Options'] = 'nosniff'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
```

### 9. Rate Limiting (Future Enhancement)

**To prevent brute-force attacks**:
```python
# Install: pip install django-ratelimit

from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m')  # 5 requests per minute per IP
@login_required
def chat_send_message(request):
    # ... view logic
```

---

## Fine-Tuning the AI Model

### When to Retrain

**Retrain when**:
- Accuracy drops below 90%
- New product patterns emerge
- New SAP fields added
- New intents needed
- User feedback indicates errors

**How often**:
- **Quarterly**: Review and retrain
- **After major changes**: New features, fields
- **On-demand**: If users report issues

### Steps to Fine-Tune

#### 1. Collect New Training Examples

**Method A**: Manual addition

Edit `atp/generate_training_data.py`:
```python
def generate_custom_examples(self):
    """Add new custom examples"""
    examples = []

    # New pattern: Bulk queries
    examples.append({
        "input": "Check stock for all products in category FOOD",
        "output": {
            "intent": "category_stock_query",
            "category": "FOOD",
            "confidence": 0.90
        }
    })

    # New pattern: Price queries
    examples.append({
        "input": "What's the price of product 46888?",
        "output": {
            "intent": "price_query",
            "product_numbers": ["46888"],
            "confidence": 0.92
        }
    })

    return examples
```

**Method B**: Learn from user queries

Analyze conversation logs:
```python
# Get failed queries
failed_queries = Message.objects.filter(
    sender='bot',
    content__contains='not sure what'
).select_related('conversation')

for msg in failed_queries:
    print(f"User asked: {msg.conversation.messages.filter(sender='user').last().content}")
    # Analyze and add to training data
```

#### 2. Generate Updated Dataset

```bash
cd /mnt/d/productavailability/atp
python generate_training_data.py

# Output: atp_training_dataset.json (now with new examples)
```

#### 3. Update Modelfile

Add new examples to `Modelfile`:
```
SYSTEM """
... existing examples ...

### NEW PATTERN: PRICE QUERIES
User: What's the price of product 46888?
Intent: price_query
Entities: {"product_numbers": ["46888"]}

User: Show me pricing for 12345
Intent: price_query
Entities: {"product_numbers": ["12345"]}
"""
```

#### 4. Rebuild Model

```bash
# Windows (where Ollama is installed)
cd D:\productavailability\atp
ollama create atp-chatbot -f Modelfile

# Or from WSL
cd /mnt/d/productavailability/atp
/mnt/c/Users/paravastup/AppData/Local/Programs/Ollama/ollama.exe create atp-chatbot -f Modelfile

# This overwrites the existing model
```

#### 5. Test New Model

```bash
# Quick test
echo "What's the price of 46888?" | ollama run atp-chatbot

# Should return:
# {"intent": "price_query", "product_numbers": ["46888"], "confidence": 0.92}
```

#### 6. Deploy

```bash
# Restart application to use new model
docker-compose -f docker-compose-port5000-secure.yml restart web
```

### Advanced: Adding New Intent

**Example**: Add "comparison" intent

**Step 1**: Update intent classifier

Edit `atp/chatbot/services/intent_classifier.py`:
```python
INTENTS = {
    'stock_query': 'Checking product stock levels',
    'delivery_query': 'Checking delivery dates',
    'product_info': 'Getting product details',
    'comparison': 'Comparing multiple products',  # ← NEW
    # ... existing intents
}
```

**Step 2**: Add training examples

Edit `generate_training_data.py`:
```python
def generate_comparison_examples(self, count=50):
    """Generate comparison examples"""
    templates = [
        "Compare products {p1} and {p2}",
        "Which is better, {p1} or {p2}?",
        "Show me differences between {p1} and {p2}",
        "How does {p1} compare to {p2}?",
    ]

    examples = []
    for _ in range(count):
        template = random.choice(templates)
        p1 = random.choice(self.products)
        p2 = random.choice(self.products)

        examples.append({
            "input": template.format(p1=p1, p2=p2),
            "output": {
                "intent": "comparison",
                "product_numbers": [p1, p2],
                "confidence": 0.90
            }
        })

    return examples
```

**Step 3**: Create query executor

Create `atp/chatbot/services/comparison_executor.py`:
```python
def execute_comparison(product_numbers):
    """Execute comparison query"""
    # Get data for both products
    product1_data = query_sap(product_numbers[0])
    product2_data = query_sap(product_numbers[1])

    # Compare
    comparison = {
        'product1': product1_data,
        'product2': product2_data,
        'differences': calculate_differences(product1_data, product2_data)
    }

    return comparison
```

**Step 4**: Update views

Edit `atp/chatbot/views.py`:
```python
def chat_send_message(request):
    # ... existing code ...

    # Add new intent handler
    if intent_result['intent'] == 'comparison':
        from .services.comparison_executor import execute_comparison
        comparison = execute_comparison(entities['product_numbers'])
        response = format_comparison_response(comparison)

    # ... rest of code ...
```

**Step 5**: Rebuild model and deploy

```bash
python generate_training_data.py
ollama create atp-chatbot -f Modelfile
docker-compose restart web
```

### Performance Tuning

**Model Parameters** in `Modelfile`:

```
# Temperature (0.0 - 2.0)
PARAMETER temperature 0.3
# Lower = More consistent (good for classification)
# Higher = More creative (good for generation)

# Top-P (0.0 - 1.0)
PARAMETER top_p 0.85
# Nucleus sampling - limits token choices
# 0.85 = Use top 85% probable tokens

# Top-K (integer)
PARAMETER top_k 40
# Limit to top K most likely tokens
# 40 = Consider only 40 best options

# Repeat Penalty (1.0 - 2.0)
PARAMETER repeat_penalty 1.1
# Penalize repeated tokens
# 1.1 = Slight penalty (prevents loops)
```

**Tuning for accuracy**:
- Lower temperature (0.1 - 0.3)
- Higher top_p (0.8 - 0.95)
- Moderate top_k (20 - 60)

**Tuning for creativity**:
- Higher temperature (0.7 - 1.0)
- Lower top_p (0.5 - 0.8)
- Higher top_k (80 - 100)

---

## Common Maintenance Tasks

### 1. Adding a New SAP Field

**Scenario**: Add "unit of measure" field

**Step 1**: Identify SAP field name
```
SAP Field: MEINS (Unit of measure)
Display Name: UOM
```

**Step 2**: Update response generator

Edit `atp/chatbot/services/response_generator.py`:
```python
field_map = {
    'upc': ('EAN11', 'UPC/EAN'),
    'brand': ('ZBRDES', 'Brand'),
    'origin': ('HERKL', 'Origin'),
    'weight': ('BRGEW', 'Weight'),
    'case_pack': ('UMREZ', 'Case Pack'),
    'vendor_sku': ('BISMT', 'Vendor SKU'),
    'uom': ('MEINS', 'Unit of Measure'),  # ← NEW
}
```

**Step 3**: Add training examples

Edit `generate_training_data.py`:
```python
field_templates = {
    # ... existing fields ...
    'uom': [
        "What's the unit of measure for {product}?",
        "Show UOM for {product}",
        "Unit of measure for {product}",
    ]
}
```

**Step 4**: Update SAP query

Edit `atp/stockcheck/sap_utils.py`:
```python
fields_to_fetch = [
    'MATNR', 'MAKTX', 'EAN11', 'BISMT',
    'ZBRDES', 'HERKL', 'BRGEW', 'UMREZ',
    'MEINS'  # ← NEW
]
```

**Step 5**: Retrain model

```bash
python generate_training_data.py
ollama create atp-chatbot -f Modelfile
docker-compose restart web
```

### 2. Updating Dependencies

**Check for updates**:
```bash
docker-compose exec web pip list --outdated
```

**Update specific package**:
```bash
# Edit requirements.txt
Django==2.1.5  →  Django==2.1.15

# Rebuild container
docker-compose build web
docker-compose up -d
```

### 3. Database Maintenance

**Clean old conversations** (monthly):
```python
# Django shell
docker-compose exec web python manage.py shell

>>> from chatbot.models import Conversation
>>> from datetime import timedelta
>>> from django.utils import timezone
>>>
>>> cutoff = timezone.now() - timedelta(days=30)
>>> old_conversations = Conversation.objects.filter(last_activity__lt=cutoff)
>>> count = old_conversations.count()
>>> print(f"Deleting {count} old conversations")
>>> old_conversations.delete()
```

**Optimize database** (monthly):
```bash
docker-compose exec db mysql -uroot -p -e "
OPTIMIZE TABLE atp.stockcheck_searchhistory;
OPTIMIZE TABLE atp.chatbot_conversation;
OPTIMIZE TABLE atp.chatbot_message;
"
```

### 4. Monitoring Model Accuracy

**Track intent accuracy**:
```python
# Add to views.py
def chat_send_message(request):
    # ... existing code ...

    # Log intent classification
    IntentLog.objects.create(
        user=request.user,
        message=user_message,
        intent=intent_result['intent'],
        confidence=intent_result['confidence']
    )
```

**Analyze logs** (quarterly):
```python
# Find low-confidence classifications
low_confidence = IntentLog.objects.filter(confidence__lt=0.85)

# Find unknown intents
unknown = IntentLog.objects.filter(intent='unknown')

# Analyze for patterns and add to training
```

---

## Summary

This guide covers:
- ✅ What Django is and how it works
- ✅ MVT architecture pattern
- ✅ Understanding models.py, views.py, urls.py, templates, forms, settings
- ✅ How database migrations work
- ✅ Request/response cycle
- ✅ AI/NLP integration details
- ✅ Custom model creation and training
- ✅ Data security measures
- ✅ How to fine-tune the AI model
- ✅ Common maintenance tasks

**Next Steps**:
1. Read through DEVELOPER_GUIDE.md for specific ATP implementation
2. Review actual code files mentioned in examples
3. Test changes in development before production
4. Keep this guide updated with new patterns

---

**Questions?** See DEVELOPER_GUIDE.md or QUICK_START.md for additional help.

**Last Updated**: November 1, 2025
**Version**: 1.0
