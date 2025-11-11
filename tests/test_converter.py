"""Tests for voice converter core functionality"""
import pytest
import numpy as np
from pathlib import Path
from rwc.core import VoiceConverter
from rwc.utils.validation import ValidationError


class TestVoiceConverter:
    """Test VoiceConverter class"""

    def test_converter_initialization(self, mock_model_file):
        """Should initialize converter with model"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        assert converter.model_path == str(mock_model_file)
        assert converter.use_rmvpe is False

    def test_converter_with_rmvpe(self, mock_model_file):
        """Should initialize converter with RMVPE enabled"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=True)
        assert converter.use_rmvpe is True

    def test_converter_invalid_model(self, temp_dir):
        """Should initialize even with non-existent model (lazy loading)"""
        nonexistent = temp_dir / "nonexistent.pth"
        # Constructor doesn't validate model existence (lazy loading)
        converter = VoiceConverter(str(nonexistent), use_rmvpe=False)
        assert converter.model_path == str(nonexistent)


class TestConvertVoice:
    """Test convert_voice method"""

    def test_convert_voice_validates_input(self, mock_model_file, temp_dir):
        """Should validate input audio file"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        nonexistent = temp_dir / "nonexistent.wav"
        output = temp_dir / "output.wav"

        with pytest.raises(ValueError, match="Invalid input"):
            converter.convert_voice(str(nonexistent), str(output))

    def test_convert_voice_validates_pitch(self, mock_model_file, sample_audio_file, temp_dir):
        """Should validate pitch change range"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output = temp_dir / "output.wav"

        # Out of range pitch
        with pytest.raises(ValueError, match="Invalid input"):
            converter.convert_voice(str(sample_audio_file), str(output), pitch_change=30)

    def test_convert_voice_validates_index_rate(self, mock_model_file, sample_audio_file, temp_dir):
        """Should validate index rate range"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output = temp_dir / "output.wav"

        # Out of range index rate
        with pytest.raises(ValueError, match="Invalid input"):
            converter.convert_voice(str(sample_audio_file), str(output), index_rate=1.5)

    def test_convert_voice_raises_not_implemented(self, mock_model_file, sample_audio_file, temp_dir):
        """Should raise RuntimeError at RVC inference step"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output = temp_dir / "output.wav"

        # Should fail at RVC inference with clear message (wrapped in RuntimeError)
        with pytest.raises(RuntimeError, match="Voice conversion failed.*RVC inference is not yet implemented"):
            converter.convert_voice(
                str(sample_audio_file),
                str(output),
                pitch_change=0,
                index_rate=0.75
            )


class TestFeatureExtraction:
    """Test feature extraction methods"""

    def test_extract_features_placeholder(self, mock_model_file):
        """Should return placeholder features with correct shape"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        # Create dummy audio data
        audio_data = np.random.randn(48000)  # 1 second @ 48kHz
        features = converter._extract_features_placeholder(audio_data, 48000)

        assert isinstance(features, np.ndarray)
        assert features.ndim == 2
        assert features.shape[1] == 256  # HuBERT feature dimension

    def test_extract_pitch_placeholder(self, mock_model_file):
        """Should extract pitch using librosa pyin"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        # Create dummy audio with some frequency content
        t = np.linspace(0, 1, 48000)
        audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

        f0_curve = converter._extract_pitch_placeholder(audio_data, 48000)

        assert isinstance(f0_curve, np.ndarray)
        assert f0_curve.ndim == 1
        assert len(f0_curve) > 0
        # Should detect something near 440 Hz
        assert np.any(f0_curve > 0)


class TestPitchShift:
    """Test pitch shift functionality"""

    def test_pitch_shift_up(self, mock_model_file):
        """Should shift pitch up correctly"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        f0_curve = np.array([100.0, 200.0, 300.0])
        shifted = converter._apply_pitch_shift(f0_curve, 12)  # Up one octave

        # 12 semitones = octave = 2x frequency
        expected = f0_curve * 2.0
        np.testing.assert_array_almost_equal(shifted, expected, decimal=5)

    def test_pitch_shift_down(self, mock_model_file):
        """Should shift pitch down correctly"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        f0_curve = np.array([200.0, 400.0, 600.0])
        shifted = converter._apply_pitch_shift(f0_curve, -12)  # Down one octave

        # -12 semitones = octave down = 0.5x frequency
        expected = f0_curve * 0.5
        np.testing.assert_array_almost_equal(shifted, expected, decimal=5)

    def test_pitch_shift_zero(self, mock_model_file):
        """Should not change pitch when shift is zero"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        f0_curve = np.array([150.0, 250.0, 350.0])
        shifted = converter._apply_pitch_shift(f0_curve, 0)

        np.testing.assert_array_equal(shifted, f0_curve)

    def test_pitch_shift_fractional(self, mock_model_file):
        """Should handle fractional semitone shifts"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        f0_curve = np.array([100.0])
        shifted = converter._apply_pitch_shift(f0_curve, 1)  # Up 1 semitone

        # 1 semitone = 2^(1/12) ≈ 1.05946
        expected = f0_curve * (2.0 ** (1.0 / 12.0))
        np.testing.assert_array_almost_equal(shifted, expected, decimal=5)


class TestRVCInference:
    """Test RVC inference placeholder"""

    def test_rvc_inference_not_implemented(self, mock_model_file):
        """Should raise NotImplementedError with helpful message"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)

        features = np.zeros((100, 256))
        f0_curve = np.zeros(100)

        with pytest.raises(NotImplementedError) as exc_info:
            converter._rvc_inference_placeholder(features, f0_curve, 0.75)

        # Check error message contains helpful information
        error_msg = str(exc_info.value)
        assert "RVC inference is not yet implemented" in error_msg
        assert "RVC-Project" in error_msg
        assert "https://github.com" in error_msg
