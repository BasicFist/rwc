# RWC - Real-time Voice Conversion

RWC is a real-time voice conversion project based on RVC (Retrieval-based Voice Conversion) technology that provides capabilities for converting voice in real-time using advanced AI models. This project is designed to provide seamless voice conversion for various applications.

## Overview

RWC (Real-time Voice Conversion) is a voice conversion system built on top of the RVC framework to provide real-time conversion of voice input using state-of-the-art machine learning models. The system is designed to be highly configurable and suitable for both research and production use.

## Features

- File-based voice conversion using RVC models (stable)
- Experimental live microphone pipeline (Phase 1)
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

## Configuration

The project can be configured through the `rwc/config.ini` file which allows customization of:
- Model paths and locations
- Default conversion parameters
- API and WebUI settings
- Performance options

You can also define environment variables in the `.env` file.

## API Endpoints

When running the API server:

- `GET /health` - Health check
- `POST /convert` - Convert voice
- `GET /models` - List available models
- `GET /` - Home endpoint with system info

## Web Interface

The RWC WebUI is a Gradio-based web interface accessible at `http://localhost:7865` when running the web interface. The interface provides:

- User-friendly drag-and-drop audio upload
- Model selection from available RVC models
- Adjustable parameters (pitch change, index rate)
- RMVPE toggle for enhanced pitch extraction
- Real-time conversion status updates
- Direct audio playback of results
- **NEW**: Real-time conversion tab for live microphone input

The real-time conversion tab allows you to configure options for live microphone conversion and provides the command to run for actual real-time conversion.

## Terminal User Interface (TUI)

The RWC system also provides a TUI (Terminal User Interface) for easier interaction:

```bash
rwc tui
```

The TUI provides:
- Interactive menu-driven interface
- File-based conversion functionality  
- Real-time conversion configuration
- Audio device listing
- Model listing and selection
- Help information
- Unified interface for all RWC features

## Microphone Support

RWC currently provides reliable file-based conversion. Live microphone support is available only as an experimental Phase 1 feature:

- PyAudio and PortAudio are required for microphone capture.
- Device compatibility is unverified; expect limited hardware coverage during this phase.
- Use file-based conversion for dependable results while live capture stabilizes.

## Performance Expectations

- File-based conversion: depends on model size and hardware; batch processing is recommended for throughput.
- Experimental live pipeline: expected end-to-end latency is currently 500–700 ms in Phase 1 builds.
- VRAM usage: 4-10GB (leaves 6-12GB headroom)
- System RAM: Minimal (<2GB for RWC operations)

## Additional Models and Datasets

The RWC system works with various pre-trained models and can be enhanced with additional datasets. Here are resources for obtaining more models and training data:

### Additional Pre-trained Models

The following repositories contain additional RVC-compatible models:

- [lj1995/VoiceConversionWebUI](https://huggingface.co/lj1995/VoiceConversionWebUI) - Original RVC models
- [auskf/RVC-beta3-test](https://huggingface.co/auskf/RVC-beta3-test) - Additional RVC models
- [Kit-Lemonfoot/kitlemonfoot_rvc_models](https://huggingface.co/Kit-Lemonfoot/kitlemonfoot_rvc_models) - Community models
- [therealvul/RVC-Models](https://huggingface.co/therealvul/RVC-Models) - More voice models
- [riptide2048/RVC-Models](https://huggingface.co/riptide2048/RVC-Models) - Additional models

To download additional models, use the additional download script:
```bash
bash download_additional_models.sh
```

### Popular Community Models on Hugging Face

Based on Hugging Face data, here are some popular community RVC models:

**Fictional Characters & Entertainment:**
- [sail-rvc/HomerSimpson2333333](https://huggingface.co/sail-rvc/HomerSimpson2333333) - Homer Simpson voice (8,970 downloads) - **SET UP IN THIS INSTALLATION**
- [sail-rvc/Hatsune_Miku__RVC_v2_](https://huggingface.co/sail-rvc/Hatsune_Miku__RVC_v2_) - Hatsune Miku voice (2,791 downloads)
- [sail-rvc/ArthurMorgan](https://huggingface.co/sail-rvc/ArthurMorgan) - Arthur Morgan from Red Dead Redemption (1,832 downloads)
- [sail-rvc/Jesse-Pinkman](https://huggingface.co/sail-rvc/Jesse-Pinkman) - Jesse Pinkman from Breaking Bad (1,727 downloads)
- [sail-rvc/Peter_Griffin__Family_Guy___RVC_V2__300_Epoch](https://huggingface.co/sail-rvc/Peter_Griffin__Family_Guy___RVC_V2__300_Epoch) - Peter Griffin from Family Guy

**Celebrities & Public Figures:**
- [sail-rvc/Donald_Trump__RVC_v2_](https://huggingface.co/sail-rvc/Donald_Trump__RVC_v2_) - Donald Trump voice (5,951 downloads)
- [sail-rvc/ArnoldSchwarzenegger](https://huggingface.co/sail-rvc/ArnoldSchwarzenegger) - Arnold Schwarzenegger voice (1,323 downloads)
- [sail-rvc/Ronaldo](https://huggingface.co/sail-rvc/Ronaldo) - Cristiano Ronaldo voice (2,273 downloads)
- [sail-rvc/Messi__RVC_V2__Crepe__-_200_Epochs_](https://huggingface.co/sail-rvc/Messi__RVC_V2__Crepe__-_200_Epochs_) - Lionel Messi voice (1,214 downloads)

### Using the Homer Simpson Model

The Homer Simpson model has been pre-downloaded as part of this setup. Here's how to use it:

1. **CLI**: Use the dedicated conversion script:
   ```bash
   bash convert_to_homer.sh -i input.wav -o output.wav
   ```

2. **Direct CLI**: Or use the rwc command directly:
   ```bash
   rwc convert --input input.wav --model models/community/HomerSimpson2333333/model.pth --output homer_output.wav --use-rmvpe
   ```

3. **Web Interface**: The model should appear in the dropdown when you refresh models in the Gradio interface.

### Using Community Models

To download and use these models:

1. Find a model on Hugging Face that interests you
2. Use the huggingface-cli to download:
   ```bash
   huggingface-cli download <username/model-name> --local-dir ./models/community/<model-name>
   ```
3. Use the model path in RWC for voice conversion

**Important Note:** Be mindful of ethical and legal considerations when using voice models of real people. Only use these for appropriate, non-malicious purposes and be aware that using celebrity voices commercially may require permission.

### Training Datasets

To train custom voice models for RVC, you would typically need:

- Clean audio recordings of the target voice (10-50 minutes of high-quality audio)
- Audio preprocessing with noise reduction
- Audio normalization and consistent formatting

### Model Types

RVC typically uses several types of models:

- **Hubert Base**: For semantic feature extraction
- **RMVPE**: For more accurate pitch extraction (alternative to Crepe)
- **Pre-trained vocoders**: For audio synthesis (e.g., D32k, D40k, D48k, G32k, G40k, G48k)
- **UVR5 models**: For audio separation tasks
- **Custom-trained models**: Trained on specific voices/speakers

### Download Additional Models

To download additional models that may be useful, use:
```bash
bash download_additional_models.sh
```

## Project Status & Documentation

**Status**: 🛠️ Phase 1 for live microphone support; file-based conversion is stable.

### Recent Improvements (2025-11-11)
- ✅ **Security**: All 4 critical vulnerabilities fixed (path traversal, debug mode, temp files, command injection)
- ✅ **Testing**: 101 tests, 100% passing, 25% coverage on critical modules
- ✅ **Quality**: Professional logging, constants, type hints, pre-commit hooks, CI/CD
- ✅ **Documentation**: Comprehensive guides for security, quality, and deployment

### Documentation Files
- **HIGH-PRIORITY-TASKS-COMPLETE.md** - Latest improvements summary
- **FINAL-IMPROVEMENTS-REPORT.md** - Complete project improvements report
- **SECURITY-FIXES-SUMMARY.md** - Security vulnerability fixes
- **CODE-QUALITY-IMPROVEMENTS.md** - Code quality enhancements
- **GIT-ALIASES.md** - Git shortcuts and commands
- **RVC_DEPLOYMENT_GUIDE.md** - Deployment instructions

### Quick Commands
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=rwc --cov-report=term-missing

# Start production API
./run_api_production.sh

# Git shortcuts (see GIT-ALIASES.md)
git log --oneline -10
git diff --stat
```

## Troubleshooting

- If CUDA is not available after installation, ensure the NVIDIA drivers and CUDA are properly installed
- If model downloads fail, check your internet connection and authentication with HuggingFace
- For audio format issues, ensure input files are in a supported format (WAV, MP3, etc.)
- For security best practices, see **SECURITY-FIXES-SUMMARY.md**
- For git workflows, see **GIT-ALIASES.md**

## Contributing

Please read the contributing guidelines (to be added) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the RVC (Retrieval-based Voice Conversion) framework
- Inspired by various real-time voice conversion projects