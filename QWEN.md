# RWC (Real-time Voice Conversion) Project - Qwen Context

## Overview

RWC (Real-time Voice Conversion) is a real-time voice conversion system built on the RVC (Retrieval-based Voice Conversion) framework. It provides a unified interface for voice conversion using various AI models, with support for both file-based and real-time conversion. The project includes CLI tools, a REST API, a Gradio web interface, and a terminal-based TUI for comprehensive user interaction.

## Project Structure

```
rwc/
├── .env.example
├── .gitignore
├── convert_to_homer.sh
├── download_additional_models.sh
├── download_models.sh
├── pyproject.toml
├── README.md
├── requirements.txt
├── run_rwc_tui.sh
├── RVC_DEPLOYMENT_GUIDE.md
├── SECURITY.md
├── start_rwc.sh
├── test_input.wav
├── .git/
├── models/
│   ├── checkpoints/...
│   ├── community/...
│   └── ...
├── rwc/
│   ├── __init__.py
│   ├── config.ini
│   ├── tui.py
│   ├── webui.py
│   ├── api/
│   ├── cli/
│   ├── core/
│   ├── tests/
│   └── utils/
├── rwc.egg-info/
└── venv/
```

### Key Directories
- **`rwc/`**: Main source code package
- **`rwc/core/`**: Core voice conversion logic
- **`rwc/cli/`**: Command-line interface implementation
- **`rwc/api/`**: Flask-based REST API
- **`rwc/webui.py`**: Gradio-based web interface
- **`rwc/tui.py`**: Terminal User Interface
- **`models/`**: Directory for storing trained models
- **`scripts/`**: Utility scripts for download, setup, etc.

## Key Features

### Core Functionality
- **Real-time Voice Conversion**: Based on RVC framework with low latency processing
- **File-based Conversion**: Convert audio files using RVC models
- **Multiple Model Support**: Works with various RVC-compatible models
- **GPU Acceleration**: Leverages NVIDIA CUDA for accelerated processing
- **Advanced Pitch Extraction**: Optional RMVPE support for better quality

### Interface Options
- **CLI**: Command-line interface for scripting and automation
- **REST API**: Flask-based API for programmatic access
- **Web UI**: Gradio-based web interface for easy interaction
- **TUI**: Terminal User Interface with menu-driven navigation

### Configuration
- **Flexible Parameters**: Adjustable pitch change, index rate, and other settings
- **Model Management**: Automatic model discovery and selection
- **Audio Device Configuration**: Support for different input/output devices
- **Environment Variable Support**: Configurable via environment variables

## Technical Architecture

### Core Components
- **`VoiceConverter`**: Main class responsible for voice conversion using RVC models
- **PyTorch/Torchaudio**: Deep learning framework for AI models
- **Librosa**: Audio processing and analysis library
- **Gradio**: Web interface framework
- **Flask**: API server framework
- **Textual**: TUI framework

### Configuration File
The `rwc/config.ini` file defines default settings:
```
[MODEL_PATHS]
hubert_model_path = models/hubert_base/hubert_base.pt
rmvpe_model_path = models/rmvpe/rmvpe.pt
pretrained_dir = models/pretrained/pretrained/

[CONVERSION]
default_pitch_change = 0
default_index_rate = 0.75
use_rmvpe_by_default = true

[API]
default_host = 0.0.0.0
default_port = 5000
max_upload_size = 50MB

[WEBUI]
default_port = 7865
```

### Model Management
The system supports multiple model sources:
- Pre-trained models from RVC project
- Community models from Hugging Face
- Custom-trained models
- Homer Simpson model (pre-configured example)

## API Endpoints

The REST API provides the following endpoints:
- `GET /health` - Service health check
- `POST /convert` - Voice conversion endpoint
- `GET /models` - List available models
- `GET /` - Home endpoint with system info

## Usage Examples

### CLI Usage
```bash
# File conversion
rwc convert --input input.wav --model models/community/HomerSimpson/model.pth --output output.wav --pitch-change 12 --index-rate 0.85

# Start API server
rwc serve-api --host 0.0.0.0 --port 5000

# Start Web UI
rwc serve-webui --port 7865

# Start TUI
rwc tui

# Real-time conversion (from microphone)
rwc real-time --input-device 0 --model models/community/HomerSimpson/model.pth --output-device 0
```

### TUI Usage
```bash
# Launch TUI interface
python3 -m rwc.tui
```

The TUI provides:
- File-based conversion with adjustable parameters
- Real-time conversion setup
- Audio device listing
- Model selection interface
- Help and documentation

### Web UI Usage
```bash
# Launch web interface
python3 -m rwc.webui
```

The Web UI provides:
- Drag-and-drop audio upload
- Model selection from dropdown
- Adjustable pitch change and index rate sliders
- RMVPE toggle for enhanced pitch extraction
- Real-time conversion command generation

## Installation & Dependencies

### Prerequisites
- Python 3.9+
- NVIDIA GPU with CUDA support (recommended: RTX series or Quadro RTX 5000)
- Linux environment (Ubuntu 22.04 or 24.04 LTS recommended)

### Setup
```bash
# Install system dependencies
sudo apt install -y build-essential python3-dev libssl-dev libsndfile1 libsndfile1-dev ffmpeg git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Test GPU support
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Model Downloads
Download required models using:
```bash
# Basic models
bash download_models.sh

# Additional models (including Homer Simpson)
bash download_additional_models.sh

# Or via CLI
rwc download-models
```

## Development Guidelines

### Python Dependencies
Key dependencies include:
- `torch>=2.0.0` - PyTorch for deep learning
- `torchaudio>=2.0.0` - Audio processing
- `librosa>=0.10.0` - Music and audio analysis
- `gradio>=3.42.0` - Web interface framework
- `click>=8.0.0` - CLI framework
- `flask>=2.0.0` - API server framework

### Code Structure
- **Core Logic**: `rwc/core/` - Voice conversion implementation
- **API Endpoints**: `rwc/api/` - Flask API implementation
- **CLI Commands**: `rwc/cli/` - Click-based CLI commands
- **TUI Interface**: `rwc/tui.py` - Textual TUI implementation
- **Web Interface**: `rwc/webui.py` - Gradio web UI implementation
- **Utilities**: `rwc/utils/` - Helper functions and utilities

### Testing
The project includes:
- Unit tests in `tests/` directory
- Integration tests for core functionality
- CLI and API endpoint tests
- Mock implementations for external dependencies

## Security Considerations

- Input validation for all file uploads and API parameters
- Path sanitization to prevent directory traversal attacks
- Environment variable management for API keys
- Secure credential storage recommendations

## Configuration & Customization

### Environment Variables
- `LITELLM_MASTER_KEY`: Authentication key for LiteLLM API access
- Model paths and other configuration values can be overridden

### Custom Models
To use custom RVC models:
1. Place your `.pth` model file in the `models/` directory
2. Use the appropriate model path when calling conversion functions
3. Ensure the model is compatible with the RVC framework

## Troubleshooting

### Common Issues
- **CUDA unavailable**: Ensure NVIDIA drivers and CUDA toolkit are installed
- **Model files missing**: Run the appropriate download script
- **Audio device issues**: Verify available devices with audio utilities
- **Permission errors**: Check file permissions for model directory

### Helpful Commands
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"

# List available audio devices
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"

# Check available models
ls models/
```