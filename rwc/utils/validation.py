"""Input validation utilities for RWC"""
import os
from pathlib import Path
from typing import Optional

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    '.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.opus'
}

# Max file size: 50MB
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024


class ValidationError(ValueError):
    """Raised when input validation fails"""
    pass


def validate_audio_file_path(file_path: str, must_exist: bool = True) -> Path:
    """
    Validate audio file path.

    Args:
        file_path: Path to audio file
        must_exist: If True, file must exist

    Returns:
        Path object

    Raises:
        ValidationError: If validation fails
    """
    try:
        path = Path(file_path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(f"Invalid file path: {e}")

    if must_exist and not path.exists():
        raise ValidationError(f"File not found: {file_path}")

    if must_exist and not path.is_file():
        raise ValidationError(f"Not a file: {file_path}")

    # Check file extension
    if path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        raise ValidationError(
            f"Unsupported audio format: {path.suffix}. "
            f"Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
        )

    # Check file size
    if must_exist:
        file_size = path.stat().st_size
        if file_size > MAX_AUDIO_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = MAX_AUDIO_FILE_SIZE / (1024 * 1024)
            raise ValidationError(
                f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)"
            )

        if file_size == 0:
            raise ValidationError("File is empty")

    return path


def validate_model_path(model_path: str) -> Path:
    """
    Validate model file path.

    Args:
        model_path: Path to model file

    Returns:
        Path object

    Raises:
        ValidationError: If validation fails
    """
    try:
        path = Path(model_path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(f"Invalid model path: {e}")

    if not path.exists():
        raise ValidationError(f"Model not found: {model_path}")

    if not path.is_file():
        raise ValidationError(f"Not a file: {model_path}")

    # Check file extension
    valid_extensions = {'.pth', '.pt', '.onnx'}
    if path.suffix.lower() not in valid_extensions:
        raise ValidationError(
            f"Invalid model format: {path.suffix}. "
            f"Expected: {', '.join(valid_extensions)}"
        )

    return path


def validate_pitch_change(pitch: int) -> int:
    """
    Validate pitch change parameter.

    Args:
        pitch: Pitch change in semitones

    Returns:
        Validated pitch value

    Raises:
        ValidationError: If out of range
    """
    if not isinstance(pitch, int):
        raise ValidationError(f"Pitch must be integer, got {type(pitch).__name__}")

    if pitch < -24 or pitch > 24:
        raise ValidationError(f"Pitch out of range: {pitch} (must be -24 to 24)")

    return pitch


def validate_index_rate(rate: float) -> float:
    """
    Validate index rate parameter.

    Args:
        rate: Index rate (0.0 to 1.0)

    Returns:
        Validated rate value

    Raises:
        ValidationError: If out of range
    """
    if not isinstance(rate, (int, float)):
        raise ValidationError(f"Rate must be numeric, got {type(rate).__name__}")

    rate = float(rate)

    if rate < 0.0 or rate > 1.0:
        raise ValidationError(f"Rate out of range: {rate} (must be 0.0 to 1.0)")

    return rate


def validate_audio_device_id(device_id: int, max_devices: int = 100) -> int:
    """
    Validate audio device ID.

    Args:
        device_id: Device ID
        max_devices: Maximum expected devices

    Returns:
        Validated device ID

    Raises:
        ValidationError: If invalid
    """
    if not isinstance(device_id, int):
        raise ValidationError(f"Device ID must be integer, got {type(device_id).__name__}")

    if device_id < 0 or device_id >= max_devices:
        raise ValidationError(f"Device ID out of range: {device_id} (0-{max_devices-1})")

    return device_id


def validate_pipewire_device_id(device_id: Optional[int]) -> Optional[int]:
    """
    Validate PipeWire device/node ID.

    Args:
        device_id: PipeWire device/node ID (can be None)

    Returns:
        Validated device ID or None

    Raises:
        ValidationError: If invalid
    """
    if device_id is None:
        return None

    if not isinstance(device_id, int):
        raise ValidationError(
            f"PipeWire device ID must be integer or None, got {type(device_id).__name__}"
        )

    if device_id < 0:
        raise ValidationError(f"PipeWire device ID must be non-negative, got {device_id}")

    return device_id


def validate_sample_rate(rate: int) -> int:
    """
    Validate audio sample rate.

    Args:
        rate: Sample rate in Hz

    Returns:
        Validated rate

    Raises:
        ValidationError: If invalid
    """
    if not isinstance(rate, int):
        raise ValidationError(f"Sample rate must be integer, got {type(rate).__name__}")

    valid_rates = {8000, 16000, 22050, 24000, 32000, 44100, 48000, 88200, 96000, 192000}

    if rate not in valid_rates:
        raise ValidationError(
            f"Invalid sample rate: {rate}. "
            f"Valid rates: {', '.join(map(str, sorted(valid_rates)))}"
        )

    return rate


def validate_channels(channels: int) -> int:
    """
    Validate number of audio channels.

    Args:
        channels: Number of channels

    Returns:
        Validated channels

    Raises:
        ValidationError: If invalid
    """
    if not isinstance(channels, int):
        raise ValidationError(f"Channels must be integer, got {type(channels).__name__}")

    if channels < 1 or channels > 8:
        raise ValidationError(f"Channels out of range: {channels} (must be 1-8)")

    return channels
