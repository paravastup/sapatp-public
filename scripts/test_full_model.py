#!/usr/bin/env python3
"""
Test the fully trained GPT-2 model with 19,995 examples
Verify it doesn't hallucinate UPC codes
"""

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from pathlib import Path
import json
import re

print("="*60)
print("🧪 TESTING FULLY TRAINED MODEL (19,995 examples)")
print("="*60)

# Check GPU
if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"✅ Using GPU: {torch.cuda.get_device_name(0)}")
else:
    device = torch.device("cpu")
    print("⚠️ Using CPU (slower)")

def test_model():
    """Test the model with various queries"""

    # Load the fully trained model
    model_path = Path('/mnt/d/demoproject/gpt2-extraction-FINAL-FULL')
    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        return

    print(f"\n📦 Loading model from {model_path}...")
    model = GPT2LMHeadModel.from_pretrained(model_path)
    tokenizer = GPT2Tokenizer.from_pretrained(model_path)

    # Set pad token
    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = model.config.eos_token_id

    model = model.to(device)
    model.eval()
    print("✅ Model loaded successfully")

    # Test cases - same as what caused hallucination before
    test_cases = [
        {
            "name": "Product 10002 with UPC",
            "prompt": "User: Context: Product 10002 has UPC 00000000010002. Question: What's the UPC?\nAssistant:",
            "expected": "00000000010002"
        },
        {
            "name": "Product 10001 without UPC",
            "prompt": "User: Context: Product 10001, brand BRAND_BETA. Question: What's the UPC?\nAssistant:",
            "expected": "null or not found"
        },
        {
            "name": "Product code confusion",
            "prompt": "User: Context: Product G3960 is available. Question: What's the EAN code?\nAssistant:",
            "expected": "null (G3960 is product code, not EAN)"
        },
        {
            "name": "Multiple fields",
            "prompt": "User: Context: Product 10002, UPC 00000000010002, brand BRAND_BETA, quantity 150. Question: Extract UPC and quantity\nAssistant:",
            "expected": "UPC: 00000000010002, quantity: 150"
        },
        {
            "name": "EAN terminology",
            "prompt": "User: Context: Item has EAN 8899556677001. Question: What's the barcode?\nAssistant:",
            "expected": "8899556677001"
        },
        {
            "name": "Distractor test",
            "prompt": "User: Context: Product 12345, order 78901, UPC 9876543210123. Question: What's the UPC?\nAssistant:",
            "expected": "9876543210123"
        },
        {
            "name": "No UPC present",
            "prompt": "User: Context: Product ABC123 is in stock. Question: What's the UPC?\nAssistant:",
            "expected": "null or not found"
        },
        {
            "name": "Original problematic case",
            "prompt": "User: Context: Product information from SAP. Product 10001. Question: What is the UPC?\nAssistant:",
            "expected": "null (should NOT hallucinate 10026, 79461, etc.)"
        }
    ]

    print("\n" + "="*60)
    print("Running test cases...")
    print("="*60)

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")
        print(f"   Prompt: {test['prompt'][:80]}...")
        print(f"   Expected: {test['expected']}")

        # Tokenize input
        inputs = tokenizer(
            test['prompt'],
            return_tensors="pt",
            truncation=True,
            max_length=256
        ).to(device)

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # Decode response
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the assistant's response
        response = full_response[len(test['prompt']):].strip()

        print(f"   Response: {response[:100]}")

        # Check for hallucination patterns
        hallucination_patterns = ["10026", "79461", "8894"]  # Previous hallucinations
        is_hallucinating = any(pattern in response for pattern in hallucination_patterns)

        # Extract any numbers that look like UPCs (8-14 digits)
        upc_pattern = r'\b\d{8,14}\b'
        found_upcs = re.findall(upc_pattern, response)

        # Analyze result
        success = False
        if "null" in test['expected'].lower() or "not found" in test['expected'].lower():
            # Should not return a UPC
            if "null" in response.lower() or "not found" in response.lower() or not found_upcs:
                success = True
                print("   ✅ Correctly returned null/not found")
            else:
                print(f"   ❌ Should have returned null, but returned: {response[:50]}")
        else:
            # Should return specific UPC
            if test['expected'] in response or any(upc in test['expected'] for upc in found_upcs):
                success = True
                print("   ✅ Correctly extracted UPC")
            else:
                print(f"   ❌ Expected {test['expected']}, got: {response[:50]}")

        if is_hallucinating:
            print(f"   ⚠️ HALLUCINATION DETECTED: Found old hallucination patterns!")
            success = False

        results.append({
            "test": test['name'],
            "success": success,
            "response": response[:100],
            "hallucinating": is_hallucinating
        })

    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for r in results if r['success'])
    hallucinations = sum(1 for r in results if r['hallucinating'])

    print(f"\nTotal tests: {total}")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Hallucinations: {hallucinations}")

    if hallucinations == 0:
        print("\n🎉 SUCCESS! No hallucinations detected!")
    else:
        print(f"\n⚠️ Found {hallucinations} hallucination(s)")

    # Show failed tests
    failed = [r for r in results if not r['success']]
    if failed:
        print("\n❌ Failed tests:")
        for r in failed:
            print(f"   - {r['test']}")
            print(f"     Response: {r['response']}")

    return results

def test_with_real_data():
    """Test with actual SAP data format"""
    print("\n" + "="*60)
    print("🔬 Testing with real SAP data format")
    print("="*60)

    # Load model
    model_path = Path('/mnt/d/demoproject/gpt2-extraction-FINAL-FULL')
    model = GPT2LMHeadModel.from_pretrained(model_path)
    tokenizer = GPT2Tokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token
    model = model.to(device)
    model.eval()

    # Real SAP-like queries
    real_queries = [
        "User: I need the UPC for product 10002\nAssistant:",
        "User: What's the barcode for item G3960?\nAssistant:",
        "User: Can you tell me the EAN code for product 10001?\nAssistant:",
        "User: Extract UPC from: Product 10002, UPC: 00000000010002, Price: $24.99\nAssistant:"
    ]

    print("\nTesting real-world queries:")
    for query in real_queries:
        print(f"\n🔍 Query: {query[:60]}...")

        inputs = tokenizer(query, return_tensors="pt", max_length=256, truncation=True).to(device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=30,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(query):].strip()

        print(f"   Response: {response}")

if __name__ == "__main__":
    print("\nThis will test the fully trained model with all 19,995 examples")
    print("Checking for hallucinations and accuracy...\n")

    # Run main tests
    results = test_model()

    # Run real data tests
    test_with_real_data()

    print("\n" + "="*60)
    print("✅ Testing complete!")
    print("="*60)