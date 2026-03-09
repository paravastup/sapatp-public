# Ollama Deployment Guide for ATP Chatbot

## Deployment Options

### Option 1: External Ollama (Recommended for POC)
**Your Current Setup** - Ollama running on your laptop or dedicated server

#### Advantages:
- ✅ No Docker complexity for Ollama
- ✅ Can use GPU acceleration on your laptop
- ✅ Easy to test different models
- ✅ Separate resource management
- ✅ Can be shared across multiple projects

#### Configuration:
```python
# atp/atp/settings_secure.py
# Point to your laptop's Ollama instance
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://192.168.1.100:11434')  # Your laptop IP
# Or for same machine
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
```

```yaml
# docker-compose-port5000-secure.yml
# NO Ollama container needed
services:
  web:
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434  # Access host's Ollama from Docker
      # For Linux, use actual IP instead of host.docker.internal
```

### Option 2: Ollama in Docker Container
For production deployment where everything needs to be containerized

#### Docker Configuration:
```yaml
# docker-compose-port5000-secure.yml
services:
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
    # Optional GPU support
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  web:
    depends_on:
      - ollama
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434  # Internal Docker network
```

### Option 3: Hybrid Approach
Use external Ollama for development, Docker for production

```python
# settings_secure.py
import os

# Auto-detect based on environment
if os.getenv('DJANGO_ENV') == 'production':
    OLLAMA_BASE_URL = 'http://ollama:11434'  # Docker container
else:
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')  # External
```

---

## Model Selection

### Available Gemma Models

Based on your mention of "4B parameters", here are the options:

1. **gemma2:2b** - 2 billion parameters (fastest, lowest memory)
   ```bash
   ollama pull gemma2:2b
   ```

2. **gemma2:9b** - 9 billion parameters (more accurate, more memory)
   ```bash
   ollama pull gemma2:9b
   ```

3. **gemma:7b** - Original Gemma 7B model
   ```bash
   ollama pull gemma:7b
   ```

4. **Custom quantized versions** (if you meant 4-bit quantization):
   ```bash
   ollama pull gemma2:9b-instruct-q4_0  # 4-bit quantized
   ```

### Model Comparison for Your Use Case

| Model | Size | Memory | Speed | Accuracy | Recommendation |
|-------|------|--------|-------|----------|----------------|
| gemma2:2b | 1.6GB | 3-4GB | Fast (1-2s) | Good | ✅ Best for POC |
| gemma2:9b | 5.5GB | 10-12GB | Medium (3-5s) | Excellent | For production |
| gemma2:9b-q4 | 3.8GB | 6-8GB | Fast (2-3s) | Very Good | Good balance |

---

## Setup Instructions

### Step 1: Verify Ollama is Running on Your Laptop

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Should return list of models
```

### Step 2: Pull Your Preferred Model

```bash
# If you want the smaller, faster model
ollama pull gemma2:2b

# If you want better accuracy (9B model with 4-bit quantization)
ollama pull gemma2:9b-instruct-q4_0

# Verify model is loaded
ollama list
```

### Step 3: Test Model Locally

```bash
# Quick test
curl http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Extract product numbers from: Check stock for products 12345 and 67890",
  "stream": false
}'
```

### Step 4: Configure Django Application

```python
# .env file
OLLAMA_BASE_URL=http://localhost:11434  # For local development
OLLAMA_MODEL=gemma2:2b  # Or your chosen model
```

### Step 5: Network Configuration for Docker

If Django runs in Docker but Ollama runs on host:

**For Windows/Mac Docker Desktop:**
```yaml
environment:
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**For Linux:**
```yaml
environment:
  - OLLAMA_BASE_URL=http://172.17.0.1:11434  # Docker bridge IP
```

**Or use your machine's actual IP:**
```yaml
environment:
  - OLLAMA_BASE_URL=http://192.168.1.100:11434  # Your laptop's IP
```

---

## Connection Testing

### Create a test script to verify connectivity:

```python
# test_ollama_connection.py
import requests
import json

def test_ollama_connection():
    """Test connection to Ollama from Django container"""

    # Try different URLs based on your setup
    urls_to_try = [
        'http://localhost:11434',           # Local
        'http://host.docker.internal:11434', # Docker Desktop
        'http://172.17.0.1:11434',          # Linux Docker
        'http://192.168.1.100:11434',       # Your laptop IP (update this)
    ]

    for url in urls_to_try:
        try:
            print(f"Trying {url}...")
            response = requests.get(f'{url}/api/tags', timeout=2)
            if response.status_code == 200:
                print(f"✅ SUCCESS: Connected to Ollama at {url}")
                print(f"Available models: {response.json()}")
                return url
        except Exception as e:
            print(f"❌ Failed: {url} - {str(e)}")

    print("Could not connect to Ollama")
    return None

def test_model_inference(base_url, model='gemma2:2b'):
    """Test model inference"""

    prompt = "What is the stock of product 12345?"

    response = requests.post(
        f'{base_url}/api/generate',
        json={
            'model': model,
            'prompt': prompt,
            'stream': False
        }
    )

    if response.status_code == 200:
        print(f"✅ Model inference working!")
        print(f"Response: {response.json()['response'][:100]}...")
    else:
        print(f"❌ Model inference failed: {response.text}")

if __name__ == "__main__":
    url = test_ollama_connection()
    if url:
        test_model_inference(url)
```

---

## Performance Considerations

### For POC (Laptop Deployment)
- **CPU Only**: 2-5 seconds per request
- **With GPU**: 0.5-2 seconds per request
- **Concurrent Requests**: 1-3 (laptop limitation)

### For Production (Server Deployment)
- **Dedicated Server**: 10-20 concurrent users
- **With GPU**: 50+ concurrent users
- **Load Balancing**: Multiple Ollama instances

### Memory Requirements
```bash
# Check available memory
free -h

# Monitor Ollama memory usage
docker stats ollama  # If using Docker
# Or
ps aux | grep ollama  # If running directly
```

---

## Troubleshooting

### Common Issues and Solutions

1. **Connection Refused**
   ```bash
   # Ensure Ollama is running
   systemctl status ollama  # Linux service
   # Or
   ollama serve  # Manual start
   ```

2. **Model Not Found**
   ```bash
   # Pull the model first
   ollama pull gemma2:2b
   ```

3. **Slow Response Times**
   - Check CPU/GPU usage
   - Consider smaller model or quantization
   - Add caching layer

4. **Docker Can't Connect to Host Ollama**
   ```bash
   # Check firewall isn't blocking port 11434
   # Windows: Windows Defender Firewall
   # Linux: ufw or iptables
   ```

---

## Recommended Setup for Your POC

Based on your requirements:

1. **Keep Ollama on your laptop** (already running)
2. **Use gemma2:2b for testing** (fast, efficient)
3. **Configure Django to connect externally**:

```python
# atp/atp/settings_secure.py
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma2:2b')
```

4. **Environment variable for flexibility**:
```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434  # Change to server IP when ready
OLLAMA_MODEL=gemma2:2b
```

5. **No Ollama in Docker** for now - keep it simple for POC

This approach gives you:
- ✅ Easy testing and model switching
- ✅ No Docker complexity for Ollama
- ✅ Can use your laptop's GPU if available
- ✅ Easy to migrate to server later

Ready to proceed with this setup?