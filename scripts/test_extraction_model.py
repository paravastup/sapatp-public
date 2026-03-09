#!/usr/bin/env python3
"""Test the extraction model with sample queries"""

import subprocess
import json
import sys

def test_extraction(model_name: str = "atp-extraction"):
    """Test the extraction model"""

    print(f"Testing {model_name} model...")
    print("=" * 60)

    test_cases = [
        {
            'name': 'Simple UPC extraction',
            'context': 'Product 10002 has UPC 10026102100020, brand BRAND_A, stock 1500 pieces',
            'query': "What's the UPC?",
            'expected_field': 'upc',
            'expected_value': '10026102100020'
        },
        {
            'name': 'Missing field should return null',
            'context': 'Product 10001 has brand BRAND_B, stock 2000 pieces',
            'query': "What's the UPC?",
            'expected_field': 'upc',
            'expected_value': None
        },
        {
            'name': 'Multiple products - specific extraction',
            'context': 'Product 10002 UPC: 10026102100020. Product 10001 UPC: 10026102100010',
            'query': "What's the UPC for 10001?",
            'expected_field': 'upc',
            'expected_value': '10026102100010'
        },
        {
            'name': 'Brand extraction',
            'context': 'Product G3960 has brand BRAND_C, UPC 10883314193807, stock 500',
            'query': "What brand is it?",
            'expected_field': 'brand',
            'expected_value': 'BRAND_C'
        },
        {
            'name': 'Stock quantity extraction',
            'context': 'Product 00213 has stock 1234 pieces, brand BRAND_A',
            'query': "How many in stock?",
            'expected_field': 'stock',
            'expected_value': '1234'
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Context: {test['context'][:60]}...")
        print(f"Query: {test['query']}")

        # Build the prompt with our extraction system prompt
        prompt = f"""You are a precise data extraction assistant.

CRITICAL RULES:
1. ONLY extract values that appear EXACTLY in the context
2. If a value is not present, return null
3. NEVER generate or guess values
4. Return valid JSON only

Context: {test['context']}

Question: {test['query']}

Extract the requested information and return JSON. Use null if not found.

Response:"""

        try:
            # Test with Ollama (Windows path)
            ollama_path = "/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe"
            cmd = [ollama_path, 'run', model_name, prompt]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            response = result.stdout.strip()

            print(f"Raw response: {response[:200]}...")

            # Try to parse JSON response
            try:
                # Clean up response
                json_str = response

                # Remove markdown code blocks if present
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

                parsed = json.loads(json_str)
                extracted_value = parsed.get(test['expected_field'])

                print(f"Extracted: {json.dumps(parsed)}")

                if extracted_value == test['expected_value']:
                    print("✓ PASS")
                    passed += 1
                elif extracted_value is None and test['expected_value'] is None:
                    print("✓ PASS (correctly returned null)")
                    passed += 1
                else:
                    print(f"✗ FAIL: Expected {test['expected_value']}, got {extracted_value}")
                    failed += 1

            except json.JSONDecodeError as e:
                print(f"✗ FAIL: Invalid JSON - {e}")
                print(f"Response was: {response[:500]}")
                failed += 1

        except subprocess.TimeoutExpired:
            print("✗ FAIL: Timeout")
            failed += 1
        except Exception as e:
            print(f"✗ FAIL: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")

    return passed, failed

if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else "atp-extraction"
    test_extraction(model)