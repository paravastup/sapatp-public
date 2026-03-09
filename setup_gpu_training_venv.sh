#!/bin/bash
# GPU Training Setup with Virtual Environment (Recommended approach)

echo "🚀 Setting up GPU Fine-Tuning Environment (Virtual Environment)"
echo "============================================================"

# Check GPU
echo "Checking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || {
    echo "❌ No NVIDIA GPU detected!"
    exit 1
}
echo "✅ GPU detected!"

# Create virtual environment
echo -e "\n📦 Creating Python virtual environment..."
if [ ! -d "venv_gpu" ]; then
    python3 -m venv venv_gpu
    echo "✅ Virtual environment created: venv_gpu"
else
    echo "✅ Virtual environment already exists: venv_gpu"
fi

# Activate virtual environment
echo -e "\n🔧 Activating virtual environment..."
source venv_gpu/bin/activate

# Upgrade pip
echo -e "\n📦 Upgrading pip..."
pip install --upgrade pip

# Install PyTorch with CUDA
echo -e "\n📦 Installing PyTorch with CUDA support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install training dependencies
echo -e "\n📦 Installing training dependencies..."
pip install transformers datasets accelerate peft bitsandbytes

# Install Unsloth
echo -e "\n📦 Installing Unsloth (may take a few minutes)..."
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
    print('✅ Unsloth installed successfully')
except:
    print('⚠️  Unsloth not found - manual installation may be needed')

try:
    import transformers
    print(f'✅ Transformers {transformers.__version__} installed')
except:
    print('⚠️  Transformers not installed')
"

echo -e "\n============================================================"
echo "✨ Setup complete!"
echo ""
echo "IMPORTANT: Always activate the virtual environment before training:"
echo "  source venv_gpu/bin/activate"
echo ""
echo "Then run:"
echo "  python3 scripts/gpu_finetune_extraction.py"
echo ""
echo "To deactivate when done:"
echo "  deactivate"
echo "============================================================"