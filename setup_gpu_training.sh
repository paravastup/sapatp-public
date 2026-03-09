#!/bin/bash
# Setup script for GPU fine-tuning environment

echo "🚀 Setting up GPU Fine-Tuning Environment"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python3 --version

# Check CUDA availability
echo -e "\nChecking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || {
    echo "❌ No NVIDIA GPU detected!"
    exit 1
}

echo -e "\n✅ GPU detected!"

# Install PyTorch with CUDA support
echo -e "\n📦 Installing PyTorch with CUDA support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install training dependencies
echo -e "\n📦 Installing training dependencies..."
pip install transformers datasets accelerate peft bitsandbytes

# Install Unsloth (the key library for efficient fine-tuning)
echo -e "\n📦 Installing Unsloth..."
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Install additional requirements
echo -e "\n📦 Installing additional packages..."
pip install trl xformers sentencepiece protobuf

# Verify installation
echo -e "\n🔍 Verifying installation..."
python3 -c "
import torch
print(f'✅ PyTorch {torch.__version__} installed')
print(f'✅ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')

try:
    import unsloth
    print('✅ Unsloth installed')
except:
    print('⚠️  Unsloth not found - manual installation may be needed')

try:
    import transformers
    print(f'✅ Transformers {transformers.__version__} installed')
except:
    print('⚠️  Transformers not installed')
"

echo -e "\n✨ Setup complete!"
echo "You can now run: python3 scripts/gpu_finetune_extraction.py"