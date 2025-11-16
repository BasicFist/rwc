"""
Real-time voice conversion streaming module

This module provides streaming/real-time voice conversion capabilities for RWC.

Architecture:
-----------
Phase 1 (Current):
    - BatchConverter: Uses ultimate-rvc via temporary files
    - Expected latency: 500-700ms
    - Simple, production-ready implementation

Phase 2 (Implemented):
    - StreamingConverter: Direct PyTorch chunk processing
    - Expected latency: <100ms with 2048-sample windows
    - Native RVC inference without file I/O

Components:
----------
- ConversionBackend: Abstract interface for conversion backends
- BufferManager: Input/output audio buffering with context tracking
- StreamingPipeline: Orchestrates audio capture → conversion → playback
- BatchConverter: Phase 1 implementation using ultimate-rvc

Usage:
-----
    from rwc.streaming import (
        BatchConverter,
        StreamingPipeline,
        ConversionConfig,
        BufferConfig
    )

    # Configure conversion backend
    config = ConversionConfig(
        model_path="models/HomerSimpson/model.pth",
        chunk_size=4096,
        pitch_shift=0,
        index_rate=0.75
    )

    # Create backend
    backend = BatchConverter(config)

    # Configure buffering
    buffer_config = BufferConfig(
        chunk_size=4096,
        sample_rate=48000
    )

    # Create pipeline
    pipeline = StreamingPipeline(backend, buffer_config)

    # Start streaming
    pipeline.start()

    # In audio capture callback:
    pipeline.process_input(audio_chunk)

    # In audio playback callback:
    output = pipeline.get_output(chunk_size)

    # Stop streaming
    pipeline.stop()
"""

from .backends import ConversionBackend, ConversionConfig, ConversionMetrics
from .buffer import BufferManager, BufferConfig
from .pipeline import StreamingPipeline
from .batch_backend import BatchConverter
from .streaming_backend import StreamingConverter

__all__ = [
    # Abstract interfaces
    'ConversionBackend',
    'ConversionConfig',
    'ConversionMetrics',

    # Buffer management
    'BufferManager',
    'BufferConfig',

    # Pipeline orchestration
    'StreamingPipeline',

    # Phase 1 backend
    'BatchConverter',

    # Phase 2 backend
    'StreamingConverter',
]

__version__ = '1.0.0'
