#!/bin/bash
# Fix PyTorch/torchvision compatibility issue

echo "🔧 Fixing PyTorch/torchvision compatibility..."
echo "=============================================="

# Ensure we're in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv_gpu/bin/activate
fi

# Uninstall conflicting packages
echo -e "\n📦 Cleaning up existing installations..."
pip uninstall torch torchvision torchaudio -y

# Install specific compatible versions
echo -e "\n📦 Installing compatible PyTorch versions..."
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# Reinstall transformers
echo -e "\n📦 Reinstalling transformers..."
pip install transformers==4.36.0

# Install Unsloth without dependencies first
echo -e "\n📦 Installing Unsloth (no deps)..."
pip install --no-deps "unsloth @ git+https://github.com/unslothai/unsloth.git"

# Install other dependencies
echo -e "\n📦 Installing remaining packages..."
pip install datasets accelerate peft bitsandbytes trl xformers sentencepiece protobuf

# Test the installation
echo -e "\n🔍 Testing installation..."
python3 -c "
import torch
print(f'✅ PyTorch {torch.__version__} installed')
print(f'✅ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
try:
    import torchvision
    print(f'✅ Torchvision {torchvision.__version__} installed')
except Exception as e:
    print(f'❌ Torchvision error: {e}')
try:
    import transformers
    print(f'✅ Transformers {transformers.__version__} installed')
except Exception as e:
    print(f'❌ Transformers error: {e}')
"

echo -e "\n✨ Compatibility fix complete!"
echo "Now run: python3 scripts/gpu_finetune_extraction.py"