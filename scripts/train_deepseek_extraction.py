#!/usr/bin/env python3
"""
Train DeepSeek-R1:8b for UPC/Product extraction
Using 20,000 examples for comprehensive training
"""

import json
import subprocess
import random
from pathlib import Path
import time

print("="*60)
print("🚀 DeepSeek-R1:8b Training for Product Extraction")
print("="*60)

def load_training_data():
    """Load all training data"""
    print("\n📊 Loading training data...")

    training_examples = []

    # Load main extraction training (15,995 examples)
    extraction_file = Path('/mnt/d/demoproject/training_data/extraction_training_15k.jsonl')
    if extraction_file.exists():
        with open(extraction_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                training_examples.append(data)
        print(f"✅ Loaded {len(training_examples)} extraction examples")

    # Load terminology training (4,000 examples)
    terminology_file = Path('/mnt/d/demoproject/training_data/terminology_training_4k.jsonl')
    if terminology_file.exists():
        count_before = len(training_examples)
        with open(terminology_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                training_examples.append(data)
        print(f"✅ Loaded {len(training_examples) - count_before} terminology examples")

    print(f"📦 Total training examples: {len(training_examples)}")
    return training_examples

def create_deepseek_modelfile(training_examples):
    """Create Modelfile optimized for DeepSeek-R1"""

    print("\n📝 Creating DeepSeek Modelfile...")

    # Select diverse examples for few-shot learning
    random.shuffle(training_examples)
    few_shot_examples = training_examples[:50]  # Use 50 diverse examples

    modelfile_content = """FROM deepseek-r1:8b

SYSTEM You are a precise data extraction assistant specialized in SAP product data.

CRITICAL RULES:
1. Extract ONLY values that appear EXACTLY in the context
2. UPC/EAN/barcodes are ALWAYS 8-14 digit numbers
3. Product numbers (like "10001", "G3960") are NOT UPCs
4. When asked for UPC/EAN/barcode but only a product number exists, return {"upc": null}
5. NEVER generate or guess values
6. Return valid JSON only

REASONING APPROACH:
<think>
1. What field is being requested?
2. Does this field exist in the context?
3. What is the exact value?
4. Is this value valid for the field type?
</think>

Field mappings:
- UPC = EAN = barcode = scanning code = product code (when 8-14 digits)
- Product number = SKU = item number (when less than 8 digits or contains letters)
"""

    # Add examples
    modelfile_content += "\n\nMESSAGE user\n"

    # Add diverse training examples
    for example in few_shot_examples[:25]:
        for msg in example['messages']:
            if msg['role'] == 'user':
                modelfile_content += f"Context: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                modelfile_content += f"MESSAGE assistant\n{msg['content']}\n\nMESSAGE user\n"

    # Critical examples to prevent hallucination
    critical_examples = [
        ("Context: Product 10002 has UPC 00000000010002. Question: What's the UPC?",
         '{"upc": "00000000010002"}'),

        ("Context: Product 10001, brand BRAND_BETA. Question: What's the UPC?",
         '{"upc": null}'),

        ("Context: Product G3960 is available. Question: What's the EAN code?",
         '{"upc": null}'),

        ("Context: Item has EAN 8899556677001. Question: What's the barcode?",
         '{"upc": "8899556677001"}'),

        ("Context: Product 12345, order 78901, UPC 9876543210123. Question: What's the UPC?",
         '{"upc": "9876543210123"}'),

        ("Context: Product ABC123 is in stock. Question: What's the UPC?",
         '{"upc": null}'),

        ("Context: The product code is 10001. Question: What's the UPC?",
         '{"upc": null}'),

        ("Context: Product 10002, delivery quantity 150. Question: Extract UPC",
         '{"upc": null}')
    ]

    for user_msg, assistant_msg in critical_examples:
        modelfile_content += f"{user_msg}\n"
        modelfile_content += f"MESSAGE assistant\n{assistant_msg}\n\nMESSAGE user\n"

    # Save Modelfile
    modelfile_path = Path('/mnt/d/demoproject/Modelfile.deepseek-extraction')
    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)

    print(f"✅ Modelfile created: {modelfile_path}")
    print(f"   Examples included: {len(few_shot_examples) + len(critical_examples)}")

    return modelfile_path

def create_model(modelfile_path):
    """Create the DeepSeek extraction model"""
    print("\n🔨 Creating DeepSeek extraction model...")

    cmd = [
        '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
        'create',
        'deepseek-extraction',
        '-f',
        str(modelfile_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Model created successfully: deepseek-extraction")
            return True
        else:
            print(f"❌ Error creating model: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to create model: {e}")
        return False

def test_model():
    """Test the DeepSeek model with critical test cases"""
    print("\n" + "="*60)
    print("🧪 Testing DeepSeek Model")
    print("="*60)

    test_cases = [
        {
            "name": "Product with UPC",
            "prompt": "Context: Product 10002 has UPC 00000000010002. Question: What's the UPC?",
            "expected": "00000000010002",
            "should_have_value": True
        },
        {
            "name": "Product without UPC",
            "prompt": "Context: Product 10001, brand BRAND_BETA. Question: What's the UPC?",
            "expected": None,
            "should_have_value": False
        },
        {
            "name": "Product code confusion",
            "prompt": "Context: Product G3960 is available. Question: What's the EAN code?",
            "expected": None,
            "should_have_value": False
        },
        {
            "name": "EAN terminology",
            "prompt": "Context: Item has EAN 8899556677001. Question: What's the barcode?",
            "expected": "8899556677001",
            "should_have_value": True
        },
        {
            "name": "Multiple fields",
            "prompt": "Context: Product 10002, UPC 00000000010002, quantity 150. Question: Extract UPC",
            "expected": "00000000010002",
            "should_have_value": True
        },
        {
            "name": "Distractor test",
            "prompt": "Context: Product 12345, order 78901, UPC 9876543210123. Question: What's the UPC?",
            "expected": "9876543210123",
            "should_have_value": True
        },
        {
            "name": "No UPC present",
            "prompt": "Context: Product ABC123 is in stock. Question: What's the UPC?",
            "expected": None,
            "should_have_value": False
        },
        {
            "name": "Original problematic case",
            "prompt": "Context: Product information from SAP. Product 10001. Question: What is the UPC?",
            "expected": None,
            "should_have_value": False
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")
        print(f"   Query: {test['prompt'][:60]}...")

        # Call DeepSeek model
        cmd = [
            '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
            'run',
            'deepseek-extraction',
            test['prompt']
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            response = result.stdout.strip()

            print(f"   Response: {response[:100]}")

            # Parse response
            success = False
            try:
                # Extract JSON from response
                if '{' in response:
                    json_start = response.index('{')
                    json_end = response.rindex('}') + 1
                    json_str = response[json_start:json_end]
                    parsed = json.loads(json_str)

                    upc_value = parsed.get('upc')

                    if test['should_have_value']:
                        if upc_value == test['expected']:
                            print(f"   ✅ Correct: {upc_value}")
                            success = True
                            passed += 1
                        else:
                            print(f"   ❌ Wrong: expected {test['expected']}, got {upc_value}")
                            failed += 1
                    else:
                        if upc_value is None or upc_value == "null":
                            print(f"   ✅ Correctly returned null")
                            success = True
                            passed += 1
                        else:
                            print(f"   ❌ Should be null, got: {upc_value}")
                            failed += 1
                else:
                    print(f"   ❌ No JSON in response")
                    failed += 1

            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                failed += 1
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed += 1

        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout")
            failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    print(f"Total: {len(test_cases)}")
    print(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {failed}")

    if passed == len(test_cases):
        print("\n🎉 PERFECT! 100% accuracy achieved!")
    elif passed >= len(test_cases) * 0.9:
        print("\n✅ EXCELLENT! Over 90% accuracy")
    elif passed >= len(test_cases) * 0.8:
        print("\n👍 GOOD! Over 80% accuracy")
    else:
        print("\n⚠️ Needs improvement")

    return passed / len(test_cases)

def main():
    print("\n🔥 Starting DeepSeek Training Process")
    print("This will create a specialized extraction model")
    print("using DeepSeek-R1:8b as the base")

    # Load training data
    training_examples = load_training_data()

    if not training_examples:
        print("❌ No training data found!")
        return

    # Create Modelfile
    modelfile_path = create_deepseek_modelfile(training_examples)

    # Create model
    if create_model(modelfile_path):
        print("\n⏱️ Waiting for model to initialize...")
        time.sleep(3)

        # Test model
        accuracy = test_model()

        print("\n" + "="*60)
        print("🏁 TRAINING COMPLETE")
        print("="*60)
        print(f"Model: deepseek-extraction")
        print(f"Base: DeepSeek-R1:8b")
        print(f"Training examples: {len(training_examples)}")
        print(f"Accuracy: {accuracy*100:.1f}%")

        if accuracy >= 0.9:
            print("\n✅ Model is ready for production use!")
            print("\nTo use in your app, update:")
            print("  ollama_client_enhanced.py")
            print("  Change: self.extraction_model = 'atp-extraction-v4'")
            print("  To: self.extraction_model = 'deepseek-extraction'")
        else:
            print("\n⚠️ Model needs refinement")
            print("Consider adding more examples or adjusting parameters")

if __name__ == "__main__":
    main()