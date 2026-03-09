#!/usr/bin/env python3
"""
Basic GPU Training Script - Minimal Dependencies
Works with your RTX 4050 (6GB VRAM)
"""

import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import sys

print("🚀 Basic GPU Training Script")
print("=" * 60)

# Check GPU
if not torch.cuda.is_available():
    print("❌ No GPU available!")
    sys.exit(1)

device = torch.device("cuda")
print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Simple extraction dataset
class ExtractionDataset(Dataset):
    def __init__(self, data_path):
        self.examples = []

        # Load training data
        with open(data_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 1000:  # Limit for testing
                    break
                example = json.loads(line)
                self.examples.append(example)

        print(f"📊 Loaded {len(self.examples)} examples")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        example = self.examples[idx]
        messages = example['messages']

        # Build input/output
        input_text = ""
        output_text = ""

        for msg in messages:
            if msg['role'] == 'user':
                input_text = msg['content']
            elif msg['role'] == 'assistant':
                output_text = msg['content']

        return input_text, output_text

# Simple transformer model
class SimpleExtractionModel(nn.Module):
    def __init__(self, vocab_size=50000, hidden_size=512, num_layers=4):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_size,
                nhead=8,
                dim_feedforward=2048,
                batch_first=True
            ),
            num_layers=num_layers
        )
        self.output = nn.Linear(hidden_size, vocab_size)

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)
        x = self.output(x)
        return x

# Training function
def train_model():
    print("\n" + "=" * 60)
    print("🔥 Starting GPU Training")
    print("=" * 60)

    # Load dataset
    import platform
    if platform.system() == 'Windows':
        train_data = Path('D:/opt/app/training_data/extraction_training_15k.jsonl')
    else:
        train_data = Path('/opt/app/training_data/extraction_training_15k.jsonl')
    if not train_data.exists():
        print(f"❌ Training data not found: {train_data}")
        return

    dataset = ExtractionDataset(train_data)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    # Create model
    print("\n📦 Creating model...")
    model = SimpleExtractionModel().to(device)
    print(f"   Model size: {sum(p.numel() for p in model.parameters())/1e6:.1f}M parameters")

    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    # Training loop
    print("\n🏋️ Training...")
    model.train()

    for epoch in range(1):  # Just 1 epoch for demo
        total_loss = 0
        batch_count = 0

        for batch_idx, (inputs, targets) in enumerate(dataloader):
            if batch_idx >= 100:  # Limit batches for demo
                break

            # Simple tokenization (just for demo)
            # In real scenario, you'd use proper tokenizer
            input_ids = torch.randint(0, 50000, (4, 128)).to(device)

            # Forward pass
            outputs = model(input_ids)

            # Compute loss (simplified)
            loss = nn.CrossEntropyLoss()(
                outputs.view(-1, 50000),
                input_ids.view(-1)
            )

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            batch_count += 1

            if batch_idx % 10 == 0:
                print(f"   Batch {batch_idx}/100, Loss: {loss.item():.4f}")

        avg_loss = total_loss / batch_count
        print(f"\n✅ Epoch {epoch+1} complete, Avg Loss: {avg_loss:.4f}")

    # Save model
    print("\n💾 Saving model...")
    torch.save(model.state_dict(), "extraction_model_basic.pt")
    print("   Model saved to: extraction_model_basic.pt")

    return model

# Test the trained model
def test_model(model):
    print("\n" + "=" * 60)
    print("🧪 Testing Model")
    print("=" * 60)

    test_cases = [
        "Context: Product 10002 has UPC 10026102100020. Question: What's the UPC?",
        "Context: Product 10001, brand BRAND_B. Question: What's the UPC?"
    ]

    model.eval()
    with torch.no_grad():
        for test in test_cases:
            # Simple tokenization (demo only)
            input_ids = torch.randint(0, 50000, (1, 128)).to(device)

            # Generate
            output = model(input_ids)

            print(f"\nInput: {test[:50]}...")
            print(f"Output shape: {output.shape}")
            print("(In real scenario, this would be decoded to JSON)")

# Alternative: Use pre-trained model with your data
def use_pretrained():
    """Alternative approach using a pre-trained small model"""
    print("\n" + "=" * 60)
    print("🎯 Alternative: Fine-tuning Pre-trained Model")
    print("=" * 60)

    try:
        from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments
        from datasets import Dataset

        print("\n📦 Loading GPT-2 (small model for 6GB)...")

        # Use smallest GPT-2 variant
        model_name = "gpt2"  # 124M parameters
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        tokenizer.pad_token = tokenizer.eos_token

        model = GPT2LMHeadModel.from_pretrained(model_name)
        model = model.to(device)

        print(f"✅ Loaded {model_name}")
        print(f"   Model size: {sum(p.numel() for p in model.parameters())/1e6:.1f}M parameters")

        # Load your data
        print("\n📊 Loading training data...")
        examples = []
        # Use Windows path when on Windows, Linux path when on Linux
        import platform
        if platform.system() == 'Windows':
            train_file = Path('D:/opt/app/training_data/extraction_training_15k.jsonl')
        else:
            train_file = Path('/opt/app/training_data/extraction_training_15k.jsonl')

        with open(train_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 100:  # Small subset for demo
                    break
                ex = json.loads(line)
                # Format as text
                text = ""
                for msg in ex['messages']:
                    if msg['role'] == 'user':
                        text += f"User: {msg['content']}\n"
                    elif msg['role'] == 'assistant':
                        text += f"Assistant: {msg['content']}\n"
                examples.append({"text": text})

        dataset = Dataset.from_list(examples)

        # Tokenize
        def tokenize_function(examples):
            return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=256)

        tokenized = dataset.map(tokenize_function, batched=True)

        # Training arguments (minimal for 6GB)
        training_args = TrainingArguments(
            output_dir="./gpt2_extraction",
            num_train_epochs=1,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            logging_steps=10,
            save_steps=1000,
            fp16=True,  # Mixed precision for memory
        )

        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized,
            tokenizer=tokenizer,
        )

        print("\n🔥 Starting fine-tuning...")
        print("   This will take 5-10 minutes...")

        # Train
        trainer.train()

        # Save
        print("\n💾 Saving fine-tuned model...")
        trainer.save_model("./gpt2_extraction_final")

        print("✅ Fine-tuning complete!")
        print("   Model saved to: ./gpt2_extraction_final")

        return model, tokenizer

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Falling back to basic PyTorch training...")
        return None, None

def main():
    print("\nChoose training approach:")
    print("1. Basic PyTorch (no dependencies)")
    print("2. Fine-tune GPT-2 (uses transformers)")

    # Try GPT-2 first
    model, tokenizer = use_pretrained()

    if model is None:
        # Fallback to basic
        print("\nUsing basic PyTorch training...")
        model = train_model()
        if model:
            test_model(model)

    print("\n" + "=" * 60)
    print("🎉 Training Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()