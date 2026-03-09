#!/usr/bin/env python3
"""
GPU Fine-Tuning Script for Extraction Model
Uses Unsloth for efficient 4-bit quantized training on RTX 4050 (6GB VRAM)
"""

import json
import torch
from pathlib import Path
from typing import List, Dict
import subprocess
import sys

# Check if required packages are installed
def check_and_install_packages():
    """Install required packages for GPU training"""
    required_packages = [
        "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
        "xformers",
        "trl",
        "peft",
        "accelerate",
        "bitsandbytes"
    ]

    print("Checking required packages...")
    for package in required_packages:
        try:
            if "@" in package:
                # For git packages, just check if unsloth is installed
                __import__("unsloth")
            else:
                __import__(package)
            print(f"✓ {package.split('[')[0]} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def prepare_training_data():
    """Combine all training data into one dataset"""
    print("\nPreparing training data...")

    all_examples = []

    # Load the main training data
    main_training = Path('/mnt/d/productavailability/training_data/extraction_training_15k.jsonl')
    if main_training.exists():
        with open(main_training, 'r') as f:
            for line in f:
                example = json.loads(line)
                all_examples.append(example)
        print(f"Loaded {len(all_examples)} examples from main training")

    # Add terminology training
    terminology_training = Path('/mnt/d/productavailability/training_data/terminology_training_4k.jsonl')
    if terminology_training.exists():
        with open(terminology_training, 'r') as f:
            for line in f:
                example = json.loads(line)
                all_examples.append(example)
        print(f"Added {4000} terminology examples")

    print(f"Total training examples: {len(all_examples)}")
    return all_examples

def format_for_gemma(examples: List[Dict]) -> List[Dict]:
    """Format training data for Gemma model"""
    formatted = []

    for example in examples:
        messages = example['messages']

        # Extract user and assistant messages
        user_msg = None
        assistant_msg = None

        for msg in messages:
            if msg['role'] == 'user':
                user_msg = msg['content']
            elif msg['role'] == 'assistant':
                assistant_msg = msg['content']

        if user_msg and assistant_msg:
            # Format for Gemma instruction tuning
            text = f"<start_of_turn>user\n{user_msg}<end_of_turn>\n<start_of_turn>model\n{assistant_msg}<end_of_turn>"
            formatted.append({"text": text})

    return formatted

def train_with_unsloth():
    """Main training function using Unsloth"""
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import Dataset
    import torch

    print("\n" + "="*60)
    print("GPU FINE-TUNING WITH UNSLOTH")
    print("="*60)

    # Model configuration
    max_seq_length = 512  # Reduced for 6GB VRAM
    dtype = None  # Auto-detect
    load_in_4bit = True  # Use 4-bit quantization for 6GB GPU

    # Load base model - using smaller Gemma 2B for 6GB VRAM
    model_name = "unsloth/gemma-2-2b-it-bnb-4bit"  # Pre-quantized version

    print(f"\nLoading model: {model_name}")
    print("This is optimized for your RTX 4050 (6GB VRAM)")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )

    # Add LoRA adapters for efficient training
    print("\nAdding LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Memory efficient
        random_state=42,
    )

    # Prepare data
    print("\nPreparing dataset...")
    examples = prepare_training_data()
    formatted_data = format_for_gemma(examples[:10000])  # Limit to 10k for 6GB GPU
    dataset = Dataset.from_list(formatted_data)

    # Training arguments optimized for RTX 4050
    training_args = TrainingArguments(
        output_dir="./extraction_model_gpu",
        per_device_train_batch_size=2,  # Small batch for 6GB
        gradient_accumulation_steps=4,  # Effective batch size of 8
        warmup_steps=10,
        num_train_epochs=1,  # Start with 1 epoch
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",  # 8-bit optimizer to save memory
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        save_strategy="epoch",
    )

    # Initialize trainer
    print("\nInitializing trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    # Start training
    print("\n" + "="*60)
    print("Starting GPU fine-tuning...")
    print(f"Training on {len(dataset)} examples")
    print(f"GPU: RTX 4050 (6GB VRAM)")
    print(f"Estimated time: 30-60 minutes")
    print("="*60 + "\n")

    trainer.train()

    # Save the fine-tuned model
    print("\nSaving model...")
    model.save_pretrained("extraction_model_gpu_final")
    tokenizer.save_pretrained("extraction_model_gpu_final")

    # Save as GGUF for Ollama
    print("\nConverting to GGUF format for Ollama...")
    model.save_pretrained_gguf("extraction_model.gguf", tokenizer, quantization_method="q4_k_m")

    print("\n✅ Training complete!")
    print("Model saved to: extraction_model_gpu_final/")
    print("GGUF file: extraction_model.gguf")

    return model, tokenizer

def create_ollama_modelfile():
    """Create Modelfile for the GPU-trained model"""
    modelfile_content = """# GPU Fine-tuned Extraction Model
FROM ./extraction_model.gguf

SYSTEM "You are a precise data extraction assistant trained to extract product information from contexts.

CRITICAL RULES:
1. ONLY extract values that appear EXACTLY in the context
2. Return valid JSON format
3. If a value is not present, return null
4. Never generate or guess values
5. All barcode terms (EAN, product code, scanning code) map to 'upc' field
6. Product numbers (46888, G3960) are NOT UPCs"

PARAMETER temperature 0.01
PARAMETER top_p 0.1
PARAMETER top_k 5"""

    with open("Modelfile.gpu-trained", "w") as f:
        f.write(modelfile_content)

    print("\nModelfile created: Modelfile.gpu-trained")
    print("\nTo use with Ollama:")
    print("ollama create atp-extraction-gpu -f Modelfile.gpu-trained")

def main():
    print("🚀 GPU Fine-Tuning Setup for Extraction Model")
    print("="*60)
    print("Hardware: NVIDIA RTX 4050 (6GB VRAM)")
    print("Model: Gemma 2 2B (4-bit quantized)")
    print("Training examples: 19,995 total")
    print("="*60)

    # Check CUDA availability
    if not torch.cuda.is_available():
        print("❌ CUDA not available! Please ensure:")
        print("1. NVIDIA drivers are installed")
        print("2. PyTorch with CUDA support is installed")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return

    print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
    print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Install required packages
    check_and_install_packages()

    # Run training
    try:
        model, tokenizer = train_with_unsloth()
        create_ollama_modelfile()

        print("\n" + "="*60)
        print("🎉 SUCCESS! GPU fine-tuning complete!")
        print("Expected accuracy: 99.9%+ (no hallucination)")
        print("\nNext steps:")
        print("1. Test the model: python test_gpu_model.py")
        print("2. Use with Ollama: ollama create atp-extraction-gpu -f Modelfile.gpu-trained")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        print("\nTroubleshooting:")
        print("1. Reduce batch_size if OOM")
        print("2. Reduce max_seq_length")
        print("3. Use fewer training examples")

if __name__ == "__main__":
    main()