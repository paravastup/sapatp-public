#!/usr/bin/env python3
"""Quick GPU test to verify training will work"""

import subprocess
import sys

def test_gpu():
    print("🔍 GPU Training Compatibility Test")
    print("=" * 50)

    # Test 1: Check GPU visibility
    print("\n1. Checking GPU visibility...")
    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total',
                           '--format=csv,noheader'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        gpu_info = result.stdout.strip()
        print(f"   ✅ GPU Found: {gpu_info}")
    else:
        print("   ❌ No GPU detected")
        return False

    # Test 2: Check Python
    print("\n2. Checking Python version...")
    python_version = sys.version
    print(f"   ✅ Python: {python_version.split()[0]}")

    # Test 3: Try importing PyTorch
    print("\n3. Checking PyTorch...")
    try:
        import torch
        print(f"   ✅ PyTorch {torch.__version__} installed")

        # Test 4: Check CUDA
        print("\n4. Checking CUDA availability...")
        if torch.cuda.is_available():
            print(f"   ✅ CUDA is available")
            print(f"   ✅ CUDA version: {torch.version.cuda}")
            print(f"   ✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"   ✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

            # Test 5: Run simple GPU operation
            print("\n5. Testing GPU computation...")
            x = torch.rand(1000, 1000).cuda()
            y = torch.rand(1000, 1000).cuda()
            z = torch.matmul(x, y)
            print(f"   ✅ GPU computation successful")

            return True
        else:
            print("   ❌ CUDA not available in PyTorch")
            print("   Need to install: pip install torch --index-url https://download.pytorch.org/whl/cu118")
            return False

    except ImportError:
        print("   ❌ PyTorch not installed")
        print("\n📦 To install PyTorch with CUDA:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 50)
    if test_gpu():
        print("\n🎉 SUCCESS! Your system is ready for GPU training!")
        print("\nYou can train in either:")
        print("1. WSL2 (current environment) - Recommended ✅")
        print("   Run: ./setup_gpu_training.sh")
        print("\n2. Windows (need to open Windows terminal)")
        print("   Run: setup_gpu_training_windows.bat")
    else:
        print("\n⚠️  Setup needed before GPU training")
        print("Run: ./setup_gpu_training.sh (in WSL2)")
        print("Or: setup_gpu_training_windows.bat (in Windows)")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()