
import pytest
from pathlib import Path
from unittest.mock import patch
from rwc.core import VoiceConverter

class TestResourceCleanupBug:
    @patch('ultimate_rvc.core.generate.common.convert')
    def test_convert_voice_cleans_up_json_when_filenames_match(self, mock_urvc_convert, mock_model_file, sample_audio_file, temp_dir):
        """
        Tests that the .json metadata file is cleaned up even when the output
        filename from urvc_convert matches the desired output filename.

        This simulates the bug condition where the json cleanup logic was skipped.
        """
        # Arrange
        converter = VoiceConverter(str(mock_model_file), use_rmvpe=False)
        output_wav_path = temp_dir / "output.wav"

        # This is the path that urvc_convert will return. To trigger the bug,
        # it must be the same as the `output_audio` path.
        result_path_from_convert = output_wav_path
        json_path_from_convert = result_path_from_convert.with_suffix('.json')

        # Mock the behavior of urvc_convert:
        # 1. It creates a .wav file (or we can simulate it).
        # 2. It creates an associated .json file.
        # 3. It returns the path to the created .wav file.
        def side_effect(*args, **kwargs):
            # Simulate creation of .wav and .json files by urvc_convert
            result_path_from_convert.touch()
            json_path_from_convert.touch()
            return result_path_from_convert

        mock_urvc_convert.side_effect = side_effect

        # Act
        converter.convert_voice(
            input_audio=str(sample_audio_file),
            output_audio=str(output_wav_path),
        )

        # Assert
        # Before the fix, this assertion will fail because the json file is not deleted.
        assert not json_path_from_convert.exists(), "The temporary .json file should be deleted."
