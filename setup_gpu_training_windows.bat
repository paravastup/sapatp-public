@echo off
REM GPU Training Setup for Windows
echo ========================================
echo GPU Fine-Tuning Setup for Windows
echo ========================================

REM Check Python
echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check GPU
echo.
echo Checking GPU...
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
if errorlevel 1 (
    echo ERROR: NVIDIA GPU not detected!
    pause
    exit /b 1
)

echo GPU detected!

REM Install PyTorch with CUDA
echo.
echo Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

REM Install dependencies
echo.
echo Installing training dependencies...
pip install transformers datasets accelerate peft bitsandbytes

REM Install Unsloth
echo.
echo Installing Unsloth...
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

REM Additional packages
echo.
echo Installing additional packages...
pip install trl xformers sentencepiece protobuf

REM Verify
echo.
echo Verifying installation...
python -c "import torch; print(f'PyTorch installed: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo.
echo ========================================
echo Setup complete!
echo Run: python scripts\gpu_finetune_extraction.py
echo ========================================
pause