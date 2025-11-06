"""
RWC Command Line Interface
"""
import click
import os
from rwc.core import VoiceConverter
import os


@click.group()
@click.version_option()
def cli():
    """Real-time Voice Conversion CLI."""
    pass


@cli.command()
@click.option('--input', '-i', required=True, help='Input audio file path')
@click.option('--model', '-m', required=True, help='Path to RVC model file (.pth)')
@click.option('--output', '-o', default='output.wav', help='Output file path')
@click.option('--pitch-change', '-p', default=0, type=int, help='Pitch change in semitones (-24 to 24)')
@click.option('--index-rate', '-ir', default=0.75, type=float, help='Index rate (0.0 to 1.0)')
@click.option('--use-rmvpe/--no-rmvpe', default=True, help='Use RMVPE for pitch extraction (more accurate)')
def convert(input, model, output, pitch_change, index_rate, use_rmvpe):
    """Convert voice from input audio using specified model."""
    click.echo(f"Converting voice from {input} using model {model}")
    click.echo(f"Using {'RMVPE' if use_rmvpe else 'default'} pitch extraction")
    click.echo(f"Pitch change: {pitch_change}, Index rate: {index_rate}")
    click.echo(f"Saving to {output}")
    
    if not os.path.exists(model):
        click.echo(f"Error: Model file not found: {model}")
        return
    
    if not os.path.exists(input):
        click.echo(f"Error: Input file not found: {input}")
        return
    
    try:
        converter = VoiceConverter(model, use_rmvpe=use_rmvpe)
        result_path = converter.convert_voice(input, output, pitch_change, index_rate)
        click.echo(f"Successfully converted voice. Output saved to: {result_path}")
    except Exception as e:
        click.echo(f"Error during conversion: {str(e)}")


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, type=int, help='Port to run the server on')
def serve_api(host, port):
    """Start API server for voice conversion."""
    click.echo(f"Starting RWC API server at {host}:{port}...")
    
    # Import here to avoid circular dependencies
    from rwc.api import app
    app.run(host=host, port=port)


@cli.command()
@click.option('--port', default=7865, type=int, help='Port to run the web UI on')
def serve_webui(port):
    """Start the Gradio web interface."""
    click.echo(f"Starting RWC Web UI at http://localhost:{port}...")
    
    # Import here to avoid circular dependencies
    from rwc import webui
    import os
    import sys
    
    # Change to the rwc directory for proper relative imports
    os.chdir(os.path.dirname(os.path.abspath(webui.__file__)))
    
    # Run the web UI
    webui.demo.launch(server_name="0.0.0.0", server_port=port, share=False)


@cli.command()
def download_models():
    """Download required models for RWC."""
    click.echo("Downloading required RWC models...")
    
    # Import and run the download utility
    from rwc.utils import download_models
    download_models()


@cli.command()
@click.option('--input-device', '-i', default=4, type=int, help='Input device ID (use "python -m rwc.utils.list_devices" to see available devices)')
@click.option('--output-device', '-o', default=0, type=int, help='Output device ID (use "python -m rwc.utils.list_devices" to see available devices)')
@click.option('--model', '-m', required=True, help='Path to RVC model file (.pth)')
@click.option('--use-rmvpe/--no-rmvpe', default=True, help='Use RMVPE for pitch extraction (more accurate)')
def real_time(input_device, output_device, model, use_rmvpe):
    """Perform real-time voice conversion from microphone input."""
    click.echo(f"Starting real-time conversion using model: {model}")
    click.echo(f"Input device: {input_device}, Output device: {output_device}")
    click.echo(f"Using {'RMVPE' if use_rmvpe else 'default'} pitch extraction")
    
    if not os.path.exists(model):
        click.echo(f"Error: Model file not found: {model}")
        return
    
    try:
        converter = VoiceConverter(model, use_rmvpe=use_rmvpe)
        converter.real_time_convert(input_device=input_device, output_device=output_device)
    except Exception as e:
        click.echo(f"Error during real-time conversion: {str(e)}")


@cli.command()
def tui():
    """Start the Terminal User Interface (TUI) for RWC."""
    click.echo("Starting RWC Terminal User Interface...")
    click.echo("This provides an interactive menu for conversion options.")
    
    try:
        from rwc.tui import main_tui
        main_tui()
    except ImportError as e:
        click.echo(f"Error starting TUI: {str(e)}")
        click.echo("Please make sure you have the required dependencies installed.")
    except Exception as e:
        click.echo(f"Unexpected error in TUI: {str(e)}")


@cli.command()
def download_additional_models():
    """Download additional models for RWC from various repositories."""
    click.echo("This command executes the download_additional_models.sh script.")
    click.echo("Please run: bash download_additional_models.sh")


if __name__ == '__main__':
    cli()