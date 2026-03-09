#!/usr/bin/env python3
"""Comprehensive test for v4 model - checks both terminology and hallucination"""

import subprocess
import json

def test_v4_model():
    """Test v4 model on both hallucination and terminology cases"""

    print("Testing atp-extraction-v4 model")
    print("=" * 60)

    # Test cases that v3 failed (hallucination)
    hallucination_tests = [
        {
            'name': 'No UPC - should not return product number',
            'context': 'Product 10001, weight: 19.98, country of origin: USA',
            'query': "What's the upc?",
            'expected': {"upc": None}
        },
        {
            'name': 'Product number is not UPC',
            'context': 'Product 10002, stock: 6217, description: SOUP BOWL CERAMIC',
            'query': "I'm looking for the upc",
            'expected': {"upc": None}
        },
        {
            'name': 'No barcode means null',
            'context': 'Product 10001, delivery quantity: 4330, product number: 10001',
            'query': "Can you tell me the UPC code?",
            'expected': {"upc": None}
        }
    ]

    # Terminology mapping tests
    terminology_tests = [
        {
            'name': 'Product code → UPC when UPC exists',
            'context': 'Product 10002 has UPC 10026102100020, brand: BRAND_A',
            'query': "What's the product code?",
            'expected': {"upc": "10026102100020"}
        },
        {
            'name': 'EAN → UPC',
            'context': 'Product 10001 has UPC 3429270008762',
            'query': "What's the EAN?",
            'expected': {"upc": "3429270008762"}
        },
        {
            'name': 'Scanning code → UPC',
            'context': 'UPC: 5772251489388 for product A1040',
            'query': "Show me the scanning code",
            'expected': {"upc": "5772251489388"}
        }
    ]

    all_tests = [
        ("HALLUCINATION PREVENTION TESTS", hallucination_tests),
        ("TERMINOLOGY MAPPING TESTS", terminology_tests)
    ]

    total_passed = 0
    total_failed = 0

    for section_name, tests in all_tests:
        print(f"\n{section_name}")
        print("-" * 40)

        for test in tests:
            print(f"\n{test['name']}")
            print(f"Context: {test['context']}")
            print(f"Query: {test['query']}")
            print(f"Expected: {test['expected']}")

            prompt = f"""{test['context']}

Question: {test['query']}

Response:"""

            try:
                ollama_path = "/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe"
                cmd = [ollama_path, 'run', 'atp-extraction-v4', prompt]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                response = result.stdout.strip()

                # Parse JSON
                json_str = response
                if '```' in json_str:
                    parts = json_str.split('```')
                    for part in parts:
                        if '{' in part and '}' in part:
                            json_str = part
                            break
                    if json_str.startswith('json'):
                        json_str = json_str[4:].strip()

                start = json_str.find('{')
                end = json_str.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = json_str[start:end]

                actual = json.loads(json_str)
                print(f"Actual: {actual}")

                if actual == test['expected']:
                    print("✅ PASS")
                    total_passed += 1
                else:
                    print("❌ FAIL")
                    total_failed += 1

            except Exception as e:
                print(f"❌ Error: {e}")
                total_failed += 1

    print("\n" + "=" * 60)
    print(f"FINAL RESULTS:")
    print(f"✅ Passed: {total_passed}/{total_passed + total_failed}")
    print(f"❌ Failed: {total_failed}/{total_passed + total_failed}")
    print(f"Success rate: {total_passed/(total_passed + total_failed)*100:.1f}%")

    if total_passed == total_passed + total_failed:
        print("\n🎉 PERFECT! V4 handles both terminology and hallucination correctly!")

if __name__ == '__main__':
    test_v4_model()