#!/usr/bin/env python3
"""
Simplified GPU Fine-Tuning Script (No Unsloth Required)
Uses standard Hugging Face libraries for stability
"""

import json
import torch
from pathlib import Path
from typing import List, Dict
import sys

def prepare_training_data():
    """Load and prepare training data"""
    print("\n📊 Loading training data...")

    all_examples = []

    # Load main training data
    main_training = Path('/mnt/d/productavailability/training_data/extraction_training_15k.jsonl')
    if main_training.exists():
        with open(main_training, 'r') as f:
            for line in f:
                all_examples.append(json.loads(line))
        print(f"   Loaded {len(all_examples)} main examples")

    # Add terminology training
    term_training = Path('/mnt/d/productavailability/training_data/terminology_training_4k.jsonl')
    if term_training.exists():
        with open(term_training, 'r') as f:
            for line in f:
                all_examples.append(json.loads(line))
        print(f"   Added 4,000 terminology examples")

    print(f"   Total: {len(all_examples)} examples")
    return all_examples

def format_for_training(examples: List[Dict]) -> List[Dict]:
    """Format data for fine-tuning"""
    formatted = []

    for ex in examples[:5000]:  # Limit for testing
        messages = ex['messages']

        # Build conversation
        text = ""
        for msg in messages:
            if msg['role'] == 'system':
                text += f"System: {msg['content']}\n"
            elif msg['role'] == 'user':
                text += f"User: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                text += f"Assistant: {msg['content']}\n"

        formatted.append({"text": text.strip()})

    return formatted

def train_with_transformers():
    """Train using standard Hugging Face Transformers"""
    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
            Trainer,
            DataCollatorForLanguageModeling,
            BitsAndBytesConfig
        )
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model, TaskType
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nInstalling missing packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "transformers", "datasets", "accelerate", "peft", "bitsandbytes"])
        # Try again
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
            Trainer,
            DataCollatorForLanguageModeling,
            BitsAndBytesConfig
        )
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model, TaskType

    print("\n" + "="*60)
    print("🚀 GPU FINE-TUNING (Simplified Version)")
    print("="*60)

    # Check GPU
    if not torch.cuda.is_available():
        print("❌ No GPU available!")
        return

    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Model selection for 6GB VRAM
    model_name = "microsoft/phi-2"  # 2.7B model, good for 6GB
    print(f"\n📦 Loading model: {model_name}")
    print("   (Optimized for 6GB VRAM)")

    # Quantization config for 6GB GPU
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )

    # Load model and tokenizer
    print("\n📦 Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )

    # Configure LoRA for efficient training
    print("\n🔧 Configuring LoRA adapters...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,  # Low rank for 6GB GPU
        lora_alpha=16,
        lora_dropout=0.1,
        bias="none",
        target_modules=["q_proj", "v_proj"]  # Minimal modules for memory
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Prepare data
    print("\n📊 Preparing dataset...")
    examples = prepare_training_data()
    formatted_data = format_for_training(examples)

    # Create dataset
    dataset = Dataset.from_list(formatted_data)

    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=256  # Short for 6GB GPU
        )

    print("   Tokenizing...")
    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    # Training arguments for 6GB GPU
    training_args = TrainingArguments(
        output_dir="./extraction_model_simple",
        num_train_epochs=1,
        per_device_train_batch_size=1,  # Tiny batch for 6GB
        gradient_accumulation_steps=8,   # Effective batch = 8
        warmup_steps=100,
        logging_steps=10,
        save_strategy="epoch",
        learning_rate=2e-4,
        fp16=True,  # Mixed precision
        optim="adamw_torch",
        gradient_checkpointing=True,  # Save memory
        report_to="none"
    )

    # Create trainer
    print("\n🏋️ Initializing trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    )

    # Train
    print("\n" + "="*60)
    print("🔥 Starting training...")
    print(f"   Examples: {len(tokenized_dataset)}")
    print(f"   Batch size: 1 (accumulated: 8)")
    print(f"   Estimated time: 15-30 minutes")
    print("="*60 + "\n")

    trainer.train()

    # Save
    print("\n💾 Saving model...")
    trainer.save_model("extraction_model_simple_final")
    tokenizer.save_pretrained("extraction_model_simple_final")

    print("\n✅ Training complete!")
    print("   Model saved to: extraction_model_simple_final/")

    return model, tokenizer

def test_model(model, tokenizer):
    """Test the trained model"""
    print("\n" + "="*60)
    print("🧪 Testing trained model...")
    print("="*60)

    test_cases = [
        {
            "context": "Product 46961 has UPC 10026102469610",
            "question": "What's the product code?"
        },
        {
            "context": "Product 46888, brand PYREX",
            "question": "What's the UPC?"
        }
    ]

    for test in test_cases:
        prompt = f"Context: {test['context']}\nQuestion: {test['question']}\nAnswer:"

        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=100,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response}")

def main():
    print("🚀 Simplified GPU Fine-Tuning")
    print("="*60)
    print("This version uses standard libraries for stability")
    print("No Unsloth required!")
    print("="*60)

    # Check environment
    if not torch.cuda.is_available():
        print("\n❌ GPU not available!")
        print("Please ensure CUDA is properly installed")
        return

    try:
        # Train
        model, tokenizer = train_with_transformers()

        # Test
        if model:
            test_model(model, tokenizer)

        print("\n" + "="*60)
        print("🎉 SUCCESS!")
        print("Your model is trained and ready")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure packages are installed:")
        print("   pip install transformers datasets accelerate peft bitsandbytes")
        print("2. Try reducing batch_size or max_length if OOM")
        print("3. Check CUDA with: python3 -c 'import torch; print(torch.cuda.is_available())'")

if __name__ == "__main__":
    main()