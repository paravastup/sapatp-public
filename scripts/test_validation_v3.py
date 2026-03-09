#!/usr/bin/env python3
"""Test the v3 model with the validation set using the proper prompt"""

import json
import subprocess
import sys
from pathlib import Path

def test_validation_v3(model_name: str = "atp-extraction-v3", num_tests: int = 100):
    """Test v3 model with validation examples"""

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

                # Just use the simple prompt - the model has the rules embedded
                prompt = f"""{user_msg}

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
                                # Debug: Show what the model is interpreting
                                if 'product code' in question.lower() or 'ean' in question.lower():
                                    print(f"  Note: Terminology issue - question asks for '{question}'")
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
    model = sys.argv[1] if len(sys.argv) > 1 else "atp-extraction-v3"
    num_tests = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    test_validation_v3(model, num_tests)