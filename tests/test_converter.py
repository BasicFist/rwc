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

        with pytest.raises(RuntimeError, match="File not found"):
            converter.convert_voice(str(nonexistent), str(output))

    def test_convert_voice_validates_pitch(self, mock_model_file, sample_audio_file, temp_dir):
        """Should validate pitch change range"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output = temp_dir / "output.wav"

        # Out of range pitch
        with pytest.raises(RuntimeError, match="Pitch out of range"):
            converter.convert_voice(str(sample_audio_file), str(output), pitch_shift=30)

    def test_convert_voice_validates_index_rate(self, mock_model_file, sample_audio_file, temp_dir):
        """Should validate index rate range"""
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output = temp_dir / "output.wav"

        # Out of range index rate
        with pytest.raises(RuntimeError, match="Rate out of range"):
            converter.convert_voice(str(sample_audio_file), str(output), index_rate=1.5)

    @pytest.mark.skip(reason="Requires actual RVC model and ultimate-rvc setup")
    def test_convert_voice_integration(self, mock_model_file, sample_audio_file, temp_dir):
        """Should convert voice using ultimate-rvc backend (integration test)"""
        # NOTE: This test is skipped by default as it requires:
        # 1. A real RVC model in models/ directory with proper structure
        # 2. ultimate-rvc package installed and configured
        # 3. Model files (HomerSimpson2333333 or similar)
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output = temp_dir / "output.wav"

        # Would call actual conversion with ultimate-rvc
        # converter.convert_voice(
        #     str(sample_audio_file),
        #     str(output),
        #     pitch_shift=0,
        #     index_rate=0.75
        # )
        # assert output.exists()
        pass


# NOTE: The following test classes have been removed as of Nov 2025
# Feature extraction, pitch extraction, and RVC inference are now handled by ultimate-rvc
# Previous test classes:
# - TestFeatureExtraction: Tested _extract_features_placeholder (removed)
# - TestPitchShift: Tested _apply_pitch_shift (removed, handled by ultimate-rvc's n_semitones)
# - TestRVCInference: Tested _rvc_inference_placeholder (removed, handled by ultimate-rvc's convert())
#
# For integration testing with actual RVC models, see test_convert_voice_integration above
