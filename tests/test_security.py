"""Security-focused tests"""
import pytest
from pathlib import Path
from rwc.api import sanitize_path
from rwc.utils.validation import (
    ValidationError,
    validate_audio_file_path,
    validate_model_path,
    validate_pipewire_device_id,
    validate_sample_rate,
    validate_channels,
)


class TestPathTraversal:
    """Test path traversal vulnerability fixes"""

    def test_blocks_parent_directory_traversal(self, models_dir):
        """Should block ../ attacks"""
        with pytest.raises(ValueError, match="escapes base directory"):
            sanitize_path("../../etc/passwd", base_dir=str(models_dir))

    def test_blocks_absolute_paths(self, models_dir):
        """Should block absolute paths"""
        with pytest.raises(ValueError):
            sanitize_path("/etc/passwd", base_dir=str(models_dir))

    def test_allows_valid_relative_paths(self, models_dir):
        """Should allow valid relative paths"""
        result = sanitize_path("model1.pth", base_dir=str(models_dir))
        assert "model1.pth" in result
        assert Path(result).exists()

    def test_allows_valid_subdirectory_paths(self, models_dir):
        """Should allow valid subdirectory paths"""
        result = sanitize_path("community/model2.pth", base_dir=str(models_dir))
        assert "model2.pth" in result
        assert Path(result).exists()

    def test_blocks_nonexistent_paths(self, models_dir):
        """Should block paths that don't exist"""
        with pytest.raises(ValueError, match="does not exist"):
            sanitize_path("nonexistent.pth", base_dir=str(models_dir))

    def test_follows_symlinks_safely(self, temp_dir):
        """Should resolve symlinks and check bounds"""
        models_dir = temp_dir / "models"
        models_dir.mkdir()

        # Create file outside models dir
        outside = temp_dir / "outside.txt"
        outside.write_text("secret")

        # Create symlink inside models dir
        link = models_dir / "link.txt"
        link.symlink_to(outside)

        # Should block (resolves to outside base_dir)
        with pytest.raises(ValueError, match="escapes"):
            sanitize_path("link.txt", base_dir=str(models_dir))


class TestInputValidation:
    """Test input validation"""

    def test_rejects_oversized_files(self, temp_dir):
        """Should reject files over size limit"""
        large_file = temp_dir / "large.wav"
        # Create a file that's too large (51MB)
        with open(large_file, 'wb') as f:
            f.write(b'x' * (51 * 1024 * 1024))

        with pytest.raises(ValidationError, match="too large"):
            validate_audio_file_path(str(large_file))

    def test_rejects_empty_files(self, temp_dir):
        """Should reject empty files"""
        empty_file = temp_dir / "empty.wav"
        empty_file.touch()

        with pytest.raises(ValidationError, match="empty"):
            validate_audio_file_path(str(empty_file))

    def test_rejects_unsupported_formats(self, temp_dir):
        """Should reject unsupported file formats"""
        bad_file = temp_dir / "bad.exe"
        bad_file.write_bytes(b"malware" * 1000)

        with pytest.raises(ValidationError, match="Unsupported audio format"):
            validate_audio_file_path(str(bad_file))

    def test_accepts_valid_audio_file(self, sample_audio_file):
        """Should accept valid audio files"""
        result = validate_audio_file_path(str(sample_audio_file))
        assert result.exists()
        assert result.suffix == '.wav'

    def test_validates_model_extensions(self, temp_dir):
        """Should validate model file extensions"""
        bad_model = temp_dir / "model.txt"
        bad_model.write_text("not a model")

        with pytest.raises(ValidationError, match="Invalid model format"):
            validate_model_path(str(bad_model))


class TestCommandInjection:
    """Test command injection prevention"""

    def test_rejects_non_integer_device_ids(self):
        """Should reject non-integer device IDs"""
        with pytest.raises(ValidationError):
            validate_pipewire_device_id("1; rm -rf /")

    def test_rejects_negative_device_ids(self):
        """Should reject negative device IDs"""
        with pytest.raises(ValidationError):
            validate_pipewire_device_id(-1)

    def test_accepts_valid_device_ids(self):
        """Should accept valid device IDs"""
        assert validate_pipewire_device_id(0) == 0
        assert validate_pipewire_device_id(5) == 5
        assert validate_pipewire_device_id(None) is None

    def test_validates_sample_rates(self):
        """Should validate audio sample rates"""
        # Valid rates
        assert validate_sample_rate(48000) == 48000
        assert validate_sample_rate(44100) == 44100

        # Invalid rates
        with pytest.raises(ValidationError):
            validate_sample_rate(-1)

        with pytest.raises(ValidationError):
            validate_sample_rate(12345)  # Not a standard rate

    def test_validates_channels(self):
        """Should validate number of channels"""
        # Valid channels
        assert validate_channels(1) == 1
        assert validate_channels(2) == 2

        # Invalid channels
        with pytest.raises(ValidationError):
            validate_channels(0)

        with pytest.raises(ValidationError):
            validate_channels(999)


class TestAPIEndpoints:
    """Test API endpoint security"""

    def test_health_endpoint(self):
        """Health endpoint should work without authentication"""
        from rwc.api import app

        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert 'status' in data
            assert data['status'] == 'healthy'

    def test_convert_requires_file(self):
        """Convert endpoint should reject missing file"""
        from rwc.api import app

        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.post('/convert', data={})
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_convert_validates_model_path(self, sample_audio_file):
        """Convert endpoint should validate model path"""
        from rwc.api import app

        app.config['TESTING'] = True
        with app.test_client() as client:
            with open(sample_audio_file, 'rb') as f:
                response = client.post('/convert', data={
                    'audio_file': (f, 'test.wav'),
                    'model_path': '../../etc/passwd'  # Attack!
                })

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
            assert 'Invalid model path' in data['error']
