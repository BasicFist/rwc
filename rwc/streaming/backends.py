"""
Abstract backend interface for voice conversion in streaming mode

This module defines the contract that all conversion backends must implement,
enabling swapping between BatchConverter (Phase 1) and StreamingConverter (Phase 2).
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class ConversionConfig:
    """Configuration for voice conversion backend"""
    model_path: str
    pitch_shift: int = 0
    index_rate: float = 0.75
    sample_rate: int = 48000
    use_rmvpe: bool = True

    # Streaming-specific
    chunk_size: int = 4096      # Samples per chunk (~85ms @ 48kHz)
    lookahead_size: int = 0     # Future context (Phase 2 only)
    context_size: int = 0       # Past context (Phase 2 only)


@dataclass
class ConversionMetrics:
    """Performance metrics for monitoring"""
    processing_time_ms: float = 0.0
    chunk_latency_ms: float = 0.0
    total_chunks_processed: int = 0
    dropped_chunks: int = 0


class ConversionBackend(ABC):
    """
    Abstract interface for voice conversion backends

    Implementations:
    - BatchConverter (Phase 1): Uses ultimate-rvc via temporary files
    - StreamingConverter (Phase 2): Direct PyTorch chunk processing

    Usage:
        config = ConversionConfig(model_path="models/model.pth")
        backend = BatchConverter(config)
        backend.initialize()

        chunk = np.random.rand(4096)
        converted = backend.convert_chunk(chunk)

        backend.cleanup()
    """

    def __init__(self, config: ConversionConfig):
        self.config = config
        self.metrics = ConversionMetrics()

    @abstractmethod
    def initialize(self) -> None:
        """
        Load models and prepare for conversion

        Called once before streaming starts. Should load all necessary
        models into memory/GPU.

        Raises:
            RuntimeError: If initialization fails
        """
        pass

    @abstractmethod
    def convert_chunk(
        self,
        audio_chunk: np.ndarray,
        context: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Convert a single audio chunk

        Args:
            audio_chunk: Input audio (shape: [chunk_size] or [chunk_size, channels])
            context: Previous audio context for continuity (Phase 2 only)

        Returns:
            Converted audio chunk (same shape as input)

        Raises:
            RuntimeError: If conversion fails
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Release resources (models, temp files, GPU memory, etc.)

        Called when streaming stops. Should free all allocated resources.
        """
        pass

    def get_latency_estimate_ms(self) -> float:
        """
        Estimate expected latency for current configuration

        Used for buffer sizing and user feedback.

        Returns:
            Estimated latency in milliseconds
        """
        return self.metrics.chunk_latency_ms if self.metrics.chunk_latency_ms > 0 else 500.0
