#!/usr/bin/env python3
"""
Quick comparison of DeepSeek 1.5B vs 8B speed
"""

import subprocess
import time

def time_model(model_name, prompt):
    """Time a single model query"""

    print(f"\n🔬 Testing {model_name}...")

    cmd = [
        '/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe',
        'run',
        model_name,
        prompt
    ]

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        elapsed = time.time() - start
        response = result.stdout.strip()

        print(f"   ✅ Response time: {elapsed:.2f}s")
        print(f"   📝 Response: {response[:100]}")
        return elapsed, response
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout after 30s")
        return 30.0, "TIMEOUT"
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0, str(e)

def main():
    print("="*60)
    print("⚡ Quick Speed Test: DeepSeek 1.5B vs 8B")
    print("="*60)

    test_prompt = "Context: Product 10001. Question: What's the UPC?"

    print(f"\nTest query: {test_prompt}")

    # Test 1.5B model
    time_1_5b, response_1_5b = time_model('deepseek-1.5b-extraction', test_prompt)

    # Test 8B model
    time_8b, response_8b = time_model('deepseek-extraction', test_prompt)

    # Also test simple 8B
    time_8b_simple, response_8b_simple = time_model('deepseek-simple', test_prompt)

    # Test baseline Gemma
    time_gemma, response_gemma = time_model('atp-extraction-v4', test_prompt)

    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)

    results = [
        ("DeepSeek 1.5B", time_1_5b, response_1_5b),
        ("DeepSeek 8B", time_8b, response_8b),
        ("DeepSeek 8B Simple", time_8b_simple, response_8b_simple),
        ("Gemma 3 v4", time_gemma, response_gemma)
    ]

    # Sort by speed
    results.sort(key=lambda x: x[1])

    print("\n⏱️ Speed Ranking:")
    for i, (name, elapsed, response) in enumerate(results, 1):
        print(f"   {i}. {name:20} {elapsed:5.2f}s")

    # Calculate speedup
    fastest_time = results[0][1]
    slowest_time = results[-1][1]

    if fastest_time > 0:
        speedup = slowest_time / fastest_time
        print(f"\n🚀 Speedup: {results[0][0]} is {speedup:.1f}x faster than {results[-1][0]}")

    # Check accuracy (all should return null for product 10001)
    print("\n🎯 Accuracy Check (should all return null):")
    for name, _, response in results:
        if 'null' in response.lower():
            print(f"   ✅ {name:20} Correct (null)")
        else:
            print(f"   ❌ {name:20} Wrong (not null)")

    # Recommendation
    print("\n" + "="*60)
    print("💡 RECOMMENDATION")
    print("="*60)

    if time_1_5b < time_8b and 'null' in response_1_5b.lower():
        print("\n✅ DeepSeek 1.5B is faster and accurate!")
        print("   Recommended for production use")
        print(f"   {time_8b/time_1_5b:.1f}x faster than 8B version")
    elif time_8b < 5.0 and 'null' in response_8b.lower():
        print("\n✅ DeepSeek 8B is fast enough and accurate!")
        print("   Good for production if <5s response time is acceptable")
    else:
        print("\n⚠️ Consider using Gemma 3 v4 for now")
        print("   DeepSeek models may need optimization")

if __name__ == "__main__":
    main()