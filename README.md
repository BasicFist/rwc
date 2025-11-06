# RWC - Real-time Voice Conversion

RWC is a real-time voice conversion project based on RVC (Retrieval-based Voice Conversion) technology that provides capabilities for converting voice in real-time using advanced AI models. This project is designed to provide seamless voice conversion for various applications.

## Overview

RWC (Real-time Voice Conversion) is a voice conversion system built on top of the RVC framework to provide real-time conversion of voice input using state-of-the-art machine learning models. The system is designed to be highly configurable and suitable for both research and production use.

## Features

- Real-time voice conversion based on RVC framework
- Low latency processing
- High-quality voice output
- Configurable conversion parameters
- API support for integration
- Command-line interface
- GPU acceleration support (NVIDIA CUDA)
- Pre-trained model support
- Web-based GUI interface

## Requirements

- Ubuntu 22.04 or 24.04 LTS
- Python 3.9 or higher
- NVIDIA GPU with CUDA support (recommended: RTX series or Quadro RTX 5000)
- At least 8GB RAM, 16GB+ recommended
- 100GB+ free disk space for models

## Installation

### Step 1: System Dependencies (requires sudo)

```bash
sudo apt update
sudo apt install -y build-essential python3-dev libssl-dev libsndfile1 libsndfile1-dev ffmpeg git
```

### Step 2: Clone and Setup Python Environment

```bash
cd /path/to/your/projects
git clone https://github.com/BasicFist/rwc.git
cd rwc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Verify GPU Support

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Test PyTorch with CUDA
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

## Usage

### Command Line Interface

Convert audio using the CLI:

```bash
# Activate virtual environment
source venv/bin/activate

# Run conversion
rwc convert --input path/to/input.wav --model path/to/model.pth --output output.wav --pitch-change 12 --index-rate 0.85
```

Start the API server:

```bash
# Activate virtual environment
source venv/bin/activate

# Start API server
rwc serve-api --host 0.0.0.0 --port 5000
```

Start the WebUI:

```bash
# Activate virtual environment
source venv/bin/activate

# Start WebUI
rwc serve-webui --port 7865
```

### Download Models

Download required models:

```bash
# Activate virtual environment
source venv/bin/activate

# Download models
rwc download-models
```

Or use the download script:

```bash
bash download_models.sh
```

### Direct Python Usage

```python
from rwc.core import VoiceConverter

# Initialize converter with model
converter = VoiceConverter("path/to/model.pth")

# Convert voice
result = converter.convert_voice(
    input_audio_path="input.wav",
    output_audio_path="output.wav",
    pitch_change=12,
    index_rate=0.85
)
```

## Project Structure

```
rwc/
├── rwc/                    # Main package
│   ├── core/               # Core voice conversion logic
│   ├── utils/              # Utility functions
│   ├── api/                # API endpoints
│   ├── cli/                # Command line interface
│   └── tests/              # Test files
├── RVC_DEPLOYMENT_GUIDE.md # Complete deployment guide for RVC-based system
├── download_models.sh      # Script to download required models
├── start_rwc.sh            # Startup script
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables example
├── .gitignore             # Git ignore patterns
└── README.md              # This file
```

## RVC Foundation

This project is built on the Retrieval-based Voice Conversion (RVC) framework. For detailed deployment instructions, system requirements, and optimization for your specific hardware (like NVIDIA Quadro RTX 5000), please refer to the [RVC_DEPLOYMENT_GUIDE.md](RVC_DEPLOYMENT_GUIDE.md) file included in this repository.

## API Endpoints

When running the API server:

- `GET /health` - Health check
- `POST /convert` - Convert voice
- `GET /models` - List available models
- `GET /` - Home endpoint with system info

## Web Interface

The RWC WebUI is accessible at `http://localhost:7865` when running the web interface.

## Performance Expectations

- Inference (voice conversion): 2-5 minutes per 30 seconds of audio
- Real-time conversion: 30-50ms latency (live microphone input)
- VRAM usage: 4-10GB (leaves 6-12GB headroom)
- System RAM: Minimal (<2GB for RWC operations)

Your Quadro RTX 5000 provides exceptional performance—significantly faster than consumer RTX 3060 (12GB) with professional grade stability.

## Troubleshooting

- If CUDA is not available after installation, ensure the NVIDIA drivers and CUDA are properly installed
- If model downloads fail, check your internet connection and authentication with HuggingFace
- For audio format issues, ensure input files are in a supported format (WAV, MP3, etc.)

## Contributing

Please read the contributing guidelines (to be added) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the RVC (Retrieval-based Voice Conversion) framework
- Inspired by various real-time voice conversion projects