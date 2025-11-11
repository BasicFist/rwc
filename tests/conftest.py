"""Pytest configuration and fixtures"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a dummy audio file for testing"""
    try:
        import numpy as np
        import soundfile as sf

        # Generate 1 second of silent audio
        sample_rate = 48000
        audio = np.zeros((sample_rate, 2), dtype=np.float32)

        audio_path = temp_dir / "test_audio.wav"
        sf.write(str(audio_path), audio, sample_rate)

        return audio_path
    except ImportError:
        # If soundfile not available, create a dummy WAV file
        audio_path = temp_dir / "test_audio.wav"
        # Write minimal WAV header (44 bytes) + 1 second of silence
        sample_rate = 48000
        num_samples = sample_rate * 2  # 1 second, 2 channels
        data_size = num_samples * 2  # 16-bit samples

        with open(audio_path, 'wb') as f:
            # RIFF header
            f.write(b'RIFF')
            f.write((36 + data_size).to_bytes(4, 'little'))
            f.write(b'WAVE')
            # fmt chunk
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # chunk size
            f.write((1).to_bytes(2, 'little'))   # audio format (PCM)
            f.write((2).to_bytes(2, 'little'))   # num channels
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * 2 * 2).to_bytes(4, 'little'))  # byte rate
            f.write((4).to_bytes(2, 'little'))   # block align
            f.write((16).to_bytes(2, 'little'))  # bits per sample
            # data chunk
            f.write(b'data')
            f.write(data_size.to_bytes(4, 'little'))
            f.write(b'\x00' * data_size)

        return audio_path


@pytest.fixture
def mock_model_file(temp_dir):
    """Create a dummy model file"""
    model_path = temp_dir / "test_model.pth"
    model_path.write_text("dummy model content")
    return model_path


@pytest.fixture
def models_dir(temp_dir):
    """Create a models directory structure"""
    models = temp_dir / "models"
    models.mkdir()

    # Create some test model files
    (models / "model1.pth").write_text("model 1")

    subdir = models / "community"
    subdir.mkdir()
    (subdir / "model2.pth").write_text("model 2")

    return models
