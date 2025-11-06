# RVC v2 Ubuntu Deployment: Complete Roadmap for HP ZBook P53

This is a comprehensive step-by-step deployment guide tailored specifically for Ubuntu on your HP ZBook P53 with NVIDIA Quadro
RTX 5000 and 64GB RAM. Your system is ideally configured for this deployment.

## Pre-Deployment System Verification

Before starting, verify your system meets all requirements by running these commands:

```bash
# Check Ubuntu version
lsb_release -a

# Verify GPU presence
lspci | grep -i nvidia

# Check CUDA support (if CUDA already installed)
nvidia-smi

# Verify Python version
python3 --version

# Check disk space
df -h ~/
```

For your system:
- ✅ Ubuntu (confirm 22.04 LTS or 24.04 LTS)
- ✅ NVIDIA Quadro RTX 5000 detected
- ✅ CUDA Compute Capability 7.5 (Turing-based)
- ✅ 16GB GDDR6 VRAM available
- ✅ 64GB system RAM
- Recommended: 100GB+ free disk space

## Phase 1: System Preparation (10 minutes)

Update all system packages and install essential dependencies:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build tools
sudo apt install build-essential python3-dev libssl-dev -y

# Install audio libraries (required for RVC)
sudo apt install libsndfile1 libsndfile1-dev -y

# Install FFmpeg (audio processing)
sudo apt install ffmpeg -y

# Install Git (for cloning repository)
sudo apt install git -y
```

Verification: All commands should complete without errors. If you see dependency conflicts, run `sudo apt autoremove` and `sudo apt autoremove`.

## Phase 2: CUDA & NVIDIA Drivers Installation (25-40 minutes)

### Step 1: Verify GPU Detection
```bash
lspci | grep -i nvidia
```
Expected output: Shows NVIDIA Quadro RTX 5000

### Step 2: Install CUDA Toolkit 12.4

For Ubuntu 22.04:
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda cuda-toolkit -y
```

For Ubuntu 24.04:
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda cuda-toolkit -y
```

Installation time: 10-15 minutes. This installs both drivers and CUDA toolkit.

### Step 3: Configure CUDA Environment Variables
```bash
# Add CUDA to PATH and LD_LIBRARY_PATH
echo 'export PATH="/usr/local/cuda/bin:$PATH"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"' >> ~/.bashrc

# Apply changes immediately
source ~/.bashrc
```

### Step 4: Verify CUDA Installation
```bash
# Check CUDA compiler
nvcc -V
```
Should show: "CUDA compilation tools, release 12.4"

Troubleshooting: If nvcc not found, try rebooting: `sudo reboot`

## Phase 3: Python Environment Setup (15-20 minutes)

### Step 1: Create Python Virtual Environment
```bash
# Create RVC directory
mkdir -p ~/rvc
cd ~/rvc

# Create virtual environment (Python 3.10 or 3.11 recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (prompt should show (venv) prefix)
```

Critical: Always run `source venv/bin/activate` before working with RVC.

### Step 2: Install PyTorch with CUDA Support
```bash
# Install PyTorch, torchvision, torchaudio with CUDA 12.4 support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```
Installation time: 10-15 minutes

### Step 3: Verify PyTorch Installation
```bash
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0)}')"
```

Expected output:
```
CUDA available: True
Device: NVIDIA Quadro RTX 5000
```

If you see CUDA available: False, go to "Troubleshooting" section.

## Phase 4: RVC Installation (20-30 minutes)

### Step 1: Clone RVC Repository
```bash
# Make sure you're in the venv-activated shell
source ~/rvc/venv/bin/activate

# Navigate to RVC directory
cd ~/rvc

# Clone official RVC repository
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git .
# (Note the dot at end—clones into current directory)
```

### Step 2: Install Python Dependencies
```bash
# Make sure venv is activated
source venv/bin/activate

# Install all RVC dependencies
pip install -r requirements.txt
```
Installation time: 5-10 minutes

### Step 3: Fix Common Dependency Issues
```bash
# Upgrade protobuf (common compatibility issue)
pip install --upgrade protobuf

# Install chardet for encoding issues
pip install chardet

# Install correct librosa version
pip install librosa==0.10.0
```

### Step 4: Verify Installation
```bash
python3 -c "import gradio; import torch; print('✓ Installation successful')"
```

If you see ✓ Installation successful, you're ready for models.

## Phase 5: Download ML Models (30-40 minutes)

RVC requires pre-trained models. Install huggingface-cli first:
```bash
pip install huggingface-hub
```

Then download all required models:
```bash
# Create models directory
mkdir -p ~/rvc/models

# Download HuBERT base model (used for feature extraction)
huggingface-cli download fishaudio/hubert_base.pt --local-dir ~/rvc/models/hubert_base

# Download vocoder models (used for audio synthesis)
huggingface-cli download RinaChanNAI/VocoderModels --local-dir ~/rvc/models/pretrained

# Download UVR5 vocal separators (used for audio preprocessing)
huggingface-cli download Rejekts/uvr-models --local-dir ~/rvc/models/uvr5_weights
```

Download time: 30-40 minutes total (depends on internet speed). Models are ~5-10GB combined.

## Phase 6: Launch & Test (5 minutes)

### Step 1: Start the WebUI Server
```bash
# Make sure you're in ~/rvc with venv activated
source ~/rvc/venv/bin/activate
cd ~/rvc

# Launch RVC WebUI
python3 infer-web.py
```

Expected output:
```
* Running on local URL: http://localhost:7865
* To create a public link, set `share=True` in `launch()`
```

### Step 2: Access Web Interface
Open your browser and navigate to: **http://localhost:7865**

You should see the RVC WebUI with tabs for:
- Voice Conversion (Inference)
- Real-Time Voice Conversion
- Model Training
- Feature Index
- Model Manager

### Step 3: Test Basic Conversion
1. Go to "Voice Conversion" tab
2. Upload a sample audio file (WAV/MP3, 10-30 seconds)
3. Select a pre-trained .pth model from dropdown
4. Click "Convert"
5. Listen to output

Success: If you hear converted audio, deployment is complete.

## One-Click Deploy Script

Save this as `~/deploy_rvc.sh`:

```bash
#!/bin/bash
set -e

echo "=== RVC v2 Ubuntu Automated Deployment ==="
echo

# Phase 1: System Update
echo "Phase 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3-dev libssl-dev libsndfile1 libsndfile1-dev ffmpeg git

# Phase 2: CUDA
echo "Phase 2: Installing CUDA Toolkit 12.4..."
UBUNTU_VERSION=$(lsb_release -rs | sed 's/\([0-9]\+\)\.\([0-9]\+\)/\1\2/')
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu${UBUNTU_VERSION}/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update && sudo apt install -y cuda cuda-toolkit

# Configure CUDA
echo 'export PATH="/usr/local/cuda/bin:$PATH"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"' >> ~/.bashrc
source ~/.bashrc

# Phase 3: Python Environment
echo "Phase 3: Creating Python virtual environment..."
mkdir -p ~/rvc && cd ~/rvc
python3 -m venv venv
source venv/bin/activate

# Phase 4: PyTorch
echo "Phase 4: Installing PyTorch with CUDA 12.4..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Phase 5: RVC
echo "Phase 5: Installing RVC..."
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git . 2>/dev/null || true
pip install -r requirements.txt
pip install --upgrade protobuf chardet librosa==0.10.0

# Phase 6: Models
echo "Phase 6: Downloading models..."
pip install huggingface-hub
mkdir -p ~/rvc/models
huggingface-cli download fishaudio/hubert_base.pt --local-dir ~/rvc/models/hubert_base
huggingface-cli download RinaChanNAI/VocoderModels --local-dir ~/rvc/models/pretrained
huggingface-cli download Rejekts/uvr-models --local-dir ~/rvc/models/uvr5_weights

echo
echo "✓ Deployment complete!"
echo "To start RVC: source ~/rvc/venv/bin/activate && python3 ~/rvc/infer-web.py"
echo "Then open: http://localhost:7865"
```

Run it:
```bash
chmod +x ~/deploy_rvc.sh
bash ~/deploy_rvc.sh
```

Total deployment time: 45-90 minutes (mostly automatic downloads).

## Troubleshooting Common Issues

**Issue: "CUDA not available"**
```bash
source ~/.bashrc
python3 -c "import torch; print(torch.cuda.is_available())"
```

If still False, reinstall CUDA:
```bash
sudo apt remove --purge cuda* && sudo apt install cuda -y
```

**Issue: "Out of memory" during training**
Reduce batch size from 16 to 8 in RVC training settings, or use smaller audio files (10-15 min instead of 30+ min).

**Issue: Port 7865 already in use**
Use different port:
```bash
python3 infer-web.py --server-name 127.0.0.1 --server-port 7866
```

**Issue: Models won't download from HuggingFace**
```bash
huggingface-cli login
# Enter your HuggingFace API token (create free account at huggingface.co)
```

**Issue: "ModuleNotFoundError" during pip install**
```bash
pip install --upgrade pip
pip install --upgrade -r requirements.txt --break-system-packages
```

## Post-Deployment: Daily Usage

After successful deployment, to use RVC daily:
```bash
# Open terminal
cd ~/rvc
source venv/bin/activate
python3 infer-web.py

# Open browser: http://localhost:7865
# Use interface to convert voices
```

To stop the server, press Ctrl+C in terminal.

## Performance Expectations on Your System

- Inference (voice conversion): 2-5 minutes per 30 seconds of audio
- Training: 90-180 minutes for 20-30 minutes of audio (200 epochs)
- Real-time conversion: 30-50ms latency (live microphone input)
- VRAM usage: 4-10GB (leaves 6-12GB headroom)
- System RAM: Minimal (<2GB for RVC operations)

Your Quadro RTX 5000 provides exceptional performance—significantly faster than consumer RTX 3060 (12GB) with professional grade stability.