#!/usr/bin/env python3
"""
Compare DeepSeek 8B vs 1.5B speed and accuracy
"""

import subprocess
import json
import time
from statistics import mean, median

def test_model_speed(model_name, test_prompt):
    """Test a single model and return response time"""

    cmd = [
        '/mnt/c/Users/paravastup/AppData/Local/Programs/Ollama/ollama.exe',
        'run',
        model_name,
        test_prompt
    ]

    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        end_time = time.time()

        response_time = end_time - start_time
        response = result.stdout.strip()

        return {
            'success': True,
            'response': response,
            'time': response_time
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'response': 'TIMEOUT',
            'time': 60.0
        }
    except Exception as e:
        return {
            'success': False,
            'response': str(e),
            'time': 0
        }

def main():
    print("="*60)
    print("🏎️ DeepSeek Speed & Accuracy Comparison")
    print("="*60)

    # Test cases for both speed and accuracy
    test_cases = [
        {
            "name": "Simple extraction",
            "prompt": "Context: Product 46961 has UPC 10026102469610. Question: What's the UPC?",
            "expected": "10026102469610"
        },
        {
            "name": "Null case",
            "prompt": "Context: Product 46888, brand PYREX. Question: What's the UPC?",
            "expected": None
        },
        {
            "name": "Complex context",
            "prompt": "Context: Product 12345, order 78901, UPC 9876543210123. Question: What's the UPC?",
            "expected": "9876543210123"
        }
    ]

    models = [
        ('deepseek-extraction', 'DeepSeek 8B'),
        ('deepseek-1.5b-extraction', 'DeepSeek 1.5B'),
        ('deepseek-simple', 'DeepSeek 8B Simple'),
        ('atp-extraction-v4', 'Gemma 3 v4 (baseline)')
    ]

    results = {}

    for model_id, model_name in models:
        print(f"\n🔬 Testing {model_name} ({model_id})...")
        print("-"*40)

        model_times = []
        model_accuracy = []

        for test_case in test_cases:
            print(f"\n  📝 {test_case['name']}")
            result = test_model_speed(model_id, test_case['prompt'])

            if result['success']:
                print(f"     Time: {result['time']:.2f}s")
                print(f"     Response: {result['response'][:80]}")

                model_times.append(result['time'])

                # Check accuracy
                if test_case['expected'] is None:
                    if 'null' in result['response'].lower():
                        model_accuracy.append(1)
                        print("     ✅ Correct (null)")
                    else:
                        model_accuracy.append(0)
                        print("     ❌ Wrong (should be null)")
                else:
                    if test_case['expected'] in result['response']:
                        model_accuracy.append(1)
                        print(f"     ✅ Correct ({test_case['expected']})")
                    else:
                        model_accuracy.append(0)
                        print(f"     ❌ Wrong (expected {test_case['expected']})")
            else:
                print(f"     ❌ Failed: {result['response']}")
                model_times.append(60.0)  # Penalty for timeout
                model_accuracy.append(0)

        # Store results
        results[model_id] = {
            'name': model_name,
            'times': model_times,
            'accuracy': model_accuracy,
            'avg_time': mean(model_times) if model_times else 0,
            'median_time': median(model_times) if model_times else 0,
            'accuracy_rate': mean(model_accuracy) if model_accuracy else 0
        }

    # Print comparison summary
    print("\n" + "="*60)
    print("📊 PERFORMANCE SUMMARY")
    print("="*60)

    print("\n⏱️ Speed Comparison:")
    print("-"*40)
    for model_id, data in sorted(results.items(), key=lambda x: x[1]['avg_time']):
        print(f"{data['name']:25} Avg: {data['avg_time']:5.2f}s | Med: {data['median_time']:5.2f}s")

    print("\n🎯 Accuracy Comparison:")
    print("-"*40)
    for model_id, data in sorted(results.items(), key=lambda x: x[1]['accuracy_rate'], reverse=True):
        print(f"{data['name']:25} {data['accuracy_rate']*100:5.1f}%")

    # Make recommendation
    print("\n" + "="*60)
    print("💡 RECOMMENDATION")
    print("="*60)

    # Find best model based on speed/accuracy balance
    best_score = 0
    best_model = None

    for model_id, data in results.items():
        # Score = accuracy weight (70%) - normalized time penalty (30%)
        # Lower time is better, so we invert it
        if data['avg_time'] > 0:
            time_score = 1.0 / data['avg_time']  # Inverse time (faster = higher score)
            normalized_time = time_score / max(1.0/r['avg_time'] for r in results.values() if r['avg_time'] > 0)
            score = (data['accuracy_rate'] * 0.7) + (normalized_time * 0.3)

            if score > best_score:
                best_score = score
                best_model = (model_id, data)

    if best_model:
        model_id, data = best_model
        print(f"\n🏆 Best Overall: {data['name']}")
        print(f"   - Speed: {data['avg_time']:.2f}s average")
        print(f"   - Accuracy: {data['accuracy_rate']*100:.1f}%")

        # Specific recommendations
        if 'deepseek-1.5b' in model_id:
            print("\n✅ DeepSeek 1.5B offers the best speed/accuracy balance!")
            print("   Recommended for production use where speed is critical")
        elif 'deepseek-extraction' in model_id:
            print("\n✅ DeepSeek 8B provides excellent accuracy!")
            print("   Recommended when accuracy is more important than speed")

        print("\n📝 To switch models, update:")
        print("   File: /mnt/d/productavailability/atp/chatbot/services/ollama_client_enhanced.py")
        print(f"   Change: self.extraction_model = '{model_id}'")

    # Speed-specific analysis
    print("\n⚡ Speed Analysis:")
    fastest = min(results.items(), key=lambda x: x[1]['avg_time'])
    slowest = max(results.items(), key=lambda x: x[1]['avg_time'])

    print(f"   Fastest: {fastest[1]['name']} ({fastest[1]['avg_time']:.2f}s)")
    print(f"   Slowest: {slowest[1]['name']} ({slowest[1]['avg_time']:.2f}s)")

    speedup = slowest[1]['avg_time'] / fastest[1]['avg_time']
    print(f"   Speed improvement: {speedup:.1f}x faster!")

if __name__ == "__main__":
    main()