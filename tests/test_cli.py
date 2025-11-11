"""Tests for CLI interface"""
import pytest
from click.testing import CliRunner
from pathlib import Path
from rwc.cli import cli


class TestCLIConvert:
    """Test convert command"""

    def test_convert_help(self):
        """Should show help for convert command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['convert', '--help'])

        assert result.exit_code == 0
        assert 'Convert voice from input audio' in result.output
        assert '--input' in result.output
        assert '--model' in result.output
        assert '--output' in result.output

    def test_convert_missing_required_args(self):
        """Should error when required arguments are missing"""
        runner = CliRunner()
        result = runner.invoke(cli, ['convert'])

        assert result.exit_code != 0
        assert 'Missing option' in result.output

    def test_convert_nonexistent_model(self, sample_audio_file, temp_dir):
        """Should error for non-existent model file"""
        runner = CliRunner()
        nonexistent = temp_dir / "nonexistent.pth"

        result = runner.invoke(cli, [
            'convert',
            '--input', str(sample_audio_file),
            '--model', str(nonexistent),
            '--output', str(temp_dir / 'output.wav')
        ])

        assert result.exit_code == 0  # Click doesn't exit with error code
        assert 'Error: Model file not found' in result.output

    def test_convert_nonexistent_input(self, mock_model_file, temp_dir):
        """Should error for non-existent input file"""
        runner = CliRunner()
        nonexistent = temp_dir / "nonexistent.wav"

        result = runner.invoke(cli, [
            'convert',
            '--input', str(nonexistent),
            '--model', str(mock_model_file),
            '--output', str(temp_dir / 'output.wav')
        ])

        assert result.exit_code == 0
        assert 'Error: Input file not found' in result.output

    def test_convert_with_valid_files(self, sample_audio_file, mock_model_file, temp_dir):
        """Should attempt conversion with valid files"""
        runner = CliRunner()
        output = temp_dir / 'output.wav'

        result = runner.invoke(cli, [
            'convert',
            '--input', str(sample_audio_file),
            '--model', str(mock_model_file),
            '--output', str(output)
        ])

        assert 'Converting voice from' in result.output
        assert 'Using RMVPE' in result.output
        # Will fail at RVC inference step
        assert 'Error during conversion' in result.output

    def test_convert_with_pitch_change(self, sample_audio_file, mock_model_file, temp_dir):
        """Should accept pitch change parameter"""
        runner = CliRunner()
        output = temp_dir / 'output.wav'

        result = runner.invoke(cli, [
            'convert',
            '--input', str(sample_audio_file),
            '--model', str(mock_model_file),
            '--output', str(output),
            '--pitch-change', '5'
        ])

        assert 'Pitch change: 5' in result.output

    def test_convert_with_index_rate(self, sample_audio_file, mock_model_file, temp_dir):
        """Should accept index rate parameter"""
        runner = CliRunner()
        output = temp_dir / 'output.wav'

        result = runner.invoke(cli, [
            'convert',
            '--input', str(sample_audio_file),
            '--model', str(mock_model_file),
            '--output', str(output),
            '--index-rate', '0.5'
        ])

        assert 'Index rate: 0.5' in result.output

    def test_convert_without_rmvpe(self, sample_audio_file, mock_model_file, temp_dir):
        """Should respect no-rmvpe flag"""
        runner = CliRunner()
        output = temp_dir / 'output.wav'

        result = runner.invoke(cli, [
            'convert',
            '--input', str(sample_audio_file),
            '--model', str(mock_model_file),
            '--output', str(output),
            '--no-rmvpe'
        ])

        assert 'Using default pitch extraction' in result.output


class TestCLIServeAPI:
    """Test serve-api command"""

    def test_serve_api_help(self):
        """Should show help for serve-api command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['serve-api', '--help'])

        assert result.exit_code == 0
        assert 'Start API server' in result.output
        assert '--host' in result.output
        assert '--port' in result.output


class TestCLIServeWebUI:
    """Test serve-webui command"""

    def test_serve_webui_help(self):
        """Should show help for serve-webui command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['serve-webui', '--help'])

        assert result.exit_code == 0
        assert 'Gradio web interface' in result.output
        assert '--port' in result.output


class TestCLIRealtime:
    """Test real-time command"""

    def test_realtime_help(self):
        """Should show help for real-time command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['real-time', '--help'])

        assert result.exit_code == 0
        assert '--model' in result.output


class TestCLIDownloadModels:
    """Test download-models command"""

    def test_download_models_help(self):
        """Should show help for download-models command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['download-models', '--help'])

        assert result.exit_code == 0
        assert 'Download required models' in result.output


class TestCLITUI:
    """Test tui command"""

    def test_tui_help(self):
        """Should show help for tui command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['tui', '--help'])

        assert result.exit_code == 0


class TestCLIMain:
    """Test main CLI entry point"""

    def test_cli_help(self):
        """Should show main help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'Real-time Voice Conversion CLI' in result.output
        assert 'convert' in result.output
        assert 'serve-api' in result.output
        assert 'serve-webui' in result.output
        assert 'real-time' in result.output

    def test_cli_version(self):
        """Should show version"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        # Version output format varies, just check it doesn't error
