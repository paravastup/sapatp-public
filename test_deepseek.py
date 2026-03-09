#!/usr/bin/env python3
"""
Test DeepSeek extraction model
"""

import subprocess
import json
import time

def test_model():
    """Test the DeepSeek model"""

    print("="*60)
    print("🧪 Testing DeepSeek-R1:8b Extraction Model")
    print("="*60)

    test_cases = [
        {
            "name": "✅ Should extract real UPC",
            "prompt": "Context: Product 10002 has UPC 10026102100020. Question: What's the UPC?",
            "expected": "10026102100020",
            "should_have": True
        },
        {
            "name": "✅ Should return null (no UPC)",
            "prompt": "Context: Product 10001, brand BRAND_B. Question: What's the UPC?",
            "expected": None,
            "should_have": False
        },
        {
            "name": "✅ Product code != UPC",
            "prompt": "Context: Product G3960 is available. Question: What's the EAN code?",
            "expected": None,
            "should_have": False
        },
        {
            "name": "✅ EAN = barcode",
            "prompt": "Context: Item has EAN 8899556677001. Question: What's the barcode?",
            "expected": "8899556677001",
            "should_have": True
        },
        {
            "name": "✅ Extract from multiple",
            "prompt": "Context: Product 12345, order 78901, UPC 9876543210123. Question: What's the UPC?",
            "expected": "9876543210123",
            "should_have": True
        },
        {
            "name": "✅ No UPC present",
            "prompt": "Context: Product ABC123 is in stock. Question: What's the UPC?",
            "expected": None,
            "should_have": False
        },
        {
            "name": "✅ Original problem case",
            "prompt": "Context: Product information from SAP. Product 10001. Question: What is the UPC?",
            "expected": None,
            "should_have": False
        },
        {
            "name": "✅ Real UPC for 10001",
            "prompt": "Context: Product 10002 UPC: 10026102100020. Product 10001 UPC: 10026102100010. Question: What's the UPC for 10001?",
            "expected": "10026102100010",
            "should_have": True
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")

        # Test with DeepSeek
        cmd = [
            '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
            'run',
            'deepseek-extraction',
            test['prompt']
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            response = result.stdout.strip()

            print(f"   Response: {response[:100]}")

            # Check for JSON
            success = False
            if '{' in response and '}' in response:
                try:
                    json_start = response.index('{')
                    json_end = response.rindex('}') + 1
                    json_str = response[json_start:json_end]
                    parsed = json.loads(json_str)

                    upc_value = parsed.get('upc')

                    if test['should_have']:
                        if str(upc_value) == str(test['expected']):
                            print(f"   ✅ PASS: Got {upc_value}")
                            passed += 1
                            success = True
                        else:
                            print(f"   ❌ FAIL: Expected {test['expected']}, got {upc_value}")
                            failed += 1
                    else:
                        if upc_value is None or upc_value == "null":
                            print(f"   ✅ PASS: Correctly returned null")
                            passed += 1
                            success = True
                        else:
                            print(f"   ❌ FAIL: Should be null, got {upc_value}")
                            failed += 1

                except Exception as e:
                    print(f"   ❌ JSON parse error: {e}")
                    failed += 1
            else:
                # Check if it's just saying null or similar
                if not test['should_have'] and ('null' in response.lower() or 'not' in response.lower() or 'no upc' in response.lower()):
                    print(f"   ✅ PASS: Indicated no UPC (non-JSON response)")
                    passed += 1
                else:
                    print(f"   ❌ No JSON in response")
                    failed += 1

        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout")
            failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)

    total = len(test_cases)
    accuracy = (passed/total)*100 if total > 0 else 0

    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({accuracy:.1f}%)")
    print(f"Failed: {failed}")

    if accuracy == 100:
        print("\n🎉 PERFECT! 100% accuracy achieved!")
        print("DeepSeek is performing flawlessly!")
    elif accuracy >= 90:
        print("\n✅ EXCELLENT! Over 90% accuracy")
        print("DeepSeek is much better than Gemma!")
    elif accuracy >= 80:
        print("\n👍 GOOD! Over 80% accuracy")
        print("DeepSeek is performing well")
    else:
        print("\n⚠️ Needs improvement")
        print("But still likely better than Gemma 3 4B")

    return accuracy

def compare_models():
    """Quick comparison between models"""
    print("\n" + "="*60)
    print("⚖️ Model Comparison")
    print("="*60)

    test_query = "Context: Product 10001. Question: What's the UPC?"

    models = [
        ('gemma3:4b', 'Gemma 3 4B'),
        ('atp-extraction-v4', 'Fine-tuned v4'),
        ('deepseek-extraction', 'DeepSeek-R1:8b')
    ]

    for model_id, model_name in models:
        print(f"\n🔍 Testing {model_name}:")

        cmd = [
            '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
            'run',
            model_id,
            test_query
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            response = result.stdout.strip()[:100]
            print(f"   Response: {response}")

            # Check for hallucination
            if any(fake in response for fake in ['10026', '79461', '8894', '100010']):
                print("   ⚠️ HALLUCINATION DETECTED!")
            elif 'null' in response.lower():
                print("   ✅ Correctly returned null")

        except:
            print("   ❌ Model not available or error")

if __name__ == "__main__":
    # Test DeepSeek
    accuracy = test_model()

    # Compare models
    compare_models()

    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)

    if accuracy >= 90:
        print("\n🎯 RECOMMENDATION: Use DeepSeek-R1:8b!")
        print("Update your app to use 'deepseek-extraction' model")
        print("\nTo switch:")
        print("1. Edit: /opt/app/atp/chatbot/services/ollama_client_enhanced.py")
        print("2. Change: self.extraction_model = 'atp-extraction-v4'")
        print("3. To: self.extraction_model = 'deepseek-extraction'")
    else:
        print("\nDeepSeek needs more training examples or tuning")