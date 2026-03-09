#!/usr/bin/env python3
"""
Fixed GPU Training Script for Windows
Properly handles labels for GPT-2 training
"""

import json
import torch
from pathlib import Path
import sys
import platform

print("="*60)
print("🚀 GPU TRAINING (Windows) - Fixed Version")
print("="*60)

# Check GPU
if not torch.cuda.is_available():
    print("❌ No GPU detected!")
    sys.exit(1)

device = torch.device("cuda")
print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

def train_gpt2():
    """Train GPT-2 with proper label handling"""
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling
    from datasets import Dataset

    print("\n📦 Loading GPT-2 model...")
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

    # IMPORTANT: Set pad token
    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = model.config.eos_token_id

    # Move to GPU
    model = model.cuda()
    print(f"✅ Model loaded on GPU")
    print(f"   Model size: {sum(p.numel() for p in model.parameters())/1e6:.1f}M parameters")

    # Load training data
    print("\n📊 Preparing training data...")

    # Use correct path for Windows
    if platform.system() == 'Windows':
        train_file = Path('D:/productavailability/training_data/extraction_training_15k.jsonl')
    else:
        train_file = Path('/mnt/d/productavailability/training_data/extraction_training_15k.jsonl')

    texts = []
    with open(train_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5000:  # Train with 5000 examples (good for 6GB VRAM)
                break
            ex = json.loads(line)

            # Format as conversation
            text = ""
            for msg in ex['messages']:
                if msg['role'] == 'user':
                    text += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    text += f"Assistant: {msg['content']}\n"

            texts.append(text.strip())

    print(f"✅ Loaded {len(texts)} training examples")

    # Create dataset
    dataset = Dataset.from_dict({"text": texts})

    # Tokenize WITH LABELS
    def tokenize_function(examples):
        # Tokenize the text
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=256  # Shorter for 6GB GPU
        )

        # IMPORTANT: Copy input_ids to labels for language modeling
        tokenized["labels"] = tokenized["input_ids"].copy()

        return tokenized

    print("   Tokenizing dataset...")
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])

    # Data collator that handles padding
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # GPT-2 is not a masked language model
        pad_to_multiple_of=8  # Efficient for GPU
    )

    # Training arguments optimized for RTX 4050
    training_args = TrainingArguments(
        output_dir="./gpt2-extraction-trained",
        overwrite_output_dir=True,
        num_train_epochs=2,  # Train for 2 epochs for better learning
        per_device_train_batch_size=2,  # Small batch for 6GB
        gradient_accumulation_steps=4,   # Effective batch = 8
        warmup_steps=100,  # More warmup for 5000 examples
        save_steps=500,
        logging_steps=100,
        learning_rate=5e-5,
        fp16=True,  # Mixed precision for efficiency
        evaluation_strategy="no",  # No eval dataset for now
        save_total_limit=2,
        load_best_model_at_end=False,
        report_to="none",  # Don't report to wandb/tensorboard
        remove_unused_columns=False,  # Important for labels
        label_names=["labels"],  # Explicitly specify label column
    )

    # Create trainer
    print("\n🏋️ Creating trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
    )

    # Train
    print("\n" + "="*60)
    print("🔥 Starting GPU training...")
    print(f"   Training examples: {len(tokenized_dataset)}")
    print(f"   Batch size: 2 (accumulated to 8)")
    print(f"   Estimated time: 5-10 minutes")
    print("="*60 + "\n")

    try:
        # Start training
        train_result = trainer.train()

        # Save model
        print("\n💾 Saving fine-tuned model...")
        trainer.save_model("./gpt2-extraction-final")
        tokenizer.save_pretrained("./gpt2-extraction-final")

        print("\n✅ Training complete!")
        print(f"   Training loss: {train_result.training_loss:.4f}")
        print(f"   Model saved to: ./gpt2-extraction-final")

        # Quick test
        test_model(model, tokenizer)

        return model, tokenizer

    except Exception as e:
        print(f"\n❌ Training error: {e}")
        print("\nTroubleshooting:")
        print("1. Try reducing batch_size to 1")
        print("2. Try reducing max_length to 128")
        print("3. Ensure GPU memory is free")
        return None, None

def test_model(model, tokenizer):
    """Test the trained model"""
    print("\n" + "="*60)
    print("🧪 Testing trained model...")
    print("="*60)

    test_prompts = [
        "User: Context: Product 46961 has UPC 10026102469610. Question: What's the UPC?\nAssistant:",
        "User: Context: Product 46888, brand PYREX. Question: What's the UPC?\nAssistant:"
    ]

    model.eval()
    for prompt in test_prompts:
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=inputs['input_ids'].shape[1] + 20,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"Response: {response[len(prompt):][:50]}...")

def main():
    print("\nThis script properly handles labels for GPT-2 training")
    print("It should work without the 'no loss' error\n")

    model, tokenizer = train_gpt2()

    if model is not None:
        print("\n" + "="*60)
        print("🎉 SUCCESS! Your model is trained!")
        print("="*60)
        print("\nNext steps:")
        print("1. Test the model with your queries")
        print("2. Convert to GGUF format for Ollama")
        print("3. Or use directly with transformers")
    else:
        print("\n⚠️ Training failed. Check the error messages above.")

if __name__ == "__main__":
    main()