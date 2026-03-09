#!/usr/bin/env python
"""
Test script to verify Ollama connectivity
Run this to ensure Ollama is accessible before Django integration
"""

import requests
import json
import sys

def test_ollama_connection():
    """Test connection to Ollama from Django environment"""

    print("=" * 60)
    print("OLLAMA CONNECTION TEST")
    print("=" * 60)

    # URLs to try based on different setups
    urls_to_try = [
        'http://localhost:11434',           # Local Ollama
        'http://127.0.0.1:11434',          # Alternative localhost
        'http://host.docker.internal:11434', # From Docker container (Windows/Mac)
        'http://172.17.0.1:11434',          # From Docker container (Linux)
    ]

    working_url = None

    for url in urls_to_try:
        try:
            print(f"\nTrying {url}...")
            response = requests.get(f'{url}/api/tags', timeout=3)
            if response.status_code == 200:
                print(f"✅ SUCCESS: Connected to Ollama at {url}")
                models = response.json().get('models', [])
                if models:
                    print(f"\nAvailable models:")
                    for model in models:
                        print(f"  - {model['name']} ({model.get('size', 'unknown size')})")
                else:
                    print("⚠️  No models found. Please pull a model first:")
                    print("    ollama pull gemma2:2b")
                working_url = url
                break
        except requests.ConnectionError:
            print(f"❌ Connection failed: {url}")
        except requests.Timeout:
            print(f"❌ Timeout: {url}")
        except Exception as e:
            print(f"❌ Error: {url} - {str(e)}")

    if not working_url:
        print("\n❌ Could not connect to Ollama!")
        print("\nPlease ensure Ollama is running:")
        print("  1. Install Ollama: https://ollama.ai")
        print("  2. Start Ollama: ollama serve")
        print("  3. Pull a model: ollama pull gemma2:2b")
        return None

    return working_url

def test_model_inference(base_url):
    """Test model inference with a sample prompt"""

    print("\n" + "=" * 60)
    print("MODEL INFERENCE TEST")
    print("=" * 60)

    # Check available models first
    try:
        response = requests.get(f'{base_url}/api/tags')
        models = response.json().get('models', [])

        if not models:
            print("❌ No models available. Please pull a model first:")
            print("    ollama pull gemma2:2b")
            return False

        # Use the first available model
        model_name = models[0]['name']
        print(f"\nUsing model: {model_name}")

    except Exception as e:
        print(f"❌ Could not get model list: {e}")
        return False

    # Test intent classification
    test_prompts = [
        {
            "description": "Stock Query Test",
            "prompt": """You are an intent classifier. Classify this user query into one of these intents:
- stock_query: Checking product stock
- delivery_query: Asking about deliveries
- export_request: Requesting data export
- help: Asking for help

User query: "What's the stock of product 46888?"

Respond with ONLY the intent name."""
        },
        {
            "description": "Entity Extraction Test",
            "prompt": """Extract product numbers from this text:
"Check stock for products 12345, 67890, and 11111"

Respond with only the product numbers separated by commas."""
        }
    ]

    all_tests_passed = True

    for test in test_prompts:
        print(f"\n{test['description']}:")
        print("-" * 40)

        try:
            response = requests.post(
                f'{base_url}/api/generate',
                json={
                    'model': model_name,
                    'prompt': test['prompt'],
                    'stream': False,
                    'options': {
                        'temperature': 0.1,
                        'num_predict': 50
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()['response'].strip()
                print(f"✅ Response: {result}")

                # Validate response for first test
                if test['description'] == "Stock Query Test":
                    if 'stock' in result.lower():
                        print("   ✓ Correctly identified as stock query")
                    else:
                        print("   ⚠️  Unexpected classification")

            else:
                print(f"❌ Inference failed: {response.status_code}")
                print(f"   Error: {response.text}")
                all_tests_passed = False

        except requests.Timeout:
            print("❌ Request timed out (>30 seconds)")
            print("   This might indicate the model is too large or system is slow")
            all_tests_passed = False

        except Exception as e:
            print(f"❌ Error during inference: {e}")
            all_tests_passed = False

    return all_tests_passed

def test_performance(base_url):
    """Test response time performance"""

    print("\n" + "=" * 60)
    print("PERFORMANCE TEST")
    print("=" * 60)

    import time

    # Get model
    try:
        response = requests.get(f'{base_url}/api/tags')
        models = response.json().get('models', [])
        if not models:
            print("❌ No models available")
            return
        model_name = models[0]['name']
    except:
        print("❌ Could not get model list")
        return

    prompt = "What is 2+2?"

    print(f"\nTesting response time with model: {model_name}")
    print("Simple prompt: 'What is 2+2?'")
    print("-" * 40)

    times = []

    for i in range(3):
        start = time.time()
        try:
            response = requests.post(
                f'{base_url}/api/generate',
                json={
                    'model': model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.1,
                        'num_predict': 10
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"  Run {i+1}: {elapsed:.2f} seconds")
            else:
                print(f"  Run {i+1}: Failed")

        except Exception as e:
            print(f"  Run {i+1}: Error - {e}")

    if times:
        avg_time = sum(times) / len(times)
        print(f"\n📊 Average response time: {avg_time:.2f} seconds")

        if avg_time < 2:
            print("✅ Excellent performance for chat application")
        elif avg_time < 4:
            print("✅ Good performance, acceptable for chat")
        elif avg_time < 8:
            print("⚠️  Slow performance, consider smaller model")
        else:
            print("❌ Too slow for interactive chat")

def main():
    """Run all tests"""

    print("\n🚀 ATP CHATBOT - OLLAMA CONNECTIVITY TEST\n")

    # Test connection
    working_url = test_ollama_connection()

    if not working_url:
        print("\n❌ Cannot proceed without Ollama connection")
        sys.exit(1)

    # Test inference
    inference_ok = test_model_inference(working_url)

    if not inference_ok:
        print("\n⚠️  Some inference tests failed")
        print("This might work but could have issues")

    # Test performance
    test_performance(working_url)

    # Summary
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"\n✅ Use this configuration in Django:")
    print(f"   OLLAMA_BASE_URL = '{working_url}'")
    print(f"\n📝 Add to your .env file:")
    print(f"   OLLAMA_BASE_URL={working_url}")

    if working_url in ['http://localhost:11434', 'http://127.0.0.1:11434']:
        print("\n⚠️  Note: This URL works for local development")
        print("   For Docker deployment, you may need to use:")
        print("   - host.docker.internal:11434 (Windows/Mac)")
        print("   - Your machine's IP address (Linux)")

if __name__ == "__main__":
    main()