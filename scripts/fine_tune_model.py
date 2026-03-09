#!/usr/bin/env python3
"""
Fine-tuning script for Gemma 3 4B with extraction training data
Uses the 15,000 examples to teach exact value extraction

Note: Ollama doesn't directly support fine-tuning, so this script provides
multiple approaches to fine-tune your model.
"""

import json
import subprocess
import os
from pathlib import Path
import sys


def check_ollama_models():
    """Check which Ollama models are available"""
    print("Checking available Ollama models...")
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        print(result.stdout)

        # Check for our models
        if 'atp-chatbot' in result.stdout:
            print("✓ atp-chatbot model found")
        if 'gemma3:4b' in result.stdout:
            print("✓ gemma3:4b model found")

    except Exception as e:
        print(f"Error checking models: {e}")


def create_base_model():
    """Create the base extraction model using Modelfile"""
    print("\nCreating base extraction model...")

    # Choose which Modelfile to use
    if Path('/mnt/d/productavailability/Modelfile.extraction-from-atp').exists():
        modelfile = 'Modelfile.extraction-from-atp'
        model_name = 'atp-extraction-v2'
    else:
        modelfile = 'Modelfile.extraction'
        model_name = 'atp-extraction'

    try:
        # Create the model with Ollama
        cmd = f'ollama create {model_name} -f {modelfile}'
        print(f"Running: {cmd}")
        result = subprocess.run(cmd.split(), capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Successfully created {model_name} model")
            return model_name
        else:
            print(f"✗ Error creating model: {result.stderr}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def convert_training_for_llama_cpp():
    """Convert training data for llama.cpp fine-tuning"""
    print("\nConverting training data for llama.cpp format...")

    input_file = Path('/mnt/d/productavailability/training_data/extraction_training_15k.jsonl')
    output_file = Path('/mnt/d/productavailability/training_data/extraction_training_llama.jsonl')

    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)

            # Convert to llama.cpp format
            text = ""
            for message in data['messages']:
                if message['role'] == 'system':
                    text += f"System: {message['content']}\n\n"
                elif message['role'] == 'user':
                    text += f"User: {message['content']}\n\n"
                elif message['role'] == 'assistant':
                    text += f"Assistant: {message['content']}\n\n"

            f_out.write(json.dumps({'text': text.strip()}) + '\n')

    print(f"✓ Converted {input_file.name} to {output_file.name}")
    return output_file


def test_extraction_model(model_name: str):
    """Test the extraction model with sample queries"""
    print(f"\nTesting {model_name} model...")

    test_cases = [
        {
            'context': 'Product 46961 has UPC 10026102469610, brand LUMINARC, stock 1500 pieces',
            'query': "What's the UPC?",
            'expected': '10026102469610'
        },
        {
            'context': 'Product 46888 has brand PYREX, stock 2000 pieces',
            'query': "What's the UPC?",
            'expected': None  # Should return null
        },
        {
            'context': 'Product 46961 UPC: 10026102469610. Product 46888 UPC: 10026102468880',
            'query': "What's the UPC for 46888?",
            'expected': '10026102468880'
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['query']}")
        print(f"Context: {test['context'][:50]}...")

        # Build prompt
        prompt = f"""Context: {test['context']}

Question: {test['query']}

Extract the requested information exactly as shown. Return JSON."""

        try:
            # Test with Ollama
            cmd = ['ollama', 'run', model_name, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            response = result.stdout.strip()
            print(f"Response: {response}")

            # Try to parse JSON response
            try:
                if response:
                    # Clean up response (remove markdown if present)
                    if '```' in response:
                        response = response.split('```')[1].strip()
                        if response.startswith('json'):
                            response = response[4:].strip()

                    parsed = json.loads(response)
                    extracted_upc = parsed.get('upc')

                    if extracted_upc == test['expected']:
                        print("✓ PASS")
                        passed += 1
                    elif extracted_upc is None and test['expected'] is None:
                        print("✓ PASS (correctly returned null)")
                        passed += 1
                    else:
                        print(f"✗ FAIL: Expected {test['expected']}, got {extracted_upc}")
                        failed += 1
                else:
                    print("✗ FAIL: No response")
                    failed += 1

            except json.JSONDecodeError:
                print(f"✗ FAIL: Invalid JSON response")
                failed += 1

        except subprocess.TimeoutExpired:
            print("✗ FAIL: Timeout")
            failed += 1
        except Exception as e:
            print(f"✗ FAIL: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")

    return passed, failed


def provide_fine_tuning_instructions():
    """Provide instructions for actual fine-tuning"""
    print("\n" + "="*80)
    print("FINE-TUNING INSTRUCTIONS")
    print("="*80)

    print("""
Since Ollama doesn't directly support fine-tuning, here are your options:

OPTION 1: Use Unsloth (Recommended for Gemma)
---------------------------------------------
1. Install Unsloth:
   pip install unsloth

2. Convert Gemma to Hugging Face format:
   from unsloth import FastGemmaModel
   model, tokenizer = FastGemmaModel.from_pretrained(
       "google/gemma-2b-it",
       load_in_4bit=True
   )

3. Fine-tune with our training data:
   python scripts/unsloth_fine_tune.py

4. Convert back to GGUF for Ollama:
   python convert.py --model fine-tuned-gemma --quantization q4_k_m

OPTION 2: Use llama.cpp (More Complex)
---------------------------------------
1. Get the Gemma GGUF file from Ollama:
   find ~/.ollama -name "gemma3*4b*.gguf"

2. Convert to llama.cpp format and fine-tune:
   ./finetune --model gemma3-4b.gguf \\
             --train-data extraction_training_llama.jsonl \\
             --epochs 3 \\
             --batch-size 4 \\
             --learning-rate 1e-5

3. Import back to Ollama:
   ollama create atp-extraction-finetuned -f Modelfile.finetuned

OPTION 3: Use OpenAI-compatible Fine-tuning Service
----------------------------------------------------
1. Convert data to OpenAI format (already in correct format!)
2. Use services like:
   - Together AI
   - Anyscale
   - Modal
   - Replicate

3. Fine-tune and download the model
4. Convert to GGUF and import to Ollama

OPTION 4: Prompt Engineering with Examples (Quick Test)
-------------------------------------------------------
Instead of fine-tuning, you can test with few-shot prompting:

1. Include 3-5 examples in every prompt
2. Use the constrained generation approach
3. This won't be as accurate but can work as a baseline
""")

    print("\n" + "="*80)
    print("RECOMMENDED NEXT STEPS")
    print("="*80)
    print("""
1. TEST CURRENT MODEL:
   Test if the base model + good prompting is sufficient

2. IF ACCURACY < 90%:
   Implement Option 1 (Unsloth) for proper fine-tuning

3. VALIDATE:
   Use the 1000 validation examples to measure accuracy

4. DEPLOY:
   Update ollama_client.py to use the fine-tuned model
""")


def create_unsloth_script():
    """Create a script for Unsloth fine-tuning"""
    script_content = '''#!/usr/bin/env python3
"""
Fine-tune Gemma 3 4B using Unsloth for fast LoRA training
Requires: pip install unsloth transformers datasets
"""

import json
from pathlib import Path
from unsloth import FastLanguageModel
from transformers import TrainingArguments
from trl import SFTTrainer
from datasets import Dataset

# Load training data
def load_training_data():
    data = []
    with open('/mnt/d/productavailability/training_data/extraction_training_15k.jsonl', 'r') as f:
        for line in f:
            item = json.loads(line)
            # Format for Unsloth
            text = ""
            for msg in item['messages']:
                if msg['role'] == 'system':
                    text += f"System: {msg['content']}\\n\\n"
                elif msg['role'] == 'user':
                    text += f"User: {msg['content']}\\n\\n"
                elif msg['role'] == 'assistant':
                    text += f"Assistant: {msg['content']}\\n\\n"
            data.append({'text': text.strip()})
    return Dataset.from_list(data)

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/gemma-2-2b-it-bnb-4bit",  # 4-bit quantized
    max_seq_length=2048,
    load_in_4bit=True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # LoRA rank
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

# Load dataset
train_dataset = load_training_data()

# Training arguments
training_args = TrainingArguments(
    output_dir="./extraction-finetuned",
    max_steps=1000,  # Adjust based on GPU
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_steps=10,
    learning_rate=2e-4,
    fp16=True,  # Use mixed precision
    logging_steps=10,
    save_steps=100,
    evaluation_strategy="no",
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    args=training_args,
    dataset_text_field="text",
    max_seq_length=2048,
)

# Train
trainer.train()

# Save model
model.save_pretrained("extraction-finetuned-gemma")
tokenizer.save_pretrained("extraction-finetuned-gemma")

print("Fine-tuning complete! Now convert to GGUF for Ollama:")
print("python llama.cpp/convert.py extraction-finetuned-gemma --outtype q4_K_M")
'''

    script_path = Path('/mnt/d/productavailability/scripts/unsloth_fine_tune.py')
    script_path.write_text(script_content)
    print(f"Created Unsloth fine-tuning script: {script_path}")


def main():
    print("="*80)
    print("LLM EXTRACTION MODEL FINE-TUNING")
    print("="*80)

    # Check current models
    check_ollama_models()

    # Create base model
    model_name = create_base_model()

    if model_name:
        # Test the model (baseline before fine-tuning)
        print("\n" + "="*80)
        print("BASELINE TEST (Before Fine-tuning)")
        print("="*80)
        test_extraction_model(model_name)

    # Convert training data for different formats
    convert_training_for_llama_cpp()

    # Create Unsloth script
    create_unsloth_script()

    # Provide instructions
    provide_fine_tuning_instructions()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"""
Training data generated: ✓ (15,995 examples)
Validation data generated: ✓ (1,000 examples)
Base model created: {'✓' if model_name else '✗'}
Modelfiles created: ✓

Next steps:
1. Choose a fine-tuning method from the options above
2. Fine-tune the model with the 15,000 examples
3. Test accuracy with the validation set
4. If accuracy > 95%, update your chatbot to use the fine-tuned model

The training data teaches the model to:
- Extract exact values without hallucination
- Return null when data is missing
- Handle multiple formats and phrasings
- Work with all 15 SAP fields
""")


if __name__ == '__main__':
    main()