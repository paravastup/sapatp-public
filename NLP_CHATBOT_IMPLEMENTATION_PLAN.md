# NLP Conversational Search Implementation Plan
## ATP SAP Middleware Transformation

### Project Information
- **Project Name**: ATP Conversational AI Search
- **Start Date**: November 2024
- **Technology Stack**: Django 2.1.5, Python 3.6, Ollama, Gemma 3
- **Project Lead**: Development Team
- **Status**: Planning Phase

---

## 1. EXECUTIVE SUMMARY

### 1.1 Vision Statement
Transform the ATP SAP middleware application from a complex dropdown-based search interface into an intuitive, conversational AI assistant that allows users to interact naturally using plain language queries.

### 1.2 Key Objectives
- Replace multi-dropdown search with single conversational input
- Enable natural language queries for stock, delivery, and product information
- Maintain 100% backward compatibility
- Achieve <4 second response time
- Support multi-plant users with conversational plant selection
- Enable export via conversation (Excel, Email, PDF)

### 1.3 Success Metrics
- 80%+ intent classification accuracy
- 70%+ user adoption rate within 2 months
- <4 second average response time
- 99%+ uptime
- 4+ star user satisfaction rating

---

## 2. TECHNICAL ARCHITECTURE

### 2.1 System Overview
```
User Input (Natural Language)
    ↓
Django Chat Interface
    ↓
Ollama API (Gemma 3 Model)
    ↓
Intent Classification & Entity Extraction
    ↓
Query Executor (SAP Integration)
    ↓
Response Generator
    ↓
Conversational Response + Data Display
```

### 2.2 Technology Components

#### Core Technologies
- **LLM Runtime**: Ollama (local deployment)
- **Language Model**: Gemma 3:2B or 3:7B
- **Framework**: Django 2.1.5 (existing)
- **Database**: MySQL 5.7 (existing)
- **SAP Integration**: pyrfc 1.9.93 (existing)

#### New Dependencies
```python
# requirements.txt additions
requests==2.31.0      # Ollama API communication
python-dateutil==2.8.2  # Date parsing
channels==2.4.0       # Optional: WebSocket support
```

### 2.3 Model Selection
- **Primary Model**: Gemma 3:2B (2 billion parameters)
  - Lightweight and fast
  - 2-4GB memory requirement
  - Good for intent classification

- **Alternative**: Gemma 3:7B (7 billion parameters)
  - Better reasoning capabilities
  - 8-16GB memory requirement
  - Higher accuracy but slower

---

## 3. IMPLEMENTATION PHASES

### PHASE 1: Infrastructure Setup (Days 1-2)

#### 1.1 Ollama Installation
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Gemma 3 model
ollama pull gemma3:2b

# Test model
ollama run gemma3:2b "Hello, test response"
```

#### 1.2 Django App Creation
```bash
cd /opt/app/atp
python manage.py startapp chatbot
```

#### 1.3 Database Models
```python
# chatbot/models.py
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    context = models.JSONField(default=dict)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # 'user' or 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
```

#### 1.4 Docker Configuration
```yaml
# docker-compose addition
ollama:
  image: ollama/ollama:latest
  container_name: atp_ollama
  volumes:
    - ollama_data:/root/.ollama
  ports:
    - "11434:11434"
  environment:
    - OLLAMA_HOST=0.0.0.0
  restart: unless-stopped
```

### PHASE 2: Core LLM Integration (Days 3-5)

#### 2.1 Ollama Client Implementation
```python
# chatbot/services/ollama_client.py
import requests
from django.conf import settings

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = 'gemma3:2b'

    def generate(self, prompt, system_prompt=None, temperature=0.3):
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': temperature}
        }
        if system_prompt:
            payload['system'] = system_prompt

        response = requests.post(
            f'{self.base_url}/api/generate',
            json=payload,
            timeout=30
        )
        return response.json()['response']
```

#### 2.2 Intent Classification
Intent types to support:
1. **stock_query** - Check product stock levels
2. **delivery_query** - Check delivery dates/quantities
3. **product_info** - Get product details (brand, origin, specs)
4. **plant_selection** - Select or change plant
5. **export_request** - Export results (Excel/Email/PDF)
6. **comparison** - Compare multiple products
7. **help** - Get help or instructions
8. **greeting** - Greetings and small talk
9. **clarification_needed** - Ambiguous query

#### 2.3 Entity Extraction
Entities to extract:
- Product numbers (4-8 digits)
- Vendor SKUs (format: ABC-123)
- Plant codes/names
- Date references
- Export formats
- Quantity terms

### PHASE 3: Query Integration (Days 6-8)

#### 3.1 SAP Query Executor
```python
# chatbot/services/query_executor.py
from stockcheck.views import stock_info

class QueryExecutor:
    def execute_search(self, plant_code, product_numbers, mode):
        results = []
        for product in product_numbers:
            try:
                data = stock_info(plant_code, product.upper(), mode)
                results.append(data)
            except Exception as e:
                results.append({
                    'MATNR': product,
                    'error': 'Product not found'
                })
        return results
```

#### 3.2 Response Generation
Generate natural language responses based on:
- User query intent
- Retrieved SAP data
- Conversation context
- User preferences

### PHASE 4: User Interface (Days 9-11)

#### 4.1 Chat Interface Design
- Single text input field
- Message bubbles (user/assistant)
- Results panel for data tables
- Export action buttons
- Typing indicators
- Quick action buttons

#### 4.2 Real-time Updates
- AJAX for message sending
- WebSocket for real-time responses (optional)
- Progressive loading for large datasets

#### 4.3 Mobile Responsiveness
- Responsive Bootstrap layout
- Touch-friendly interface
- Optimized for small screens

### PHASE 5: Advanced Features (Days 12-14)

#### 5.1 Multi-turn Conversations
- Context persistence
- Conversation history
- Follow-up questions
- Clarification handling

#### 5.2 Plant Selection Logic
```python
# For multi-plant users
if user.plant.count() > 1 and not context.get('selected_plant'):
    # Ask user to select plant
    return prompt_plant_selection()
```

#### 5.3 Export Integration
- Excel generation (existing xlwt)
- Email delivery (existing SMTP)
- PDF generation (new feature)

### PHASE 6: Testing & Optimization (Days 15-17)

#### 6.1 Testing Strategy
- Unit tests for each service
- Integration tests for full flow
- Load testing for Ollama
- User acceptance testing

#### 6.2 Performance Optimization
- Response caching
- Query optimization
- Prompt engineering
- Model fine-tuning (optional)

#### 6.3 Security Hardening
- Input sanitization
- Rate limiting
- SQL injection prevention
- XSS protection

### PHASE 7: Deployment (Days 18-20)

#### 7.1 Deployment Steps
1. Backup existing system
2. Deploy Ollama container
3. Run database migrations
4. Deploy Django changes
5. Test in staging
6. Progressive rollout

#### 7.2 Monitoring Setup
- Response time tracking
- Error rate monitoring
- Intent classification accuracy
- User satisfaction metrics

---

## 4. PROMPT ENGINEERING

### 4.1 Intent Classification Prompt
```
You are an intent classifier for a product availability system.

Classify the user query into ONE of these intents:
- stock_query: Checking product stock levels
- delivery_query: Asking about deliveries
- product_info: Product details
- plant_selection: Selecting plant
- export_request: Export data
- comparison: Compare products
- help: Need help
- greeting: Greetings
- clarification_needed: Unclear

Examples:
"What's the stock of 10001?" → stock_query
"When is next delivery?" → delivery_query
"Send me Excel file" → export_request

Query: [USER_QUERY]
Intent:
```

### 4.2 Entity Extraction Prompt
```
Extract entities from the user query.

Look for:
- product_numbers: 4-8 digit numbers
- vendor_skus: Format like "ABC-123"
- plant_code: 4-digit codes
- export_format: excel/email/pdf

Query: [USER_QUERY]
Entities (JSON):
```

### 4.3 Response Generation Prompt
```
You are a helpful product availability assistant.

Guidelines:
- Be conversational and friendly
- Keep responses concise (<100 words)
- Use bullet points for multiple items
- Highlight important numbers with **bold**

User asked: [QUERY]
Data: [SAP_DATA]

Generate response:
```

---

## 5. QUERY EXAMPLES

### 5.1 Supported Query Types

#### Stock Queries
- "What's the stock of product 10001?"
- "Check availability for SKU 123456"
- "How much inventory for 111, 222, 333?"
- "Show stock for vendor SKU OLD-123"

#### Delivery Queries
- "When is the next delivery for 10001?"
- "What's coming in next week?"
- "Check in-transit quantity for 123"
- "Delivery schedule for product 456"

#### Product Information
- "What's the brand of 10001?"
- "Where is product 123 manufactured?"
- "Case pack for SKU 789?"
- "Get UPC code for 456"

#### Comparisons
- "Compare stock for 111, 222, 333"
- "Which products have negative stock?"
- "Show all on-demand items"
- "List products with deliveries"

#### Export Requests
- "Email me these results"
- "Download as Excel"
- "Export to PDF"
- "Send report to my email"

---

## 6. FALLBACK MECHANISMS

### 6.1 When Ollama is Unavailable
```python
if not ollama_available:
    # Use regex-based extraction
    entities = extract_with_regex(query)
    intent = classify_with_rules(query)
```

### 6.2 Low Confidence Handling
```python
if confidence < 0.6:
    # Ask for clarification
    return "Could you clarify if you want to:
            1. Check stock levels
            2. See delivery dates
            3. Export data
            4. Something else?"
```

### 6.3 Error Recovery
- Graceful error messages
- Retry logic for timeouts
- Fallback to classic search
- Admin notifications

---

## 7. MIGRATION STRATEGY

### 7.1 Phased Rollout
1. **Week 1**: Deploy as "Beta" feature
2. **Week 2**: Pilot with 10% users
3. **Week 3**: Expand to 50% users
4. **Week 4**: Make default for all
5. **Week 5+**: Deprecate old interface

### 7.2 User Training
- In-app tooltips
- Sample queries displayed
- Help documentation
- Video tutorials

### 7.3 Backward Compatibility
- Keep classic search available
- Feature flag for enabling/disabling
- Gradual migration path
- Data export from old format

---

## 8. RISK ASSESSMENT

### 8.1 Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Ollama performance issues | Medium | High | GPU acceleration, caching |
| Low intent accuracy | Medium | Medium | Prompt refinement, fallbacks |
| SAP integration failures | Low | High | Existing error handling |
| User adoption resistance | Medium | Medium | Training, gradual rollout |

### 8.2 Security Risks
- Input injection attacks → Input sanitization
- Rate limiting abuse → Request throttling
- Data exposure → Access controls
- Model hallucinations → Validation layer

---

## 9. RESOURCE REQUIREMENTS

### 9.1 Hardware
- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **Optimal**: 32GB RAM, GPU support

### 9.2 Time Estimate
- **Total Duration**: 20 working days
- **Development**: 15 days
- **Testing**: 3 days
- **Deployment**: 2 days

### 9.3 Team Requirements
- Django developer (primary)
- UI/UX designer (part-time)
- QA tester (final phase)
- DevOps engineer (deployment)

---

## 10. SUCCESS CRITERIA

### 10.1 Technical Metrics
- [ ] 80%+ intent classification accuracy
- [ ] <4 second response time (95th percentile)
- [ ] 99%+ uptime
- [ ] Zero data loss
- [ ] 100% SAP query success rate

### 10.2 User Metrics
- [ ] 70%+ adoption rate
- [ ] 4+ star satisfaction rating
- [ ] 50%+ reduction in support tickets
- [ ] 30%+ increase in search usage

### 10.3 Business Metrics
- [ ] 20% faster task completion
- [ ] Reduced training time for new users
- [ ] Improved data accessibility
- [ ] Enhanced decision-making speed

---

## APPENDIX A: File Structure

```
atp/
├── chatbot/                    # New Django app
│   ├── models.py              # Chat models
│   ├── views.py               # Chat views
│   ├── forms.py               # Simple chat form
│   ├── urls.py                # Chat URLs
│   ├── admin.py               # Admin interface
│   ├── services/              # Business logic
│   │   ├── ollama_client.py  # LLM integration
│   │   ├── intent_classifier.py
│   │   ├── entity_extractor.py
│   │   ├── query_executor.py
│   │   ├── response_generator.py
│   │   └── conversation_manager.py
│   ├── prompts/               # Prompt templates
│   │   ├── system_prompt.py
│   │   ├── intent_prompts.py
│   │   └── response_prompts.py
│   ├── templates/chatbot/     # UI templates
│   │   ├── chat.html
│   │   └── chat_widget.html
│   ├── static/chatbot/        # Frontend assets
│   │   ├── css/chat.css
│   │   └── js/chat.js
│   └── tests/                 # Test suite
│       ├── test_intent.py
│       ├── test_entity.py
│       └── test_integration.py
```

---

## APPENDIX B: Configuration

### Django Settings
```python
# settings_secure.py additions
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma3:2b')
CHAT_INTERFACE_ENABLED = os.getenv('CHAT_INTERFACE_ENABLED', 'True') == 'True'
CHAT_RATE_LIMIT = int(os.getenv('CHAT_RATE_LIMIT', '30'))  # per minute
```

### Environment Variables
```bash
# .env additions
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=gemma3:2b
CHAT_INTERFACE_ENABLED=True
CHAT_RATE_LIMIT=30
```

---

*Document Version: 1.0*
*Last Updated: November 2024*
*Status: Ready for Implementation*