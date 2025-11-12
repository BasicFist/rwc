"""
Streaming pipeline orchestration for real-time voice conversion

Coordinates audio capture → buffering → conversion → playback
"""

import time
import threading
from typing import Optional, Callable
import numpy as np

from rwc.streaming.backends import ConversionBackend
from rwc.streaming.buffer import BufferManager, BufferConfig
from rwc.utils.logging_config import get_logger

logger = get_logger(__name__)


class StreamingPipeline:
    """
    Real-time voice conversion pipeline

    Architecture:
    1. Audio capture thread → input buffer
    2. Conversion thread → process chunks → output buffer
    3. Audio playback thread → output buffer → speakers

    Phase 1: Uses BatchConverter (ultimate-rvc)
    Phase 2: Swaps to StreamingConverter (RVC-Project core)

    Usage:
        backend = BatchConverter(config)
        buffer_config = BufferConfig(chunk_size=4096)
        pipeline = StreamingPipeline(backend, buffer_config)

        pipeline.start()

        # In audio capture thread:
        pipeline.process_input(audio_chunk)

        # In audio playback thread:
        output = pipeline.get_output(chunk_size)

        pipeline.stop()
    """

    def __init__(
        self,
        backend: ConversionBackend,
        buffer_config: BufferConfig,
        on_metrics_update: Optional[Callable] = None
    ):
        """
        Initialize streaming pipeline

        Args:
            backend: Conversion backend (BatchConverter or StreamingConverter)
            buffer_config: Buffer configuration
            on_metrics_update: Optional callback for metrics updates
        """
        self.backend = backend
        self.buffer = BufferManager(buffer_config)
        self.on_metrics_update = on_metrics_update

        # Threading
        self.conversion_thread = None
        self.running = False
        self.conversion_lock = threading.Lock()

        # Metrics
        self.total_latency_ms = 0.0
        self.start_time = None
        self.last_metrics_update = 0.0

    def start(self) -> None:
        """
        Initialize backend and start conversion thread

        Raises:
            RuntimeError: If initialization fails
        """
        logger.info("Starting streaming pipeline")

        # Initialize backend (load models)
        self.backend.initialize()

        # Start conversion thread
        self.running = True
        self.conversion_thread = threading.Thread(
            target=self._conversion_loop,
            daemon=True,
            name="RWC-Conversion"
        )
        self.conversion_thread.start()
        self.start_time = time.time()

        logger.info("Streaming pipeline started")

    def stop(self) -> None:
        """Stop conversion thread and cleanup"""
        logger.info("Stopping streaming pipeline")

        self.running = False
        if self.conversion_thread:
            self.conversion_thread.join(timeout=2.0)
            if self.conversion_thread.is_alive():
                logger.warning("Conversion thread did not stop gracefully")

        self.backend.cleanup()

        logger.info("Streaming pipeline stopped")

    def process_input(self, audio_data: np.ndarray) -> None:
        """
        Called by audio capture thread to write captured audio to input buffer

        Args:
            audio_data: Captured audio samples
        """
        self.buffer.write_input(audio_data)

    def get_output(self, size: int) -> Optional[np.ndarray]:
        """
        Called by audio playback thread to get converted audio for playback

        Args:
            size: Number of samples to read

        Returns:
            Converted audio or None if not ready
        """
        return self.buffer.read_output(size)

    def _conversion_loop(self) -> None:
        """
        Conversion thread main loop

        Processes chunks as they become available in the input buffer.
        """
        logger.debug("Conversion loop started")

        while self.running:
            # Check if buffer has enough data
            if not self.buffer.has_chunk_ready():
                time.sleep(0.001)  # 1ms sleep to avoid busy-wait
                continue

            # Read chunk + context
            chunk, context = self.buffer.read_chunk_for_processing()

            # Convert chunk
            start_time = time.perf_counter()
            try:
                with self.conversion_lock:
                    converted_chunk = self.backend.convert_chunk(chunk, context)
            except Exception as e:
                logger.error(f"Chunk conversion failed: {e}")
                # On error, use original chunk as fallback
                converted_chunk = chunk

            end_time = time.perf_counter()

            # Write to output buffer
            self.buffer.write_output(converted_chunk)

            # Update metrics
            processing_time_ms = (end_time - start_time) * 1000
            self.total_latency_ms = self.backend.get_latency_estimate_ms()

            # Call metrics callback (if provided and interval elapsed)
            now = time.time()
            if self.on_metrics_update and (now - self.last_metrics_update) >= 0.5:
                metrics = {
                    'processing_time_ms': processing_time_ms,
                    'total_latency_ms': self.total_latency_ms,
                    'chunks_processed': self.backend.metrics.total_chunks_processed,
                    'dropped_chunks': self.backend.metrics.dropped_chunks,
                    'buffer_health': self.buffer.get_buffer_health()
                }
                try:
                    self.on_metrics_update(metrics)
                except Exception as e:
                    logger.warning(f"Metrics callback failed: {e}")

                self.last_metrics_update = now

        logger.debug("Conversion loop stopped")

    def get_metrics(self) -> dict:
        """
        Return current pipeline metrics

        Returns:
            Dictionary with comprehensive metrics
        """
        uptime_s = time.time() - self.start_time if self.start_time else 0

        return {
            'uptime_seconds': uptime_s,
            'total_latency_ms': self.total_latency_ms,
            'backend_metrics': {
                'processing_time_ms': self.backend.metrics.processing_time_ms,
                'chunks_processed': self.backend.metrics.total_chunks_processed,
                'dropped_chunks': self.backend.metrics.dropped_chunks
            },
            'buffer_metrics': self.buffer.get_buffer_health()
        }

    def is_running(self) -> bool:
        """Check if pipeline is running"""
        return self.running and self.conversion_thread is not None and self.conversion_thread.is_alive()
