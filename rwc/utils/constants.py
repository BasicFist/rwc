"""
Constants for RWC
Centralized constants to avoid magic numbers throughout the codebase
"""
from typing import Set

# Audio Processing Constants
DEFAULT_SAMPLE_RATE: int = 48000  # Hz
DEFAULT_CHANNELS: int = 2  # Stereo
DEFAULT_CHUNK_SIZE: int = 1024  # Buffer size
AUDIO_FORMAT_FLOAT32: str = 'float32'
BYTES_PER_SAMPLE_INT16: int = 2  # s16le format

# Valid sample rates
VALID_SAMPLE_RATES: Set[int] = {
    8000, 16000, 22050, 24000, 32000,
    44100, 48000, 88200, 96000, 192000
}

# Audio Channel Limits
MIN_CHANNELS: int = 1
MAX_CHANNELS: int = 8

# Chunk Size Limits
MIN_CHUNK_SIZE: int = 64
MAX_CHUNK_SIZE: int = 8192

# File Size Limits
MAX_AUDIO_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
MAX_MODEL_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB

# Audio Formats
SUPPORTED_AUDIO_EXTENSIONS: Set[str] = {
    '.wav', '.mp3', '.flac', '.m4a',
    '.aac', '.ogg', '.opus'
}

# Model Formats
SUPPORTED_MODEL_EXTENSIONS: Set[str] = {
    '.pth', '.pt', '.onnx'
}

# Conversion Parameters
DEFAULT_PITCH_CHANGE: int = 0  # semitones
MIN_PITCH_CHANGE: int = -24
MAX_PITCH_CHANGE: int = 24

DEFAULT_INDEX_RATE: float = 0.75
MIN_INDEX_RATE: float = 0.0
MAX_INDEX_RATE: float = 1.0

# Audio Device Limits
MAX_AUDIO_DEVICES: int = 100

# Meter Display
DEFAULT_METER_REFRESH: float = 0.1  # seconds
METER_BAR_WIDTH: int = 30
METER_MAX_RMS: float = 0.2  # Normalization factor
METER_EPSILON: float = 1e-8  # Prevent log(0)

# API Configuration
DEFAULT_API_HOST: str = '127.0.0.1'
DEFAULT_API_PORT: int = 5000
DEFAULT_API_WORKERS: int = 4
DEFAULT_API_TIMEOUT: int = 120  # seconds

# WebUI Configuration
DEFAULT_WEBUI_PORT: int = 7865

# Timeout Values (seconds)
SUBPROCESS_TIMEOUT: int = 60
MODEL_LOAD_TIMEOUT: int = 30
CONVERSION_TIMEOUT: int = 300  # 5 minutes

# Processing
SILENCE_THRESHOLD: float = 0.01  # RMS threshold for silence detection

# Error Messages
ERROR_MESSAGES = {
    'model_not_found': "Model file not found: {path}",
    'audio_not_found': "Audio file not found: {path}",
    'invalid_format': "Unsupported file format: {format}",
    'file_too_large': "File too large: {size}MB (max: {max}MB)",
    'invalid_pitch': "Pitch out of range: {pitch} (must be {min} to {max})",
    'invalid_rate': "Rate out of range: {rate} (must be {min} to {max})",
    'conversion_failed': "Voice conversion failed",
    'model_load_failed': "Failed to load model",
    'cuda_not_available': "CUDA not available, using CPU",
    'invalid_device': "Invalid audio device ID: {device_id}",
}

# Log Messages
LOG_MESSAGES = {
    'model_loaded': "Model loaded successfully: {model}",
    'conversion_started': "Starting conversion: {input} -> {output}",
    'conversion_completed': "Conversion completed in {duration:.2f}s",
    'realtime_started': "Real-time conversion started",
    'realtime_stopped': "Real-time conversion stopped",
    'api_started': "API server started on {host}:{port}",
    'webui_started': "WebUI started on port {port}",
}

# Directory Paths
DEFAULT_MODELS_DIR: str = "models"
DEFAULT_CONFIG_PATH: str = "rwc/config.ini"
DEFAULT_LOG_DIR: str = "logs"
DEFAULT_TEMP_DIR: str = "/tmp"

# Feature Flags
ENABLE_CUDA: bool = True
ENABLE_RMVPE: bool = True
ENABLE_METRICS: bool = False
ENABLE_DEBUG_LOGGING: bool = False
