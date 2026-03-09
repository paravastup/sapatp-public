#!/usr/bin/env python3
"""Test the v3 model on previously failed terminology cases"""

import subprocess
import json
import sys

def test_terminology_fixes(model_name: str = "atp-extraction-v3"):
    """Test the model on cases that previously failed due to terminology issues"""

    print(f"Testing {model_name} on terminology edge cases...")
    print("=" * 60)

    # These are the exact test cases that failed in v2
    test_cases = [
        {
            'name': 'Test 24: product code → UPC (not product number)',
            'context': 'UPC: 4154191637947 for product 10002, weight: 18.85, brand: BRAND_A',
            'query': "What's the product code?",
            'expected': {"upc": "4154191637947"},
            'v2_wrong': {"product_code": "10002"}
        },
        {
            'name': 'Test 28: EAN → UPC when context has UPC',
            'context': 'For product G3960, the UPC is 8985801984483, stock: 1921, weight: 7.49',
            'query': "I'm looking for the EAN code",
            'expected': {"upc": "8985801984483"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 31: ean (lowercase) → UPC',
            'context': 'UPC: 6844548537245 for product 40004, delivery quantity: 429, weight: 1.64, product number: 40004',
            'query': "What is the ean?",
            'expected': {"upc": "6844548537245"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 36: product code with both UPC and product number',
            'context': 'UPC: 7885064749434 for product 40068, weight: 12.10, stock: 5421',
            'query': "Show me the product code",
            'expected': {"upc": "7885064749434"},
            'v2_wrong': {"product_code": "40068"}
        },
        {
            'name': 'Test 50: EAN when UPC exists',
            'context': 'For product 00213, the UPC is 2290378536632, case pack size: 1, description: SERVING PLATTER OVAL',
            'query': "Show me the EAN",
            'expected': {"upc": "2290378536632"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 55: EAN (uppercase)',
            'context': 'Product 10002: UPC is 9402949150131, case pack size: 48, country of origin: USA, vendor: VENDOR043',
            'query': "What's the EAN?",
            'expected': {"upc": "9402949150131"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 59: EAN code',
            'context': 'For product 00213, the UPC is 9533658678271, description: DINNER PLATE 10" WHITE, vendor: VENDOR048',
            'query': "What is the EAN code?",
            'expected': {"upc": "9533658678271"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 87: ean → UPC',
            'context': 'Product G3960 has UPC 9957356082028, plant: 1003',
            'query': "Please provide the ean",
            'expected': {"upc": "9957356082028"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 91: product code with context',
            'context': 'Product 40055 - UPC: 9123426666324, country of origin: ITALY, delivery quantity: 1940, plant: 1000',
            'query': "What's the product code?",
            'expected': {"upc": "9123426666324"},
            'v2_wrong': {"product_code": "40055"}
        },
        {
            'name': 'Test 94: ean (lowercase) request',
            'context': 'UPC: 7321675898699 for product 00213, case pack size: 24, purchase order: PO-2025-626',
            'query': "I need the ean",
            'expected': {"upc": "7321675898699"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 95: EAN (uppercase) request',
            'context': 'Product 10001 has UPC 6007986284147, product number: 10001, brand: BRAND_A, vendor SKU: V-39116',
            'query': "Get the EAN",
            'expected': {"upc": "6007986284147"},
            'v2_wrong': {"ean": None}
        },
        {
            'name': 'Test 100: EAN with capitalization',
            'context': 'Product 10001 - UPC: 8143823842369, vendor: VENDOR003, weight: 18.48',
            'query': "Could you find the EAN?",
            'expected': {"upc": "8143823842369"},
            'v2_wrong': {"EAN": None}
        }
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n{test['name']}")
        print(f"Context: {test['context'][:80]}...")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")
        print(f"V2 returned (wrong): {test['v2_wrong']}")

        # Build prompt
        prompt = f"""You are a precise data extraction assistant.

CRITICAL: These terms ALL refer to the UPC/barcode field:
- product code → upc
- EAN/ean → upc
- scanning code → upc
- bar code → upc

RULES:
1. ONLY extract values that appear EXACTLY in the context
2. Return valid JSON only
3. ALL barcode-related terms map to "upc" field

Context: {test['context']}

Question: {test['query']}

Response:"""

        try:
            # Test with Ollama
            ollama_path = "/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe"
            cmd = [ollama_path, 'run', model_name, prompt]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            response = result.stdout.strip()

            # Clean and parse response
            json_str = response
            if '```' in json_str:
                parts = json_str.split('```')
                for part in parts:
                    if '{' in part and '}' in part:
                        json_str = part
                        break
                if json_str.startswith('json'):
                    json_str = json_str[4:].strip()

            # Extract JSON object
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = json_str[start:end]

            try:
                actual = json.loads(json_str)
                print(f"V3 returned: {actual}")

                if actual == test['expected']:
                    print("✅ FIXED! V3 handles this correctly")
                    passed += 1
                else:
                    print(f"❌ Still failing")
                    failed += 1

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")
                print(f"Response was: {response[:200]}")
                failed += 1

        except subprocess.TimeoutExpired:
            print("❌ Timeout")
            failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS FOR V3 MODEL:")
    print(f"✅ Fixed: {passed}/{len(test_cases)}")
    print(f"❌ Still failing: {failed}/{len(test_cases)}")
    print(f"Success rate: {passed/len(test_cases)*100:.1f}%")

    if passed == len(test_cases):
        print("\n🎉 PERFECT! All terminology issues have been resolved!")
    elif passed > failed:
        print(f"\n✨ Major improvement! {passed} cases fixed from v2 to v3")

    return passed, failed

if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else "atp-extraction-v3"
    test_terminology_fixes(model)