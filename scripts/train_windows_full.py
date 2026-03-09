#!/usr/bin/env python3
"""
FULL GPU Training - Uses ALL 19,995 examples
For maximum accuracy (will take 1-2 hours)
"""

import json
import torch
from pathlib import Path
import sys
import platform

print("="*60)
print("🚀 FULL GPU TRAINING - Maximum Accuracy")
print("="*60)

# Check GPU
if not torch.cuda.is_available():
    print("❌ No GPU detected!")
    sys.exit(1)

device = torch.device("cuda")
print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

def train_full():
    """Train with ALL data for best results"""
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling
    from datasets import Dataset

    print("\n📦 Loading GPT-2 model...")
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = model.config.eos_token_id

    model = model.cuda()
    print(f"✅ Model on GPU")

    # Load ALL training data
    print("\n📊 Loading FULL training dataset...")

    texts = []

    # Main training data (15,995 examples)
    train_file = Path('/mnt/d/productavailability/training_data/extraction_training_15k.jsonl')
    with open(train_file, 'r', encoding='utf-8') as f:
        for line in f:
            ex = json.loads(line)
            text = ""
            for msg in ex['messages']:
                if msg['role'] == 'user':
                    text += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    text += f"Assistant: {msg['content']}\n"
            texts.append(text.strip())

    # Add terminology training (4,000 examples)
    term_file = Path('/mnt/d/productavailability/training_data/terminology_training_4k.jsonl')
    if term_file.exists():
        with open(term_file, 'r', encoding='utf-8') as f:
            for line in f:
                ex = json.loads(line)
                text = ""
                for msg in ex['messages']:
                    if msg['role'] == 'user':
                        text += f"User: {msg['content']}\n"
                    elif msg['role'] == 'assistant':
                        text += f"Assistant: {msg['content']}\n"
                texts.append(text.strip())

    print(f"✅ Loaded {len(texts)} total examples!")

    # Create dataset
    dataset = Dataset.from_dict({"text": texts})

    # Tokenize with smaller chunks for memory efficiency
    def tokenize_function(examples):
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=128  # Shorter to fit more examples
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    print("   Tokenizing (this may take a minute)...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        batch_size=100,  # Process in batches
        remove_columns=["text"]
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=8
    )

    # Aggressive memory optimization for 6GB
    training_args = TrainingArguments(
        output_dir="./gpt2-extraction-FULL",
        overwrite_output_dir=True,
        num_train_epochs=1,  # Just 1 epoch for full data
        per_device_train_batch_size=1,  # Minimal batch
        gradient_accumulation_steps=16,  # Effective batch = 16
        warmup_steps=500,
        save_steps=2000,
        logging_steps=250,
        learning_rate=3e-5,
        fp16=True,
        gradient_checkpointing=True,  # Save memory
        evaluation_strategy="no",
        save_total_limit=2,
        load_best_model_at_end=False,
        report_to="none",
        remove_unused_columns=False,
        label_names=["labels"],
        dataloader_num_workers=0,  # Avoid multiprocessing overhead
        optim="adamw_torch_fused",  # Faster optimizer
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

    print("\n" + "="*60)
    print("🔥 Starting FULL training...")
    print(f"   Training examples: {len(tokenized_dataset)}")
    print(f"   This will take 60-90 minutes")
    print(f"   Watch the loss decrease!")
    print("="*60 + "\n")

    try:
        train_result = trainer.train()

        print("\n💾 Saving FULLY trained model...")
        trainer.save_model("./gpt2-extraction-FINAL-FULL")
        tokenizer.save_pretrained("./gpt2-extraction-FINAL-FULL")

        print("\n✅ FULL training complete!")
        print(f"   Final loss: {train_result.training_loss:.4f}")
        print(f"   Model saved to: ./gpt2-extraction-FINAL-FULL")
        print("\n🎉 This is your BEST model with ALL data!")

    except RuntimeError as e:
        if "out of memory" in str(e):
            print("\n❌ Out of memory!")
            print("Try the 5000 example version instead")
            print("Or reduce max_length to 64")
        else:
            raise e

if __name__ == "__main__":
    print("\n⚠️ This will train with ALL 19,995 examples")
    print("Estimated time: 60-90 minutes")
    print("For faster training, use train_windows_fixed.py (5000 examples)")

    response = input("\nContinue with FULL training? (y/n): ")
    if response.lower() == 'y':
        train_full()
    else:
        print("Use train_windows_fixed.py for 5000 example training")