#!/usr/bin/env python3
"""
Test intent classification for follow-up questions
"""

import subprocess
import json

def test_intent_classification(query):
    """Test how a query is classified"""

    system_prompt = """Classify intent: stock_query, delivery_query, product_info, plant_selection, export_request, comparison, help, greeting, clarification_needed.
Reply with intent name only."""

    prompt = f'Query: "{query}"\nIntent:'

    cmd = [
        '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
        'run',
        'gemma3:4b',
        f"{system_prompt}\n\n{prompt}"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        response = result.stdout.strip()
        return response
    except:
        return "ERROR"

def main():
    """Test various follow-up queries"""

    test_queries = [
        # Clear stock queries
        ("What's the stock for product 10001?", "stock_query"),
        ("How many pieces in stock?", "stock_query"),
        ("Stock levels?", "stock_query"),
        ("What's the availability?", "stock_query"),

        # Follow-up stock queries (problematic)
        ("What about the stock?", "stock_query"),
        ("How about stock?", "stock_query"),
        ("And the stock?", "stock_query"),
        ("Stock?", "stock_query"),
        ("How many?", "stock_query"),

        # UPC queries
        ("What's the UPC for 10001?", "product_info"),
        ("Give me the UPC", "product_info"),
        ("UPC?", "product_info"),

        # Follow-up UPC queries
        ("What about the UPC?", "product_info"),
        ("And the barcode?", "product_info"),

        # Mixed follow-ups
        ("Now show me stock", "stock_query"),
        ("Give me stock instead", "stock_query"),
        ("I meant stock", "stock_query"),
    ]

    print("="*60)
    print("🧪 Testing Intent Classification")
    print("="*60)

    correct = 0
    total = 0

    for query, expected_intent in test_queries:
        classified = test_intent_classification(query)
        total += 1

        # Clean up response
        classified = classified.lower().strip()
        if '\n' in classified:
            classified = classified.split('\n')[0]

        is_correct = classified == expected_intent
        if is_correct:
            correct += 1
            symbol = "✅"
        else:
            symbol = "❌"

        print(f"\n{symbol} Query: '{query}'")
        print(f"   Expected: {expected_intent}")
        print(f"   Got: {classified}")

    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

    if correct < total * 0.8:
        print("\n⚠️ Intent classification needs improvement!")
        print("Follow-up questions are being misclassified")
        print("\nPossible solutions:")
        print("1. Improve intent classification prompt")
        print("2. Add keyword detection for common follow-ups")
        print("3. Consider conversation context in classification")

if __name__ == "__main__":
    main()