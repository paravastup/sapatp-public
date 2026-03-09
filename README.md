# ATP - SAP Product Availability Middleware

ATP (Available to Promise) is a Django web application that provides real-time product availability checking from SAP systems. It offers two interfaces: a traditional form-based search and an AI-powered conversational chatbot built with a custom-trained LLM and RAG (Retrieval Augmented Generation).

## Architecture

```
                         +------------------+
                         |    Browser       |
                         |  (Port 5000)     |
                         +--------+---------+
                                  |
                         +--------+---------+
                         |     Nginx        |
                         | (Reverse Proxy)  |
                         +--------+---------+
                                  |
                         +--------+---------+
                         |  Django + Gunicorn|
                         |  (Python 3.6)    |
                         +---+----------+---+
                             |          |
              +--------------+          +--------------+
              |                                        |
     +--------+--------+                    +----------+---------+
     |  Stock Check    |                    |   AI Chatbot       |
     |  (Form Search)  |                    |  (NLP Interface)   |
     +--------+--------+                    +----+----------+----+
              |                                  |          |
     +--------+--------+              +---------++    +-----+-------+
     |   SAP System    |              |  Ollama  |    | FAISS Index |
     |  (RFC/BAPI)     |              | (LLM)   |    | (RAG)       |
     +-----------------+              +----------+    +-------------+
              |
     +--------+--------+
     |     MySQL       |
     | (Users, History)|
     +-----------------+
```

## Tech Stack

- **Backend**: Django 2.1.5, Python 3.6, Gunicorn
- **Database**: MySQL 5.7, Redis (caching)
- **SAP Integration**: pyrfc 1.9.93 (NetWeaver RFC SDK)
- **AI/ML**: Ollama (Gemma 3 4B, custom-trained), FAISS (vector search)
- **Frontend**: Bootstrap 4.1.3, jQuery 3.3.1, DataTables
- **Infrastructure**: Docker, Docker Compose, Nginx

## Features

### Traditional Search
- Multi-product search by SKU (comma-separated)
- Multi-plant support across manufacturing locations
- Real-time SAP RFC calls for stock levels, delivery schedules, product details
- Excel/CSV export of results
- Search history tracking

### AI Chatbot
- Natural language queries ("What's the stock of product 10001?")
- Context-aware conversations (remembers last 10 products)
- Follow-up handling ("What's the UPC?" references previous product)
- Action repeat ("Do the same with 10002")
- Intent classification and entity extraction via custom-trained model
- Product catalog search via RAG pipeline
- Export results via email or Excel

## Prerequisites

- Docker and Docker Compose
- Ollama installed on the host machine with the `atp-chatbot` model
- SAP system access with valid credentials and network connectivity
- SAP NetWeaver RFC SDK (`nwrfcsdk/` directory - not included, obtain from SAP)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url> && cd sapatp-public
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database passwords, SAP credentials, and Ollama host IP
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Wait ~30 seconds** for MySQL initialization, then access:
   - Home: http://localhost:5000/
   - AI Chat: http://localhost:5000/atp/chat/
   - Admin: http://localhost:5000/atp/admin/

## Configuration

All sensitive configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

| Variable | Description |
|----------|-------------|
| `DATABASE_PASSWORD` | MySQL password for the Django user |
| `MYSQL_ROOT_PASSWORD` | MySQL root password |
| `DJANGO_SECRET_KEY` | Django secret key (generate a new one for production) |
| `OLLAMA_BASE_URL` | URL to Ollama instance (e.g., `http://192.168.1.100:11434`) |
| `OLLAMA_MODEL` | Model name (default: `gemma3:4b`) |

SAP connection is configured in `atp/atp/settings_secure.py` via environment variables.

## Project Structure

```
sapatp-public/
├── atp/                              # Django project root
│   ├── atp/                          # Project settings
│   │   ├── settings.py               # Base settings
│   │   ├── settings_secure.py        # Production settings (env vars)
│   │   ├── urls.py                   # URL routing
│   │   └── wsgi.py                   # WSGI entry point
│   │
│   ├── stockcheck/                   # SAP stock check app
│   │   ├── models.py                 # User, Plant, Profile, SearchHistory
│   │   ├── views.py                  # Search views and SAP queries
│   │   ├── forms.py                  # Product search forms
│   │   ├── sap_connector.py          # SAP RFC connection layer
│   │   └── validators.py             # Input validation
│   │
│   ├── chatbot/                      # AI chatbot app
│   │   ├── models.py                 # Conversation, Message, ExportNotification
│   │   ├── views.py                  # Chat API endpoints
│   │   └── services/                 # Business logic layer
│   │       ├── intent_classifier.py  # NLP intent classification
│   │       ├── entity_extractor.py   # Entity extraction (products, plants)
│   │       ├── ollama_client.py      # Ollama LLM integration
│   │       ├── conversation_manager.py
│   │       ├── query_executor.py     # Execute SAP queries from chat
│   │       ├── response_generator.py # Format responses
│   │       ├── rag_indexer.py        # Build FAISS product index
│   │       ├── rag_retriever.py      # Vector similarity search
│   │       └── response_generator_rag.py  # RAG-augmented responses
│   │
│   ├── products/                     # Product catalog app
│   │   ├── models.py                 # Product, Brand, Category models
│   │   ├── services.py               # Product data service
│   │   └── tasks.py                  # Feed import tasks
│   │
│   ├── docs/                         # Help/documentation app
│   ├── templates/                    # HTML templates
│   ├── static/                       # CSS, JS, images
│   ├── Modelfile                     # Ollama model definition (618 examples)
│   ├── generate_training_data.py     # Training data generator
│   └── atp_training_dataset.json     # Complete training dataset
│
├── scripts/                          # ML training & validation scripts
├── training_data/                    # Training datasets (JSONL)
├── Modelfile.*                       # Model definition variants
│
├── docker-compose.yml                # Docker services configuration
├── Dockerfile                        # Web container image
├── nginx.conf                        # Nginx reverse proxy config
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
└── pyrfc-1.9.93-*.whl               # SAP RFC Python wheel
```

## AI/ML Architecture

The chatbot uses a multi-layer AI pipeline combining a custom-trained LLM with RAG for accurate, context-aware responses.

### Model Selection

We use **Google Gemma 3 4B** via Ollama. After evaluating 4B vs 12B variants, we chose 4B for its balance of speed (10-15s responses) and accuracy for our domain-specific task. See [GEMMA3_MODEL_ANALYSIS.md](GEMMA3_MODEL_ANALYSIS.md) for the full comparison.

### Training Pipeline

1. **Training data generation** (`atp/generate_training_data.py`): Programmatically generates 618 domain-specific examples covering stock queries, product info, delivery schedules, follow-ups, and action repeats.

2. **Model definition** (`atp/Modelfile`): Defines the system prompt with intent categories, entity types, SAP field mappings, and all 618 examples as few-shot learning context.

3. **Anti-hallucination training** (`scripts/generate_extraction_training.py`): Generates 15,000+ extraction examples that teach the model to extract exact values from SAP data rather than generating/guessing values.

See [CUSTOM_MODEL_TRAINING_GUIDE.md](CUSTOM_MODEL_TRAINING_GUIDE.md) for the full training approach and [TRAINING_RESULTS.md](TRAINING_RESULTS.md) for accuracy metrics.

### RAG Pipeline

The RAG system provides product catalog context to the chatbot:

1. **Indexing** (`rag_indexer.py`): Product data from the XML feed is converted to text, embedded using `nomic-embed-text` (768 dimensions), and stored in a FAISS index.

2. **Retrieval** (`rag_retriever.py`): User queries are embedded and matched against the FAISS index using vector similarity search to find relevant products.

3. **Generation** (`response_generator_rag.py`): Retrieved product context is injected into the LLM prompt, grounding responses in real catalog data. Falls back to non-RAG mode if the index is unavailable.

### Intent Classification Flow

```
User message
    |
    v
Intent Classifier --> stock_check | product_info | delivery | plant_selection | export | comparison | help
    |
    v
Entity Extractor --> product_numbers, plant_codes, field_names, date_ranges
    |
    v
Query Executor --> SAP RFC calls (BAPI_MATERIAL_AVAILABILITY, etc.)
    |
    v
Response Generator --> Formatted natural language response
```

## Application URLs

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/atp/search/` | Traditional product search |
| `/atp/chat/` | AI chatbot interface |
| `/atp/admin/` | Django admin panel |
| `/atp/login/` | User login |

## Common Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f web

# Django shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Build product index for RAG
docker-compose exec web python manage.py build_product_index

# Rebuild (after code changes)
docker-compose build web && docker-compose up -d
```

## Security

- All secrets are managed via environment variables (`.env`)
- Input validation on all user-facing forms
- Django ORM prevents SQL injection
- CSRF protection on all forms
- XSS protection via auto-escaping and security headers
- Session security with HTTP-only cookies and 1-hour timeout
- Non-root container user in production

**Important**: Change all default passwords in `.env` before deploying to production. Generate a new `DJANGO_SECRET_KEY`.

## Documentation

| Document | Description |
|----------|-------------|
| [DEPLOY.md](DEPLOY.md) | Deployment guide |
| [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) | Setup reference |
| [CODEBASE_OVERVIEW.md](CODEBASE_OVERVIEW.md) | Technical overview |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Developer reference |
| [GEMMA3_MODEL_ANALYSIS.md](GEMMA3_MODEL_ANALYSIS.md) | Model selection analysis |
| [CUSTOM_MODEL_TRAINING_GUIDE.md](CUSTOM_MODEL_TRAINING_GUIDE.md) | Training approach |
| [TRAINING_RESULTS.md](TRAINING_RESULTS.md) | Training accuracy results |
| [NLP_CHATBOT_IMPLEMENTATION_PLAN.md](NLP_CHATBOT_IMPLEMENTATION_PLAN.md) | Chatbot implementation plan |
| [OLLAMA_DEPLOYMENT_GUIDE.md](OLLAMA_DEPLOYMENT_GUIDE.md) | Ollama setup guide |

## License

Proprietary - Internal Use Only
