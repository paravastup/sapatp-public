# Chatbot Testing Guide

## Prerequisites

1. **Ollama must be running** on your laptop/host machine:
   ```bash
   ollama serve
   ```

2. **Gemma3:4b model must be loaded**:
   ```bash
   ollama pull gemma3:4b
   ```

---

## Testing Steps

### Step 1: Test Ollama Connection (Outside Django)

```bash
# Run the standalone test script
python3 test_ollama_connection.py
```

This will verify:
- Ollama is accessible at http://localhost:11434
- Gemma3:4b model is available
- Response time is acceptable (<4 seconds)

### Step 2: Run Migrations for Chatbot Models

Since the Django app is in Docker, run migrations there:

```bash
# Option 1: If Docker is running
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py makemigrations chatbot
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py migrate

# Option 2: Start Docker first, then run migrations
docker-compose -f docker-compose-port5000-secure.yml up -d
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py makemigrations chatbot
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py migrate
```

### Step 3: Test Chatbot Backend Services

```bash
# Test all services
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot

# Test specific components
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --test ollama
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --test intent
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --test entity
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --test response
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --test conversation
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --test sap

# Test a specific query
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py test_chatbot --query "What's the stock of product 10001?"
```

### Step 4: Run Full Backend Test Suite

```bash
# This runs outside Docker and tests everything
python3 test_chatbot_backend.py
```

---

## Expected Test Results

### ✅ Successful Test Output

```
============================================================
TEST 1: OLLAMA CONNECTION
============================================================
✅ Ollama connection successful
✅ Generation test: Hello World...

TEST 2: INTENT CLASSIFICATION
----------------------------------------
✅ Query: 'What's the stock of product 10001?...'
   Expected: stock_query, Got: stock_query (confidence: 0.90)
✅ Query: 'When is the next delivery?...'
   Expected: delivery_query, Got: delivery_query (confidence: 0.85)

Accuracy: 100.0%

TEST 3: ENTITY EXTRACTION
----------------------------------------
✅ Query: 'Check stock for products 12345, 67890'
   Extracted: {'product_numbers': ['12345', '67890']}

TEST 4: RESPONSE GENERATION
----------------------------------------
✅ greeting: Hello there!...
✅ help: I can help you with...
✅ stock_query: Product **10001** has **150** pieces in stock...

TEST 5: CONVERSATION FLOW
----------------------------------------
✅ Created session: 1
👤 User: Hello
🤖 Bot: Hello! How can I help you check product availability today?
   Intent: greeting (0.90)

✅ Conversation completed with 6 messages

TEST 6: SAP INTEGRATION
----------------------------------------
⚠️ SAP not available: Connection error
   This is normal if SAP is not connected
```

---

## Troubleshooting

### Issue: "Ollama connection failed"

**Solution:**
1. Make sure Ollama is running: `ollama serve`
2. Check if it's accessible: `curl http://localhost:11434/api/tags`
3. If in Docker, update `.env`:
   ```
   OLLAMA_BASE_URL=http://host.docker.internal:11434  # Windows/Mac
   OLLAMA_BASE_URL=http://172.17.0.1:11434           # Linux
   ```

### Issue: "No module named 'chatbot'"

**Solution:**
1. Make sure `chatbot` is added to `INSTALLED_APPS` in settings
2. Restart Django/Docker after adding the app

### Issue: "Table 'chatbot_chatsession' doesn't exist"

**Solution:**
Run migrations:
```bash
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py migrate
```

### Issue: "SAP integration not available"

**Solution:**
This is normal if SAP is not connected. The chatbot will still work with mock data for testing.

### Issue: Slow response times

**Solution:**
1. Check Ollama performance: `ollama ps`
2. Consider using a smaller model if needed
3. Ensure sufficient RAM (8GB+ recommended)

---

## Testing Without Docker

If you want to test without Docker (requires Python 3.6 environment):

```bash
# Install dependencies
pip install django==2.1.5 requests

# Set environment variables
export DJANGO_SETTINGS_MODULE=atp.settings_secure
export PYTHONPATH=/mnt/d/demoproject/atp:$PYTHONPATH

# Run tests
cd /mnt/d/demoproject/atp
python manage.py test_chatbot
```

---

## Next Steps After Testing

Once all tests pass:

1. **Create Chat UI**: Build the frontend interface
2. **Add Views/URLs**: Create API endpoints for the chat
3. **Integration Testing**: Test with real SAP data
4. **Performance Tuning**: Optimize response times
5. **User Testing**: Get feedback from actual users

---

## Quick Test Commands

```bash
# 1. Check Ollama
curl http://localhost:11434/api/tags

# 2. Test intent classification
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"gemma3:4b","prompt":"Classify intent: What is the stock of 10001?","stream":false}'

# 3. Quick Django test (if Docker is running)
docker-compose -f docker-compose-port5000-secure.yml exec web python -c "from chatbot.services.ollama_client import OllamaClient; print(OllamaClient().test_connection())"
```

---

## Success Criteria

The chatbot backend is ready when:

✅ Ollama connection works
✅ Intent classification accuracy > 80%
✅ Entity extraction works for product numbers
✅ Response generation produces natural language
✅ Conversation flow maintains context
✅ Database models are migrated
✅ All tests pass without errors

---

*Last Updated: November 2024*