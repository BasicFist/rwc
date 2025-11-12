"""
Phase 1 batch conversion backend using ultimate-rvc

Converts audio chunks by writing to temporary files and using
the existing convert_voice() method from VoiceConverter.
"""

import tempfile
import time
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf

from rwc.streaming.backends import ConversionBackend, ConversionConfig
from rwc.utils.logging_config import get_logger

logger = get_logger(__name__)


class BatchConverter(ConversionBackend):
    """
    Phase 1 backend using ultimate-rvc for conversion

    Strategy:
    1. Save audio chunk to temporary WAV file
    2. Call VoiceConverter.convert_voice() (uses ultimate-rvc)
    3. Load converted audio from output file
    4. Clean up temporary files
    5. Return converted chunk

    Trade-offs:
    - Higher latency (500ms-1s) due to file I/O overhead
    - Simpler implementation (reuses existing convert_voice)
    - Production-ready (uses tested ultimate-rvc pipeline)
    - No streaming optimizations

    Expected latency breakdown:
    - File write: ~10-20ms
    - ultimate-rvc conversion: ~300-700ms (depends on chunk size)
    - File read: ~10-20ms
    - Total: ~320-740ms + chunk duration

    Usage:
        config = ConversionConfig(
            model_path="models/HomerSimpson/model.pth",
            chunk_size=4096
        )
        backend = BatchConverter(config)
        backend.initialize()

        chunk = np.random.rand(4096)
        converted = backend.convert_chunk(chunk)

        backend.cleanup()
    """

    def __init__(self, config: ConversionConfig):
        super().__init__(config)
        self.temp_dir = None
        self.voice_converter = None

    def initialize(self) -> None:
        """
        Load VoiceConverter for batch processing

        Creates temporary directory and initializes VoiceConverter
        with the specified model.

        Raises:
            RuntimeError: If model loading fails
        """
        from rwc.core import VoiceConverter

        logger.info("Initializing BatchConverter with ultimate-rvc backend")
        logger.info(f"Model: {self.config.model_path}")
        logger.info(f"Chunk size: {self.config.chunk_size} samples ({self.config.chunk_size / self.config.sample_rate * 1000:.1f}ms)")

        # Create temp directory for chunk files
        self.temp_dir = tempfile.mkdtemp(prefix="rwc_streaming_")
        logger.debug(f"Temporary directory: {self.temp_dir}")

        try:
            # Initialize VoiceConverter (loads models)
            self.voice_converter = VoiceConverter(
                model_path=self.config.model_path,
                use_rmvpe=self.config.use_rmvpe
            )
            logger.info("BatchConverter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VoiceConverter: {e}")
            # Cleanup temp dir on failure
            if self.temp_dir and Path(self.temp_dir).exists():
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise RuntimeError(f"BatchConverter initialization failed: {e}")

    def convert_chunk(
        self,
        audio_chunk: np.ndarray,
        context: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Convert chunk by: chunk → temp file → ultimate-rvc → load result

        Args:
            audio_chunk: Input audio chunk
            context: Previous audio context (ignored in Phase 1)

        Returns:
            Converted audio chunk (same length as input)

        Raises:
            RuntimeError: If conversion fails
        """
        if self.voice_converter is None:
            raise RuntimeError("BatchConverter not initialized - call initialize() first")

        start_time = time.perf_counter()
        chunk_id = self.metrics.total_chunks_processed

        # Generate unique temp file names
        input_temp = Path(self.temp_dir) / f"chunk_{chunk_id:06d}_in.wav"
        output_temp = Path(self.temp_dir) / f"chunk_{chunk_id:06d}_out.wav"

        try:
            # Save chunk to temp file
            write_start = time.perf_counter()
            sf.write(str(input_temp), audio_chunk, self.config.sample_rate)
            write_time = (time.perf_counter() - write_start) * 1000

            # Convert using ultimate-rvc (via VoiceConverter)
            convert_start = time.perf_counter()
            self.voice_converter.convert_voice(
                input_audio=str(input_temp),
                output_audio=str(output_temp),
                pitch_shift=self.config.pitch_shift,
                index_rate=self.config.index_rate,
                sample_rate=self.config.sample_rate
            )
            convert_time = (time.perf_counter() - convert_start) * 1000

            # Load converted audio
            read_start = time.perf_counter()
            converted_audio, _ = sf.read(str(output_temp))
            read_time = (time.perf_counter() - read_start) * 1000

            # Ensure same length as input (trim or pad if needed)
            if len(converted_audio) > len(audio_chunk):
                converted_audio = converted_audio[:len(audio_chunk)]
            elif len(converted_audio) < len(audio_chunk):
                pad_length = len(audio_chunk) - len(converted_audio)
                converted_audio = np.pad(converted_audio, (0, pad_length), mode='constant')

            # Update metrics
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000
            self.metrics.processing_time_ms = processing_time_ms
            self.metrics.chunk_latency_ms = processing_time_ms
            self.metrics.total_chunks_processed += 1

            logger.debug(
                f"Chunk {chunk_id} processed in {processing_time_ms:.1f}ms "
                f"(write: {write_time:.1f}ms, convert: {convert_time:.1f}ms, read: {read_time:.1f}ms)"
            )

            return converted_audio

        except Exception as e:
            logger.error(f"Chunk {chunk_id} conversion failed: {e}")
            self.metrics.dropped_chunks += 1
            # Return original audio as fallback
            return audio_chunk

        finally:
            # Clean up temp files
            try:
                if input_temp.exists():
                    input_temp.unlink()
                if output_temp.exists():
                    output_temp.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp files: {e}")

    def cleanup(self) -> None:
        """
        Remove temp directory and release models

        Cleans up all temporary files and releases VoiceConverter resources.
        """
        import shutil

        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

        # Models are cleaned up by VoiceConverter destructor
        self.voice_converter = None
        logger.info(f"BatchConverter cleaned up (processed {self.metrics.total_chunks_processed} chunks, dropped {self.metrics.dropped_chunks})")

    def get_latency_estimate_ms(self) -> float:
        """
        Estimate latency based on chunk size and processing overhead

        Phase 1 components:
        - File I/O: ~30-50ms (write + read)
        - ultimate-rvc processing: ~300-700ms (depending on chunk size and GPU)
        - Buffer overhead: ~85ms (chunk duration @ 4096 samples)

        Total: ~415-835ms

        Returns:
            Estimated latency in milliseconds
        """
        # Use measured latency if available
        if self.metrics.chunk_latency_ms > 0:
            return self.metrics.chunk_latency_ms

        # Otherwise estimate
        chunk_duration_ms = (self.config.chunk_size / self.config.sample_rate) * 1000
        file_io_overhead_ms = 40
        urvc_processing_ms = chunk_duration_ms * 4  # Empirical: 4x real-time
        buffer_overhead_ms = chunk_duration_ms

        return chunk_duration_ms + file_io_overhead_ms + urvc_processing_ms + buffer_overhead_ms
