"""Tests for validation utilities"""
import pytest
from pathlib import Path
from rwc.utils.validation import (
    ValidationError,
    validate_audio_file_path,
    validate_model_path,
    validate_pitch_change,
    validate_index_rate,
    validate_audio_device_id,
    validate_pipewire_device_id,
    validate_sample_rate,
    validate_channels,
    SUPPORTED_AUDIO_FORMATS,
    MAX_AUDIO_FILE_SIZE,
)


class TestAudioFileValidation:
    """Test audio file path validation"""

    def test_valid_audio_file(self, sample_audio_file):
        """Should accept valid audio files"""
        result = validate_audio_file_path(str(sample_audio_file))
        assert result.exists()
        assert result.is_file()
        assert result.suffix == '.wav'

    def test_nonexistent_file(self, temp_dir):
        """Should reject nonexistent files"""
        nonexistent = temp_dir / "nonexistent.wav"
        with pytest.raises(ValidationError, match="not found"):
            validate_audio_file_path(str(nonexistent))

    def test_empty_file(self, temp_dir):
        """Should reject empty files"""
        empty = temp_dir / "empty.wav"
        empty.touch()
        with pytest.raises(ValidationError, match="empty"):
            validate_audio_file_path(str(empty))

    def test_oversized_file(self, temp_dir):
        """Should reject oversized files"""
        large = temp_dir / "large.wav"
        with open(large, 'wb') as f:
            f.write(b'x' * (MAX_AUDIO_FILE_SIZE + 1))
        with pytest.raises(ValidationError, match="too large"):
            validate_audio_file_path(str(large))

    def test_unsupported_format(self, temp_dir):
        """Should reject unsupported file formats"""
        bad_file = temp_dir / "bad.txt"
        bad_file.write_text("not audio")
        with pytest.raises(ValidationError, match="Unsupported audio format"):
            validate_audio_file_path(str(bad_file))

    def test_all_supported_formats(self, temp_dir):
        """Should accept all supported formats"""
        for ext in SUPPORTED_AUDIO_FORMATS:
            audio_file = temp_dir / f"test{ext}"
            audio_file.write_bytes(b'test' * 1000)  # Non-empty
            result = validate_audio_file_path(str(audio_file))
            assert result.suffix == ext

    def test_optional_must_exist(self, temp_dir):
        """Should allow nonexistent if must_exist=False"""
        nonexistent = temp_dir / "future.wav"
        result = validate_audio_file_path(str(nonexistent), must_exist=False)
        assert result.suffix == '.wav'


class TestModelValidation:
    """Test model file path validation"""

    def test_valid_model(self, mock_model_file):
        """Should accept valid model files"""
        result = validate_model_path(str(mock_model_file))
        assert result.exists()
        assert result.suffix == '.pth'

    def test_nonexistent_model(self, temp_dir):
        """Should reject nonexistent models"""
        nonexistent = temp_dir / "model.pth"
        with pytest.raises(ValidationError, match="not found"):
            validate_model_path(str(nonexistent))

    def test_invalid_model_format(self, temp_dir):
        """Should reject invalid model formats"""
        bad_model = temp_dir / "model.txt"
        bad_model.write_text("not a model")
        with pytest.raises(ValidationError, match="Invalid model format"):
            validate_model_path(str(bad_model))

    def test_all_model_formats(self, temp_dir):
        """Should accept all valid model formats"""
        for ext in ['.pth', '.pt', '.onnx']:
            model = temp_dir / f"model{ext}"
            model.write_bytes(b'model')
            result = validate_model_path(str(model))
            assert result.suffix == ext


class TestPitchValidation:
    """Test pitch change validation"""

    def test_valid_pitch_values(self):
        """Should accept valid pitch values"""
        assert validate_pitch_change(0) == 0
        assert validate_pitch_change(-24) == -24
        assert validate_pitch_change(24) == 24
        assert validate_pitch_change(-12) == -12
        assert validate_pitch_change(12) == 12

    def test_out_of_range_pitch(self):
        """Should reject out of range pitch values"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_pitch_change(-25)

        with pytest.raises(ValidationError, match="out of range"):
            validate_pitch_change(25)

    def test_non_integer_pitch(self):
        """Should reject non-integer pitch values"""
        with pytest.raises(ValidationError, match="must be integer"):
            validate_pitch_change(12.5)

        with pytest.raises(ValidationError, match="must be integer"):
            validate_pitch_change("12")


class TestIndexRateValidation:
    """Test index rate validation"""

    def test_valid_rates(self):
        """Should accept valid rate values"""
        assert validate_index_rate(0.0) == 0.0
        assert validate_index_rate(0.5) == 0.5
        assert validate_index_rate(1.0) == 1.0
        assert validate_index_rate(0.75) == 0.75

    def test_out_of_range_rates(self):
        """Should reject out of range rates"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_index_rate(-0.1)

        with pytest.raises(ValidationError, match="out of range"):
            validate_index_rate(1.1)

    def test_integer_rate(self):
        """Should accept integers and convert to float"""
        assert validate_index_rate(0) == 0.0
        assert validate_index_rate(1) == 1.0

    def test_non_numeric_rate(self):
        """Should reject non-numeric rates"""
        with pytest.raises(ValidationError, match="must be numeric"):
            validate_index_rate("0.5")


class TestAudioDeviceValidation:
    """Test audio device ID validation"""

    def test_valid_device_ids(self):
        """Should accept valid device IDs"""
        assert validate_audio_device_id(0) == 0
        assert validate_audio_device_id(5) == 5
        assert validate_audio_device_id(99) == 99

    def test_negative_device_id(self):
        """Should reject negative device IDs"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_audio_device_id(-1)

    def test_too_large_device_id(self):
        """Should reject device IDs >= max_devices"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_audio_device_id(100)

        with pytest.raises(ValidationError, match="out of range"):
            validate_audio_device_id(1000)

    def test_non_integer_device_id(self):
        """Should reject non-integer device IDs"""
        with pytest.raises(ValidationError, match="must be integer"):
            validate_audio_device_id(5.5)

        with pytest.raises(ValidationError, match="must be integer"):
            validate_audio_device_id("5")


class TestPipeWireValidation:
    """Test PipeWire device ID validation"""

    def test_valid_pipewire_ids(self):
        """Should accept valid PipeWire device IDs"""
        assert validate_pipewire_device_id(0) == 0
        assert validate_pipewire_device_id(42) == 42
        assert validate_pipewire_device_id(1000) == 1000

    def test_none_pipewire_id(self):
        """Should accept None for PipeWire device ID"""
        assert validate_pipewire_device_id(None) is None

    def test_negative_pipewire_id(self):
        """Should reject negative PipeWire device IDs"""
        with pytest.raises(ValidationError, match="must be non-negative"):
            validate_pipewire_device_id(-1)

    def test_non_integer_pipewire_id(self):
        """Should reject non-integer PipeWire device IDs"""
        with pytest.raises(ValidationError, match="must be integer or None"):
            validate_pipewire_device_id(5.5)

        with pytest.raises(ValidationError, match="must be integer or None"):
            validate_pipewire_device_id("5")


class TestSampleRateValidation:
    """Test sample rate validation"""

    def test_valid_sample_rates(self):
        """Should accept standard sample rates"""
        valid_rates = [8000, 16000, 22050, 24000, 32000, 44100, 48000, 88200, 96000, 192000]
        for rate in valid_rates:
            assert validate_sample_rate(rate) == rate

    def test_invalid_sample_rate(self):
        """Should reject non-standard sample rates"""
        with pytest.raises(ValidationError, match="Invalid sample rate"):
            validate_sample_rate(12345)

        with pytest.raises(ValidationError, match="Invalid sample rate"):
            validate_sample_rate(1000)

    def test_non_integer_sample_rate(self):
        """Should reject non-integer sample rates"""
        with pytest.raises(ValidationError, match="must be integer"):
            validate_sample_rate(48000.5)

        with pytest.raises(ValidationError, match="must be integer"):
            validate_sample_rate("48000")


class TestChannelsValidation:
    """Test channels validation"""

    def test_valid_channels(self):
        """Should accept valid channel counts"""
        for channels in range(1, 9):
            assert validate_channels(channels) == channels

    def test_zero_channels(self):
        """Should reject zero channels"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_channels(0)

    def test_too_many_channels(self):
        """Should reject more than 8 channels"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_channels(9)

        with pytest.raises(ValidationError, match="out of range"):
            validate_channels(100)

    def test_negative_channels(self):
        """Should reject negative channels"""
        with pytest.raises(ValidationError, match="out of range"):
            validate_channels(-1)

    def test_non_integer_channels(self):
        """Should reject non-integer channels"""
        with pytest.raises(ValidationError, match="must be integer"):
            validate_channels(2.5)

        with pytest.raises(ValidationError, match="must be integer"):
            validate_channels("2")
