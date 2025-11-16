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
from typing import Optional, Tuple, Dict, Any, Union
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
    
    def convert_voice(
        self,
        input_audio: Union[str, Path, np.ndarray],
        output_audio: Union[str, Path],
        pitch_shift: int = 0,
        index_rate: float = 0.5,
        sample_rate: int = 48000,
    ) -> Path:
        """
        Convert voice using RVC model with ultimate-rvc backend
        
        Args:
            input_audio: Path to input audio or numpy array
            output_audio: Path for output audio
            pitch_shift: Pitch shift in semitones (-24 to +24)
            index_rate: Feature retrieval strength (0.0 to 1.0)
            sample_rate: Target sample rate (ignored, uses model's rate)
            
        Returns:
            Path to converted audio file
        """
        from ultimate_rvc.core.generate.common import convert as urvc_convert
        from ultimate_rvc.typing_extra import F0Method, EmbedderModel
        from rwc.utils.validation import (
            validate_pitch_change,
            validate_index_rate as validate_idx_rate,
            validate_audio_file_path
        )
        import tempfile

        logger = get_logger(__name__)
        logger.info("Starting voice conversion with ultimate-rvc backend")

        try:
            # Validate inputs
            validate_pitch_change(pitch_shift)
            validate_idx_rate(index_rate)
            # Handle numpy array input by saving to temporary file
            temp_input = None
            if isinstance(input_audio, np.ndarray):
                temp_input = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                import soundfile as sf
                sf.write(temp_input.name, input_audio, sample_rate)
                input_path = temp_input.name
            else:
                input_path = str(input_audio)
                validate_audio_file_path(input_path)
            
            # Extract model name from self.model_path
            # Model should be in models/ directory with standard structure
            model_path = Path(self.model_path)
            model_name = model_path.parent.name  # e.g., "HomerSimpson2333333"
            
            # Create output directory if needed
            output_path = Path(output_audio)
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Map rwc parameters to ultimate-rvc parameters
            # ultimate-rvc uses semitones directly (same as rwc's pitch_shift)
            # ultimate-rvc's index_rate maps directly to rwc's index_rate
            
            f0_methods = [F0Method.RMVPE]  # Use RMVPE for pitch extraction
            if not self.use_rmvpe:
                f0_methods = [F0Method.CREPE]  # Fallback to CREPE
            
            logger.info(f"Converting with model: {model_name}")
            logger.info(f"Pitch shift: {pitch_shift} semitones")
            logger.info(f"Index rate: {index_rate}")
            logger.info(f"F0 method: {f0_methods[0]}")
            
            # Call ultimate-rvc's convert function
            result_path = urvc_convert(
                audio_track=input_path,
                directory=output_dir,
                model_name=model_name,
                n_semitones=pitch_shift,
                f0_methods=f0_methods,
                index_rate=index_rate,
                rms_mix_rate=1.0,  # Full volume envelope mixing
                protect_rate=0.33,  # Protect consonants/breathing
                hop_length=128,  # Standard hop length
                split_audio=False,  # Process as single chunk
                autotune_audio=False,  # No autotune by default
                clean_audio=False,  # No noise reduction by default
                embedder_model=EmbedderModel.CONTENTVEC,  # Standard embedder
                sid=0,  # Default speaker ID
            )
            
            # Rename result to match expected output path
            if result_path != output_path:
                import shutil
                shutil.move(str(result_path), str(output_path))
                # Also move the metadata JSON if it exists
                json_path = result_path.with_suffix('.json')
                if json_path.exists():
                    json_path.unlink()
            
            # Clean up temporary input file if created
            if temp_input:
                try:
                    os.unlink(temp_input.name)
                except:
                    pass
            
            logger.info(f"Voice conversion completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Voice conversion failed: {e}")
            raise RuntimeError(f"Voice conversion failed: {e}")

    # NOTE: The following placeholder methods have been removed as of Nov 2025
    # RVC inference is now handled by the ultimate-rvc package integration in convert_voice()
    # Previous placeholder methods:
    # - _extract_features_placeholder: HuBERT feature extraction (now in ultimate-rvc)
    # - _extract_pitch_placeholder: RMVPE/CREPE pitch extraction (now in ultimate-rvc)
    # - _rvc_inference_placeholder: RVC inference pipeline (now in ultimate-rvc)
    # - _apply_pitch_shift: Pitch shifting (now handled by ultimate-rvc's n_semitones parameter)

    def real_time_convert(
        self,
        input_device: int = 0,
        output_device: int = 0,
        show_meter: bool = True,
        meter_refresh: float = 0.1,
        pipewire_source: Optional[int] = None,
        pipewire_sink: Optional[int] = None,
        chunk_size: int = 2048,
        pitch_shift: int = 0,
        index_rate: float = 0.75,
    ):
        """
        Perform real-time voice conversion using microphone input

        Args:
            input_device: PyAudio input device index
            output_device: PyAudio output device index
            show_meter: Whether to show audio level meter
            meter_refresh: Meter refresh rate in seconds
            pipewire_source: PipeWire source node ID (for pw-cat)
            pipewire_sink: PipeWire sink node ID (for pw-cat)
            chunk_size: Processing chunk size in samples (default: 2048 ≈ 43ms @ 48kHz)
            pitch_shift: Pitch shift in semitones (-24 to +24)
            index_rate: Feature retrieval strength (0.0 to 1.0)

        Note: Real-time conversion requires the following additional dependencies:
        - PortAudio library (system library) - installed
        - PyAudio Python package - installed

        Target Latency: <100ms using StreamingConverter (no per-chunk disk I/O)
        """
        use_pwcat = shutil.which("pw-cat") is not None

        if use_pwcat:
            print("pw-cat detected - using PipeWire default devices for streaming.")
            self._real_time_convert_pwcat(
                show_meter=show_meter,
                meter_refresh=meter_refresh,
                source_id=pipewire_source,
                sink_id=pipewire_sink,
                chunk_size=chunk_size,
                pitch_shift=pitch_shift,
                index_rate=index_rate,
            )
            return

        import pyaudio
        import numpy as np
        from rwc.streaming import (
            StreamingConverter,
            BatchConverter,
            StreamingPipeline,
            ConversionConfig,
            BufferConfig
        )

        print(f"Starting real-time conversion on device {input_device} -> {output_device}")
        print(f"Using {'RMVPE' if self.use_rmvpe else 'default'} pitch extraction")
        print(f"Chunk size: {chunk_size} samples (~{chunk_size / 48000 * 1000:.1f}ms @ 48kHz)")
        print("Expected latency: <100ms with streaming backend")

        # Set up audio parameters
        chunk = chunk_size  # Align device buffers with processing window
        FORMAT = pyaudio.paFloat32
        CHANNELS = 1  # Mono for RVC processing
        RATE = 48000  # Sample rate to match RVC models

        # Initialize streaming pipeline
        conversion_config = ConversionConfig(
            model_path=str(self.model_path),
            pitch_shift=pitch_shift,
            index_rate=index_rate,
            sample_rate=RATE,
            use_rmvpe=self.use_rmvpe,
            chunk_size=chunk_size
        )

        buffer_config = BufferConfig(
            chunk_size=chunk_size,
            sample_rate=RATE,
            channels=CHANNELS
        )

        try:
            backend = StreamingConverter(conversion_config)
        except Exception:
            print("Streaming backend initialization failed, falling back to batch mode (higher latency)")
            backend = BatchConverter(conversion_config)

        def _log_metrics(metrics: dict) -> None:
            buffer_latency = metrics['buffer_health'].get('total_latency_ms', 0.0)
            total_latency = metrics.get('total_latency_ms', 0.0)
            processing_time = metrics.get('processing_time_ms', 0.0)
            sys.stdout.write(
                f"\rLatency ~{total_latency:.1f}ms (proc {processing_time:.1f}ms, buffer {buffer_latency:.1f}ms)"
            )
            sys.stdout.flush()

        pipeline = StreamingPipeline(backend, buffer_config, on_metrics_update=_log_metrics)

        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            # Start streaming pipeline
            pipeline.start()
            print("Streaming pipeline initialized successfully!")

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

            # Real-time conversion loop
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

                    # Send audio to streaming pipeline for conversion
                    pipeline.process_input(audio_array)

                    # Get converted audio from pipeline
                    processed_audio = pipeline.get_output(chunk)

                    # If no output ready yet, use silence (startup latency)
                    if processed_audio is None:
                        processed_audio = np.zeros(chunk, dtype=np.float32)

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
            import traceback
            traceback.print_exc()
        finally:
            # Clean up
            if 'stream_in' in locals():
                stream_in.stop_stream()
                stream_in.close()
            if 'stream_out' in locals():
                stream_out.stop_stream()
                stream_out.close()
            p.terminate()

            # Stop streaming pipeline
            if 'pipeline' in locals():
                pipeline.stop()

            # Leave a clean newline after live latency updates
            sys.stdout.write("\n")
            sys.stdout.flush()

            # Leave a clean newline after live latency updates
            sys.stdout.write("\n")
            sys.stdout.flush()

            print("Real-time conversion streams closed.")

    def _real_time_convert_pwcat(
        self,
        rate: int = 48000,
        channels: int = 1,
        show_meter: bool = True,
        meter_refresh: float = 0.1,
        source_id: Optional[int] = None,
        sink_id: Optional[int] = None,
        chunk_size: int = 2048,
        pitch_shift: int = 0,
        index_rate: float = 0.75,
    ):
        """
        PipeWire-based real-time loop using pw-cat for capture/playback.

        Args:
            rate: Sample rate in Hz
            channels: Number of audio channels
            show_meter: Whether to show audio level meter
            meter_refresh: Meter refresh rate in seconds
            source_id: PipeWire source node ID (integer only)
            sink_id: PipeWire sink node ID (integer only)
            chunk_size: Processing chunk size in samples (default: 2048 ≈ 43ms @ 48kHz)
            pitch_shift: Pitch shift in semitones (-24 to +24)
            index_rate: Feature retrieval strength (0.0 to 1.0)

        Target Latency: <100ms using StreamingConverter (no per-chunk disk I/O)

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
        from rwc.streaming import (
            StreamingConverter,
            BatchConverter,
            StreamingPipeline,
            ConversionConfig,
            BufferConfig
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
        if not isinstance(chunk_size, int) or chunk_size < 256 or chunk_size > 8192:
            raise ValueError(f"Invalid chunk size: {chunk_size} (must be 256-8192)")

        # Initialize streaming pipeline
        conversion_config = ConversionConfig(
            model_path=str(self.model_path),
            pitch_shift=pitch_shift,
            index_rate=index_rate,
            sample_rate=rate,
            use_rmvpe=self.use_rmvpe,
            chunk_size=chunk_size
        )

        buffer_config = BufferConfig(
            chunk_size=chunk_size,
            sample_rate=rate,
            channels=channels
        )

        try:
            backend = StreamingConverter(conversion_config)
        except Exception:
            print("Streaming backend initialization failed, falling back to batch mode (higher latency)")
            backend = BatchConverter(conversion_config)

        def _log_metrics(metrics: dict) -> None:
            buffer_latency = metrics['buffer_health'].get('total_latency_ms', 0.0)
            total_latency = metrics.get('total_latency_ms', 0.0)
            processing_time = metrics.get('processing_time_ms', 0.0)
            sys.stdout.write(
                f"\rLatency ~{total_latency:.1f}ms (proc {processing_time:.1f}ms, buffer {buffer_latency:.1f}ms)"
            )
            sys.stdout.flush()

        pipeline = StreamingPipeline(backend, buffer_config, on_metrics_update=_log_metrics)

        print(f"Chunk size: {chunk_size} samples (~{chunk_size / rate * 1000:.1f}ms @ {rate}Hz)")
        print("Expected latency: <100ms with streaming backend")

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
        chunk = chunk_size  # Keep pw-cat buffers aligned to processing window
        bytes_per_chunk = chunk * channels * bytes_per_sample
        epsilon = 1e-8
        meter_bar_width = 30
        last_meter_update = time.monotonic()

        print("Opening PipeWire streams (default source/sink)...")

        # Start streaming pipeline
        pipeline.start()
        print("Streaming pipeline initialized successfully!")

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

                # Send audio to streaming pipeline for conversion
                pipeline.process_input(audio_array)

                # Get converted audio from pipeline
                processed = pipeline.get_output(chunk)

                # If no output ready yet, use silence (startup latency)
                if processed is None:
                    processed = np.zeros(chunk, dtype=np.float32)

                # Convert to int16 and write to playback
                processed = np.clip(processed, -1.0, 1.0)
                output_bytes = (processed * 32767.0).astype(np.int16).tobytes()

                play_proc.stdin.write(output_bytes)

        except KeyboardInterrupt:
            print("\nReal-time conversion stopped by user.")
        except Exception as exc:
            print(f"\nError during PipeWire streaming: {exc}")
            import traceback
            traceback.print_exc()
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

            # Stop streaming pipeline
            if 'pipeline' in locals():
                pipeline.stop()

            # Drain stderr for debugging
            for proc, label in [(record_proc, "record"), (play_proc, "playback")]:
                try:
                    if proc.stderr:
                        err = proc.stderr.read().decode().strip()
                        if err:
                            print(f"[pw-cat {label} stderr] {err}")
                except Exception:
                    pass
