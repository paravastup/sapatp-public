#!/usr/bin/env python3
"""
Simulate fine-tuning by creating a model with embedded few-shot examples
Since Ollama doesn't support direct fine-tuning, we'll use prompt engineering
"""

import json
import random
from pathlib import Path

def create_enhanced_modelfile():
    """Create an enhanced Modelfile with few-shot examples embedded"""

    # Load some training examples
    training_file = Path('/mnt/d/demoproject/training_data/extraction_training_15k.jsonl')
    examples = []

    with open(training_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 10:  # Get first 10 examples for few-shot
                break
            examples.append(json.loads(line))

    # Build few-shot prompt
    few_shot = ""
    for i, ex in enumerate(examples[:5], 1):
        messages = ex['messages']
        user_msg = next(m['content'] for m in messages if m['role'] == 'user')
        assistant_msg = next(m['content'] for m in messages if m['role'] == 'assistant')

        # Extract just the context and question
        if 'Context:' in user_msg and 'Question:' in user_msg:
            parts = user_msg.split('Context:', 1)[1].split('Question:', 1)
            context = parts[0].strip()
            question = parts[1].strip() if len(parts) > 1 else ""

            few_shot += f"""
Example {i}:
Context: {context[:100]}...
Question: {question}
Response: {assistant_msg}
"""

    modelfile_content = f'''# Enhanced extraction model with few-shot examples
FROM atp-chatbot

SYSTEM """You are a precise data extraction assistant.

You MUST return valid JSON for every query. Here are examples of correct responses:

{few_shot}

CRITICAL RULES:
1. ALWAYS return valid JSON format like {{"field": "value"}} or {{"field": null}}
2. ONLY extract values that appear EXACTLY in the context
3. If a value is not present, return {{"field": null}}
4. NEVER generate or guess values
5. Copy values exactly as shown

Remember: Your response must be valid JSON only. No other text."""

PARAMETER temperature 0.01
PARAMETER top_p 0.1
PARAMETER top_k 5
PARAMETER repeat_penalty 1.0
PARAMETER num_predict 100
PARAMETER seed 42'''

    # Save the enhanced Modelfile
    modelfile_path = Path('/mnt/d/demoproject/Modelfile.extraction-enhanced')
    modelfile_path.write_text(modelfile_content)
    print(f"Created enhanced Modelfile: {modelfile_path}")
    return modelfile_path

def test_with_few_shot():
    """Test using few-shot prompting directly"""

    print("\nTesting with few-shot prompting...")
    print("=" * 60)

    # Load training examples for few-shot
    training_file = Path('/mnt/d/demoproject/training_data/extraction_training_15k.jsonl')
    few_shot_examples = []

    with open(training_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            few_shot_examples.append(json.loads(line))

    # Build few-shot prompt
    few_shot_prompt = "Here are examples of correct extraction:\n\n"

    for i, ex in enumerate(few_shot_examples, 1):
        messages = ex['messages']
        user_msg = next(m['content'] for m in messages if m['role'] == 'user')
        assistant_msg = next(m['content'] for m in messages if m['role'] == 'assistant')

        if 'Context:' in user_msg and 'Question:' in user_msg:
            parts = user_msg.split('Context:', 1)[1].split('Question:', 1)
            context = parts[0].strip()[:100]
            question = parts[1].strip()

            few_shot_prompt += f"Example {i}:\n"
            few_shot_prompt += f"Context: {context}...\n"
            few_shot_prompt += f"Question: {question}\n"
            few_shot_prompt += f"Response: {assistant_msg}\n\n"

    # Now test with a real query
    test_context = "Product 10002 has UPC 00000000010002, brand BRAND_ALPHA"
    test_query = "What's the UPC?"

    full_prompt = f"""{few_shot_prompt}Now extract from this:
Context: {test_context}
Question: {test_query}
Response:"""

    print("Few-shot prompt created with 5 examples")
    print(f"Testing: {test_query}")
    print(f"Context: {test_context}")

    # Save test prompt for manual testing
    test_prompt_path = Path('/mnt/d/demoproject/test_prompt.txt')
    test_prompt_path.write_text(full_prompt)
    print(f"\nSaved test prompt to: {test_prompt_path}")
    print("You can test this manually with: ollama run atp-extraction < test_prompt.txt")

def main():
    print("Simulating Fine-tuning Process")
    print("=" * 60)

    # Create enhanced Modelfile
    modelfile_path = create_enhanced_modelfile()

    # Create the enhanced model
    import subprocess

    print("\nCreating enhanced extraction model...")

    # Copy to Windows temp
    temp_modelfile = Path('/mnt/c/Users/demouser/AppData/Local/Temp/Modelfile-enhanced')
    temp_modelfile.write_text(modelfile_path.read_text())

    try:
        ollama_path = "/mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe"
        cmd = [ollama_path, 'create', 'atp-extraction-v2', '-f', str(temp_modelfile)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Successfully created atp-extraction-v2 model with few-shot examples")
        else:
            print(f"Error creating model: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with few-shot
    test_with_few_shot()

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("1. Test the enhanced model: python3 scripts/test_extraction_model.py atp-extraction-v2")
    print("2. For real fine-tuning, use Unsloth or cloud services")
    print("3. The training data is ready in training_data/extraction_training_15k.jsonl")

if __name__ == '__main__':
    main()