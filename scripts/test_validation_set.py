#!/usr/bin/env python3
"""Test the model with the validation set"""

import json
import subprocess
import sys
from pathlib import Path

def test_validation_examples(model_name: str = "atp-extraction-v2", num_tests: int = 20):
    """Test model with validation examples"""

    print(f"Testing {model_name} with validation set")
    print("=" * 60)

    validation_file = Path('/opt/app/training_data/extraction_validation_1k.jsonl')

    if not validation_file.exists():
        print(f"Error: Validation file not found: {validation_file}")
        return 0, 0

    passed = 0
    failed = 0
    test_count = 0

    with open(validation_file, 'r') as f:
        for line in f:
            if test_count >= num_tests:
                break

            test_count += 1
            example = json.loads(line)
            messages = example['messages']

            # Extract the user message and expected response
            user_msg = next(m['content'] for m in messages if m['role'] == 'user')
            expected = next(m['content'] for m in messages if m['role'] == 'assistant')

            print(f"\nTest {test_count}:")

            # Extract context and question
            if 'Context:' in user_msg and 'Question:' in user_msg:
                parts = user_msg.split('Context:', 1)[1].split('Question:', 1)
                context = parts[0].strip()[:100] + "..."
                question = parts[1].strip() if len(parts) > 1 else ""

                print(f"Context: {context}")
                print(f"Question: {question}")
                print(f"Expected: {expected}")

                # Build full prompt
                prompt = f"""You are a precise data extraction assistant.

CRITICAL RULES:
1. ALWAYS return valid JSON format
2. ONLY extract values that appear EXACTLY in the context
3. If a value is not present, return null
4. NEVER generate or guess values

{user_msg}

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

                    # Parse both expected and actual
                    try:
                        expected_json = json.loads(expected)
                        actual_json = json.loads(json_str)

                        print(f"Actual: {json.dumps(actual_json)}")

                        # Compare
                        if expected_json == actual_json:
                            print("✓ PASS")
                            passed += 1
                        else:
                            # Check if they're semantically equivalent (e.g., null vs None)
                            match = True
                            for key in expected_json:
                                expected_val = expected_json.get(key)
                                actual_val = actual_json.get(key)
                                if expected_val != actual_val:
                                    # Allow some flexibility for null values
                                    if not (expected_val is None and actual_val is None):
                                        match = False
                                        break

                            if match:
                                print("✓ PASS (equivalent)")
                                passed += 1
                            else:
                                print(f"✗ FAIL: Mismatch")
                                failed += 1

                    except json.JSONDecodeError as e:
                        print(f"✗ FAIL: Invalid JSON - {e}")
                        print(f"Response was: {response[:200]}")
                        failed += 1

                except subprocess.TimeoutExpired:
                    print("✗ FAIL: Timeout")
                    failed += 1
                except Exception as e:
                    print(f"✗ FAIL: {e}")
                    failed += 1

    print("\n" + "=" * 60)
    print(f"VALIDATION RESULTS: {passed} passed, {failed} failed")
    print(f"Accuracy: {passed/(passed+failed)*100:.1f}%")

    return passed, failed

if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else "atp-extraction-v2"
    num_tests = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    test_validation_examples(model, num_tests)