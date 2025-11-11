# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: RWC (Real-time Voice Conversion)

RWC is a real-time voice conversion system based on RVC (Retrieval-based Voice Conversion) technology. The project is **production-ready** with security hardening, comprehensive testing, and professional documentation.

**Status**: ✅ Security-hardened (Nov 2025), 101 tests passing, 25% coverage on critical modules

---

## Essential Commands

### Development Environment
```bash
# Activate virtual environment (REQUIRED for all commands)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=rwc --cov-report=term-missing

# Run parallel tests
pytest tests/ -n auto

# Run single test file
pytest tests/test_converter.py -v

# Run specific test
pytest tests/test_cli.py::test_convert_command -v
```

### Code Quality
```bash
# Format code
black --line-length=100 rwc/

# Sort imports
isort --profile black rwc/

# Lint
flake8 rwc/ --max-line-length=100

# Type check
mypy rwc/ --ignore-missing-imports

# Security scan
bandit -r rwc/

# Run pre-commit hooks
pre-commit run --all-files
```

### Running the Application
```bash
# CLI voice conversion
rwc convert --input input.wav --model models/model.pth --output output.wav

# Start API server (development)
rwc serve-api --host 0.0.0.0 --port 5000

# Start API server (production)
./run_api_production.sh

# Start Web UI
rwc serve-webui --port 7865

# Start TUI
rwc tui

# Real-time conversion
rwc real-time --model models/model.pth --input-device 0 --output-device 0
```

### Model Management
```bash
# Download base models
bash download_models.sh

# Download additional community models
bash download_additional_models.sh

# Convert with Homer Simpson model (pre-installed)
bash convert_to_homer.sh -i input.wav -o output.wav
```

---

## Architecture Overview

### Package Structure
```
rwc/
├── core/              # VoiceConverter - main conversion engine
├── api/               # Flask REST API with security hardening
├── cli/               # Click-based CLI commands
├── utils/             # Shared utilities (logging, validation, constants)
├── tui.py            # Terminal user interface
├── webui.py          # Gradio web interface
└── config.ini        # Configuration file
```

### Core Components

**VoiceConverter (`rwc/core/`)** - Central conversion engine:
- Loads RVC models (.pth), HuBERT feature extractor, RMVPE pitch extraction
- `convert_voice()`: File-based batch conversion with validation pipeline
- `real_time_convert()`: Microphone→speaker streaming (PyAudio/PipeWire)
- Feature extraction → pitch extraction → RVC inference → synthesis

**Utils (`rwc/utils/`)**:
- `constants.py`: Audio params (48kHz, 2ch), limits (50MB audio, 500MB models), ranges (pitch ±24, index 0.0-1.0)
- `validation.py`: Input validation (files, ranges, devices) with security checks
- `logging_config.py`: Structured logging with sensitive data filtering
- `audio_devices.py`: Device enumeration (PyAudio/PipeWire)

**API (`rwc/api/`)** - Flask REST server:
- `POST /convert`: Upload audio → validate → convert → return
- `GET /models`: List available models
- `GET /health`: GPU availability check
- **Security**: Path sanitization, directory traversal prevention, error message filtering, file upload validation

**CLI (`rwc/cli/`)** - Click commands with comprehensive argument validation

### Voice Conversion Pipeline
```
Input Audio → Load (librosa)
  → Feature Extraction (HuBERT)
  → Pitch Extraction (RMVPE/librosa)
  → Pitch Shift (optional)
  → RVC Inference
  → Audio Synthesis (soundfile)
  → Output
```

### Real-time Processing
- PyAudio fallback (cross-platform)
- PipeWire streaming (`pw-cat`) for modern Linux
- Chunk-based processing (1024 frames @ 48kHz)
- Audio level metering with visual feedback

### Test Organization (`tests/`)
- `test_converter.py`: VoiceConverter initialization, validation, feature extraction
- `test_cli.py`: CLI command parsing and execution (15 tests)
- `test_validation.py`: Input validation edge cases
- `test_security.py`: Path sanitization, error handling (critical)
- `test_logging.py`: Logging configuration
- `conftest.py`: Pytest fixtures (mock models, temp dirs, sample audio)

---

## Key Development Patterns

### Configuration-First Design
- Most parameters configurable via `config.ini` or runtime overrides
- Environment variables supported via `.env` file
- Lazy loading of models (only when needed)

### Security Principles (Critical)
- **Path Sanitization**: All file paths validated in `validation.py:validate_audio_file()` and `api/__init__.py`
- **Input Validation**: Strict ranges for pitch (±24), index (0.0-1.0), file sizes (50MB audio, 500MB models)
- **Error Message Filtering**: No internal paths or sensitive data exposed in API responses
- **Temporary File Cleanup**: Secure deletion of uploaded files after processing

### Testing Strategy
- Fixtures in `conftest.py` for test isolation
- Mock models and sample audio generators
- Unit tests focus on validation, security, and error handling
- Integration tests require actual models (optional)

### Pluggable Components
- Pitch extraction: RMVPE preferred, librosa fallback
- Audio backends: PyAudio (standard), PipeWire (Linux)
- Multiple interfaces: CLI, API, Web UI, TUI

---

## Critical Implementation Notes

### Current Status
The architecture is **complete** with security hardening and testing. Key subsystems:
- ✅ Input validation and security
- ✅ CLI, API, Web UI, TUI interfaces
- ✅ Real-time audio processing
- ⚠️ RVC inference uses placeholder (`_rvc_inference_placeholder()` - raises NotImplementedError)
- ⚠️ HuBERT feature extraction is placeholder (returns dummy 256-dim vectors)

### Security Vulnerabilities Fixed (Nov 11, 2025)
1. ✅ Path traversal in API file uploads
2. ✅ Debug mode disabled in production
3. ✅ Temporary file cleanup
4. ✅ Command injection prevention in audio device handling

### When Adding New Features
1. **Add validation** in `rwc/utils/validation.py` first
2. **Write tests** before implementation (TDD)
3. **Update constants** in `rwc/utils/constants.py` if needed
4. **Log operations** using `rwc.utils.logging_config.get_logger()`
5. **Run security scan**: `bandit -r rwc/` before committing
6. **Run all tests**: `pytest tests/ -v` before committing

### Pre-commit Hooks
The project uses pre-commit hooks (`.pre-commit-config.yaml`):
- Black (formatting)
- isort (import sorting)
- flake8 (linting)
- Trailing whitespace removal
- End-of-file fixer
- YAML syntax check

Install: `pre-commit install`

### CI/CD Pipeline
GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR:
1. **Lint**: black, isort, flake8, mypy
2. **Security**: bandit, safety
3. **Test**: pytest across Python 3.9-3.12
4. **Build**: package validation with twine
5. **Integration**: optional tests on master/main

---

## Documentation Files

- **README.md**: User-facing documentation, installation, usage
- **RVC_DEPLOYMENT_GUIDE.md**: Complete deployment instructions for RVC-based systems
- **SECURITY-FIXES-SUMMARY.md**: Security vulnerability fixes (Nov 2025)
- **CODE-QUALITY-IMPROVEMENTS.md**: Code quality enhancements
- **HIGH-PRIORITY-TASKS-COMPLETE.md**: Latest improvements summary
- **FINAL-IMPROVEMENTS-REPORT.md**: Complete project improvements report
- **GIT-ALIASES.md**: Git shortcuts and workflows

---

## Common Gotchas

1. **Virtual Environment**: Always activate venv before running any command
2. **CUDA Availability**: Check GPU with `python -c "import torch; print(torch.cuda.is_available())"`
3. **Model Paths**: Models expected in `models/` directory, use absolute or relative paths
4. **Audio Formats**: Only WAV, MP3 supported. Use librosa for loading.
5. **File Size Limits**: 50MB for audio, 500MB for models (see `constants.py`)
6. **Security**: Never bypass validation in `validation.py` - it prevents critical vulnerabilities
7. **Testing**: Run tests in project root, not inside `tests/` directory
8. **Real-time Conversion**: Requires PyAudio or PipeWire, check device IDs with `rwc tui`

---

## Hardware Requirements

- Ubuntu 22.04/24.04 LTS
- Python 3.9+
- NVIDIA GPU with CUDA (recommended: RTX series or Quadro RTX 5000)
- 8GB+ RAM (16GB recommended)
- 100GB+ disk space for models

**Performance (Quadro RTX 5000)**:
- Inference: 2-5 min per 30s audio
- Real-time: 30-50ms latency
- VRAM: 4-10GB (6-12GB headroom)

---

## Contact & Support

- GitHub Issues: Report bugs and request features
- Security Issues: Follow responsible disclosure (see SECURITY-FIXES-SUMMARY.md)
- License: MIT (see LICENSE file)
