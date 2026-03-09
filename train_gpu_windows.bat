@echo off
REM Simple GPU Training Script for Windows
REM Run this in Windows Command Prompt or PowerShell

echo ============================================
echo GPU Training Setup for Windows
echo ============================================

cd /d D:\demoproject

REM Create virtual environment if it doesn't exist
if not exist "venv_windows" (
    echo Creating virtual environment...
    python -m venv venv_windows
)

REM Activate virtual environment
echo Activating virtual environment...
call venv_windows\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install packages one by one to avoid conflicts
echo.
echo Installing PyTorch with CUDA...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo Installing transformers...
pip install transformers==4.36.0

echo.
echo Installing additional packages...
pip install datasets accelerate==0.25.0 peft==0.7.0 bitsandbytes

REM Run the training script
echo.
echo ============================================
echo Starting GPU Training
echo ============================================
python scripts\train_basic_gpu.py

echo.
echo Training complete!
pause