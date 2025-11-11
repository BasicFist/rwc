"""
Core RWC (Real-time Voice Conversion) functionality
Based on RVC (Retrieval-based Voice Conversion) framework
"""
import os
import sys
import time
import torch
import librosa
import numpy as np
from typing import Optional, Tuple, Dict, Any
import configparser
import shutil
import subprocess
from pathlib import Path

from rwc.utils.logging_config import get_logger
from rwc.utils.constants import (
    DEFAULT_SAMPLE_RATE,
    DEFAULT_CHANNELS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_PITCH_CHANGE,
    DEFAULT_INDEX_RATE,
    METER_BAR_WIDTH,
    METER_MAX_RMS,
    METER_EPSILON,
    MIN_CHUNK_SIZE,
    MAX_CHUNK_SIZE,
    ERROR_MESSAGES,
    LOG_MESSAGES,
)

logger = get_logger(__name__)

class VoiceConverter:
    """
    Core voice conversion class based on RVC framework
    """
    def __init__(
        self,
        model_path: str,
        config_path: Optional[str] = None,
        use_rmvpe: Optional[bool] = None
    ) -> None:
        """
        Initialize the voice converter with a model

        Args:
            model_path: Path to the RVC model file (.pth)
            config_path: Optional path to config file
            use_rmvpe: Whether to use RMVPE for pitch extraction (more accurate)

        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If model loading fails
        """
        logger.info(f"Initializing VoiceConverter with model: {model_path}")

        self.model_path = model_path
        self.config_path = config_path or 'rwc/config.ini'
        self.config = self._load_config()

        # Use parameter if provided, otherwise use config default
        self.use_rmvpe = use_rmvpe if use_rmvpe is not None else self.config.getboolean('CONVERSION', 'use_rmvpe_by_default', fallback=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        if not torch.cuda.is_available():
            logger.warning(ERROR_MESSAGES['cuda_not_available'])

        self.model: Optional[Any] = None
        self.hubert_model: Optional[Any] = None
        self.rmvpe_model: Optional[Any] = None

        # Initialize models
        self._load_models()
        logger.info(LOG_MESSAGES['model_loaded'].format(model=Path(model_path).name))
    
    def _load_config(self) -> configparser.ConfigParser:
        """
        Load configuration from config file

        Returns:
            ConfigParser instance with loaded configuration
        """
        logger.debug(f"Loading configuration from {self.config_path}")
        config = configparser.ConfigParser()
        
        # Read default config first
        default_config_path = 'rwc/config.ini'
        if os.path.exists(default_config_path):
            config.read(default_config_path)
        
        # Override with custom config if provided
        if self.config_path and os.path.exists(self.config_path):
            config.read(self.config_path)
        
        return config
    
    def _load_models(self):
        """
        Load the voice conversion models
        """
        print(f"Loading model from: {self.model_path}")
        print(f"Using device: {self.device}")
        
        # Initialize hubert model for feature extraction
        self._load_hubert_model()
        
        # Initialize RMVPE model if available and requested
        if self.use_rmvpe:
            self._load_rmvpe_model()
    
    def _load_hubert_model(self):
        """
        Load the HuBERT model for feature extraction
        """
        hubert_path = self.config.get('MODEL_PATHS', 'hubert_model_path', fallback='models/hubert_base/hubert_base.pt')
        if os.path.exists(hubert_path):
            print(f"Loading HuBERT model from {hubert_path}")
            # In a full implementation, we would load the actual model here
        else:
            print(f"Warning: HuBERT model not found at {hubert_path}. Please run 'bash download_models.sh'")
    
    def _load_rmvpe_model(self):
        """
        Load the RMVPE model for more accurate pitch extraction
        """
        rmvpe_path = self.config.get('MODEL_PATHS', 'rmvpe_model_path', fallback='models/rmvpe/rmvpe.pt')
        if os.path.exists(rmvpe_path):
            print(f"Loading RMVPE model from {rmvpe_path}")
            # In a full implementation, we would load the actual model here
            self.rmvpe_model = rmvpe_path
        else:
            print(f"RMVPE model not found at {rmvpe_path}, falling back to built-in pitch extraction")
            self.use_rmvpe = False
    
    def convert_voice(self, input_audio_path: str, output_audio_path: str, 
                     pitch_change: Optional[int] = None, index_rate: Optional[float] = None) -> str:
        """
        Convert voice from input audio to target speaker
        
        Args:
            input_audio_path: Path to input audio file
            output_audio_path: Path to save output audio file
            pitch_change: Pitch change in semitones (uses config default if not specified)
            index_rate: How much to use the feature index (0.0-1.0) (uses config default if not specified)
        
        Returns:
            Path to the output audio file
        """
        # Use config defaults if parameters not provided
        default_pitch_change = self.config.getint('CONVERSION', 'default_pitch_change', fallback=0)
        pitch_change = pitch_change if pitch_change is not None else default_pitch_change
        
        default_index_rate = self.config.getfloat('CONVERSION', 'default_index_rate', fallback=0.75)
        index_rate = index_rate if index_rate is not None else default_index_rate
        
        print(f"Converting voice: {input_audio_path} -> {output_audio_path}")
        print(f"Using {'RMVPE' if self.use_rmvpe else 'default'} pitch extraction")
        print(f"Pitch change: {pitch_change}, Index rate: {index_rate}")
        
        # Placeholder for actual voice conversion logic
        # In a real implementation, this would:
        # 1. Load the input audio
        # 2. Extract features using the loaded models
        # 3. Apply voice conversion using RVC techniques
        # 4. Generate output audio
        # 5. Save the output
        
        # For now, just return the output path
        return output_audio_path
    
    def real_time_convert(
        self,
        input_device: int = 0,
        output_device: int = 0,
        show_meter: bool = True,
        meter_refresh: float = 0.1,
        pipewire_source: Optional[int] = None,
        pipewire_sink: Optional[int] = None,
    ):
        """
        Perform real-time voice conversion using microphone input
        
        Note: Real-time conversion requires the following additional dependencies:
        - PortAudio library (system library) - installed
        - PyAudio Python package - installed
        """
        use_pwcat = shutil.which("pw-cat") is not None
        
        if use_pwcat:
            print("pw-cat detected - using PipeWire default devices for streaming.")
            self._real_time_convert_pwcat(
                show_meter=show_meter,
                meter_refresh=meter_refresh,
                source_id=pipewire_source,
                sink_id=pipewire_sink,
            )
            return
        
        import pyaudio
        import numpy as np
        
        print(f"Starting real-time conversion on device {input_device} -> {output_device}")
        print(f"Using {'RMVPE' if self.use_rmvpe else 'default'} pitch extraction")
        
        # Set up audio parameters
        chunk = 1024  # Buffer size
        FORMAT = pyaudio.paFloat32
        CHANNELS = 2  # Stereo input to match detected device
        RATE = 48000  # Sample rate to match detected device
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            # Open input stream
            stream_in = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=chunk
            )
            
            # Open output stream
            stream_out = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=output_device,
                frames_per_buffer=chunk
            )
            
            print("Real-time conversion streams opened successfully!")
            print("Recording and converting in real-time... (Press Ctrl+C to stop)")
            if show_meter:
                print("Microphone level meter active (updates every "
                      f"{meter_refresh:.1f}s)")
            
            # For demonstration, just pass through audio with a simple processing
            # In a real implementation, this would involve RVC-style processing
            try:
                last_meter_update = time.monotonic()
                meter_bar_width = 30
                epsilon = 1e-8
                
                while True:
                    # Read data from microphone
                    data = stream_in.read(chunk, exception_on_overflow=False)
                    
                    # Convert to numpy array for processing
                    audio_array = np.frombuffer(data, dtype=np.float32)
                    
                    if show_meter:
                        now = time.monotonic()
                        if now - last_meter_update >= meter_refresh:
                            rms = float(np.sqrt(np.mean(np.square(audio_array))))
                            meter_level = min(rms / 0.2, 1.0)
                            filled = int(meter_level * meter_bar_width)
                            bar = "#" * filled + "." * (meter_bar_width - filled)
                            db = 20 * np.log10(max(rms, epsilon))
                            sys.stdout.write(
                                f"\rMic level [{bar}] {db:6.1f} dBFS"
                            )
                            sys.stdout.flush()
                            last_meter_update = now
                    
                    # Here would be the actual RVC processing
                    # For now, just pass through with slight amplification to show processing
                    processed_audio = audio_array * 1.1
                    
                    # Convert back to bytes
                    output_data = processed_audio.astype(np.float32).tobytes()
                    
                    # Play processed audio
                    stream_out.write(output_data)
                    
            except KeyboardInterrupt:
                print("\nReal-time conversion stopped by user.")
            finally:
                if show_meter:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
            
        except Exception as e:
            print(f"Error during real-time conversion: {e}")
        finally:
            # Clean up
            if 'stream_in' in locals():
                stream_in.stop_stream()
                stream_in.close()
            if 'stream_out' in locals():
                stream_out.stop_stream()
                stream_out.close()
            p.terminate()
            print("Real-time conversion streams closed.")

    def _real_time_convert_pwcat(
        self,
        rate: int = 48000,
        channels: int = 1,
        chunk: int = 1024,
        show_meter: bool = True,
        meter_refresh: float = 0.1,
        source_id: Optional[int] = None,
        sink_id: Optional[int] = None,
    ):
        """
        PipeWire-based real-time loop using pw-cat for capture/playback.

        Args:
            rate: Sample rate in Hz
            channels: Number of audio channels
            chunk: Buffer size
            show_meter: Whether to show audio level meter
            meter_refresh: Meter refresh rate in seconds
            source_id: PipeWire source node ID (integer only)
            sink_id: PipeWire sink node ID (integer only)

        Raises:
            ValueError: If parameters are invalid
        """
        import numpy as np
        from rwc.utils.validation import (
            validate_pipewire_device_id,
            validate_sample_rate,
            validate_channels,
            ValidationError
        )

        # Validate inputs to prevent command injection
        try:
            rate = validate_sample_rate(rate)
            channels = validate_channels(channels)
            source_id = validate_pipewire_device_id(source_id)
            sink_id = validate_pipewire_device_id(sink_id)
        except ValidationError as e:
            raise ValueError(f"Invalid parameter: {e}")

        # Validate chunk size
        if not isinstance(chunk, int) or chunk < 64 or chunk > 8192:
            raise ValueError(f"Invalid chunk size: {chunk} (must be 64-8192)")

        # Build command with validated parameters (safe from injection)
        record_cmd = [
            "pw-cat",
            "--record",
            f"--rate={rate}",
            f"--channels={channels}",
        ]
        if source_id is not None:
            # Safe: source_id is validated integer
            record_cmd.extend(["--target", str(source_id)])
        record_cmd.append("-")

        play_cmd = [
            "pw-cat",
            "--playback",
            f"--rate={rate}",
            f"--channels={channels}",
        ]
        if sink_id is not None:
            # Safe: sink_id is validated integer
            play_cmd.extend(["--target", str(sink_id)])
        play_cmd.append("-")

        bytes_per_sample = 2  # s16le
        bytes_per_chunk = chunk * channels * bytes_per_sample
        epsilon = 1e-8
        meter_bar_width = 30
        last_meter_update = time.monotonic()

        print("Opening PipeWire streams (default source/sink)...")

        record_proc = subprocess.Popen(
            record_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        play_proc = subprocess.Popen(
            play_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if not record_proc.stdout or not play_proc.stdin:
            raise RuntimeError("Failed to open pw-cat streams.")

        try:
            print("Real-time conversion streams opened successfully!")
            print("Recording and converting via PipeWire (Ctrl+C to stop)")
            if show_meter:
                print("Microphone level meter active (updates every "
                      f"{meter_refresh:.1f}s)")

            while True:
                chunk_bytes = record_proc.stdout.read(bytes_per_chunk)
                if not chunk_bytes:
                    # End of stream; give pw-cat time to flush stderr
                    time.sleep(0.05)
                    err = record_proc.stderr.read().decode() if record_proc.stderr else ""
                    raise RuntimeError(f"pw-cat ended unexpectedly.\n{err}")

                audio_array = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32)
                audio_array /= 32768.0

                if show_meter:
                    now = time.monotonic()
                    if now - last_meter_update >= meter_refresh:
                        rms = float(np.sqrt(np.mean(np.square(audio_array))))
                        meter_level = min(rms / 0.2, 1.0)
                        filled = int(meter_level * meter_bar_width)
                        bar = "#" * filled + "." * (meter_bar_width - filled)
                        db = 20 * np.log10(max(rms, epsilon))
                        sys.stdout.write(f"\rMic level [{bar}] {db:6.1f} dBFS")
                        sys.stdout.flush()
                        last_meter_update = now

                # Placeholder processing (pass-through with slight gain)
                processed = np.clip(audio_array * 1.1, -1.0, 1.0)
                output_bytes = (processed * 32767.0).astype(np.int16).tobytes()

                play_proc.stdin.write(output_bytes)

        except KeyboardInterrupt:
            print("\nReal-time conversion stopped by user.")
        except Exception as exc:
            print(f"\nError during PipeWire streaming: {exc}")
        finally:
            if show_meter:
                sys.stdout.write("\n")
                sys.stdout.flush()

            if record_proc.stdout:
                record_proc.stdout.close()
            if play_proc.stdin:
                play_proc.stdin.close()

            record_proc.terminate()
            play_proc.terminate()

            # Drain stderr for debugging
            for proc, label in [(record_proc, "record"), (play_proc, "playback")]:
                try:
                    if proc.stderr:
                        err = proc.stderr.read().decode().strip()
                        if err:
                            print(f"[pw-cat {label} stderr] {err}")
                except Exception:
                    pass
