#!/usr/bin/env python3
"""
Test the atp-extraction-v4 model directly
"""

import subprocess
import json

def test_model():
    """Test the v4 model with various queries"""

    test_cases = [
        {
            "name": "Product with UPC",
            "query": "Context: Product 10002 has UPC 10026102100020. Question: What's the UPC?"
        },
        {
            "name": "Product without UPC",
            "query": "Context: Product 10001, brand BRAND_B. Question: What's the UPC?"
        },
        {
            "name": "EAN terminology",
            "query": "Context: Item has EAN 8899556677001. Question: What's the barcode?"
        },
        {
            "name": "Original problematic case",
            "query": "Context: Product information from SAP. Product 10001. Question: What is the UPC?"
        }
    ]

    print("="*60)
    print("🧪 Testing atp-extraction-v4 Model")
    print("="*60)

    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Query: {test['query'][:60]}...")

        # Call Ollama with the v4 model
        full_prompt = f"User: {test['query']}\nAssistant:"

        cmd = [
            '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
            'run',
            'atp-extraction-v4',
            full_prompt
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            response = result.stdout.strip()

            print(f"   Response: {response[:100]}")

            # Check for JSON structure
            if response.startswith('{'):
                try:
                    parsed = json.loads(response.split('\n')[0])
                    print(f"   ✅ Valid JSON: {parsed}")
                except:
                    print(f"   ⚠️ Invalid JSON structure")

            # Check for hallucination patterns
            if any(pattern in response for pattern in ["10026", "79461", "8894"]):
                print("   ⚠️ WARNING: Old hallucination pattern detected!")

        except subprocess.TimeoutExpired:
            print("   ❌ Timeout - model took too long")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)

if __name__ == "__main__":
    test_model()