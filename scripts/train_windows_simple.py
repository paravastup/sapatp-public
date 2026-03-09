#!/usr/bin/env python3
"""
Ultra-Simple GPU Training for Windows
Minimal dependencies, maximum compatibility
"""

import json
import torch
from pathlib import Path
import sys

print("="*60)
print("🚀 SIMPLE GPU TRAINING (Windows)")
print("="*60)

# Check GPU
if not torch.cuda.is_available():
    print("❌ No GPU detected!")
    print("Make sure you have NVIDIA drivers installed")
    sys.exit(1)

print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

def train_simple():
    """Super simple training that just works"""
    try:
        from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
        from transformers import Trainer, TrainingArguments

        print("\n📦 Loading GPT-2 model...")
        model = GPT2LMHeadModel.from_pretrained('gpt2')
        tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        tokenizer.pad_token = tokenizer.eos_token

        # Move model to GPU
        model = model.cuda()
        print(f"✅ Model loaded on GPU")

        # Create simple training data
        print("\n📊 Preparing training data...")
        train_path = Path('training_data.txt')

        # Convert JSONL to text
        examples = []
        jsonl_path = Path('D:/demoproject/training_data/extraction_training_15k.jsonl')
        if jsonl_path.exists():
            with open(jsonl_path, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 100:  # Just 100 examples for quick test
                        break
                    ex = json.loads(line)
                    # Format as simple text
                    for msg in ex['messages']:
                        if msg['role'] == 'user':
                            examples.append(f"Question: {msg['content']}")
                        elif msg['role'] == 'assistant':
                            examples.append(f"Answer: {msg['content']}\n")

        # Save as text file
        with open(train_path, 'w') as f:
            f.write('\n'.join(examples))

        print(f"✅ Created training file with {len(examples)//2} examples")

        # Create dataset
        dataset = TextDataset(
            tokenizer=tokenizer,
            file_path=str(train_path),
            block_size=128
        )

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )

        # Training arguments - MINIMAL for compatibility
        training_args = TrainingArguments(
            output_dir='./gpt2-trained',
            overwrite_output_dir=True,
            num_train_epochs=1,
            per_device_train_batch_size=1,
            save_steps=500,
            save_total_limit=2,
            logging_steps=10,
            fp16=True,  # Use mixed precision
        )

        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=dataset,
        )

        print("\n🔥 Starting training...")
        print("This will take 5-10 minutes for 100 examples")

        # Train
        trainer.train()

        # Save
        print("\n💾 Saving model...")
        trainer.save_model('./gpt2-extraction-windows')

        print("\n✅ Training complete!")
        print("Model saved to: ./gpt2-extraction-windows")

        # Quick test
        print("\n🧪 Testing model...")
        test_input = "Context: Product 10002 has UPC 00000000010002. Question: What's the UPC?"
        inputs = tokenizer(test_input, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=100, temperature=0.1)

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Input: {test_input}")
        print(f"Output: {result}")

    except ImportError as e:
        print(f"\n❌ Missing package: {e}")
        print("\nPlease install:")
        print("pip install transformers datasets accelerate")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTry reducing batch_size or using fewer examples")

if __name__ == "__main__":
    train_simple()