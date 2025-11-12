"""
Buffer management for streaming audio processing

Handles input/output buffering, lookahead, and context management
for smooth real-time voice conversion.
"""

import numpy as np
from collections import deque
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class BufferConfig:
    """Buffer management configuration"""
    chunk_size: int = 4096          # Samples per processing chunk
    lookahead_chunks: int = 0       # Future context (Phase 2)
    context_chunks: int = 0         # Past context (Phase 2)
    sample_rate: int = 48000
    channels: int = 1

    @property
    def lookahead_size(self) -> int:
        """Number of lookahead samples"""
        return self.chunk_size * self.lookahead_chunks

    @property
    def context_size(self) -> int:
        """Number of context samples"""
        return self.chunk_size * self.context_chunks


class BufferManager:
    """
    Ring buffer with lookahead and context management

    Phase 1: Simple chunking (no lookahead/context)
    Phase 2: Full lookahead + context for RVC continuity

    Usage:
        config = BufferConfig(chunk_size=4096)
        buffer_mgr = BufferManager(config)

        # Write captured audio
        buffer_mgr.write_input(audio_data)

        # Check if ready for processing
        if buffer_mgr.has_chunk_ready():
            chunk, context = buffer_mgr.read_chunk_for_processing()
            # ... convert chunk ...
            buffer_mgr.write_output(converted_chunk)

        # Read for playback
        output = buffer_mgr.read_output(chunk_size)
    """

    def __init__(self, config: BufferConfig):
        self.config = config

        # Input buffer (collects audio from capture)
        max_buffer_size = config.chunk_size * 10  # ~200ms @ 48kHz, 4096 chunk
        self.input_buffer = np.zeros(max_buffer_size, dtype=np.float32)
        self.input_write_pos = 0

        # Context buffer (previous audio for Phase 2)
        self.context_buffer = deque(maxlen=config.context_chunks)

        # Output buffer (converted audio ready for playback)
        self.output_buffer = deque(maxlen=20)  # Up to ~400ms output

        # Crossfade support (to smooth chunk boundaries)
        self.crossfade_samples = min(512, config.chunk_size // 8)  # ~10ms crossfade
        self.last_chunk_tail = None  # Store tail of previous chunk for crossfade

        # Metrics
        self.total_samples_received = 0
        self.total_samples_output = 0

    def write_input(self, audio_data: np.ndarray) -> None:
        """
        Write captured audio to input buffer

        Args:
            audio_data: Audio samples to write
        """
        samples_to_write = len(audio_data)

        # Append to buffer
        if self.input_write_pos + samples_to_write <= len(self.input_buffer):
            self.input_buffer[self.input_write_pos:self.input_write_pos + samples_to_write] = audio_data
            self.input_write_pos += samples_to_write
        else:
            # Buffer overflow - handle based on overflow size
            if samples_to_write >= len(self.input_buffer):
                # Input larger than buffer - take only the last portion that fits
                self.input_buffer[:] = audio_data[-len(self.input_buffer):]
                self.input_write_pos = len(self.input_buffer)
            else:
                # Shift left and append
                shift_amount = samples_to_write
                self.input_buffer[:-shift_amount] = self.input_buffer[shift_amount:]
                self.input_buffer[-shift_amount:] = audio_data
                self.input_write_pos = len(self.input_buffer)

        self.total_samples_received += samples_to_write

    def has_chunk_ready(self) -> bool:
        """
        Check if buffer has enough data for processing

        Returns:
            True if a chunk can be extracted
        """
        return self.input_write_pos >= self.config.chunk_size

    def read_chunk_for_processing(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Read chunk + context for conversion

        Returns:
            (chunk, context) where:
            - chunk: Audio to convert (size: chunk_size)
            - context: Previous audio for continuity (Phase 2 only, None in Phase 1)
        """
        # Extract chunk
        chunk = self.input_buffer[:self.config.chunk_size].copy()

        # Get context (if available and needed)
        context = None
        if len(self.context_buffer) > 0:
            context = np.concatenate(list(self.context_buffer))

        # Shift buffer
        self.input_buffer[:-self.config.chunk_size] = self.input_buffer[self.config.chunk_size:]
        self.input_write_pos -= self.config.chunk_size

        # Save this chunk as context for next iteration (Phase 2)
        if self.config.context_chunks > 0:
            self.context_buffer.append(chunk)

        return chunk, context

    def write_output(self, converted_audio: np.ndarray) -> None:
        """
        Write converted audio to output buffer with crossfading

        Applies crossfading between chunks to smooth transitions and
        reduce audible "seams" between independently processed chunks.

        Args:
            converted_audio: Converted audio chunk
        """
        # Apply crossfading to smooth chunk boundaries
        if self.last_chunk_tail is not None and len(converted_audio) > self.crossfade_samples:
            # Create crossfade window (linear fade)
            fade_out = np.linspace(1.0, 0.0, self.crossfade_samples, dtype=np.float32)
            fade_in = np.linspace(0.0, 1.0, self.crossfade_samples, dtype=np.float32)

            # Apply crossfade to beginning of new chunk
            crossfade_region = converted_audio[:self.crossfade_samples].copy()
            crossfade_region = (self.last_chunk_tail * fade_out) + (crossfade_region * fade_in)

            # Replace beginning of chunk with crossfaded version
            converted_audio = converted_audio.copy()  # Avoid modifying original
            converted_audio[:self.crossfade_samples] = crossfade_region

        # Save tail of this chunk for next iteration
        if len(converted_audio) > self.crossfade_samples:
            self.last_chunk_tail = converted_audio[-self.crossfade_samples:].copy()
        else:
            self.last_chunk_tail = converted_audio.copy()

        self.output_buffer.append(converted_audio)
        self.total_samples_output += len(converted_audio)

    def read_output(self, size: int) -> Optional[np.ndarray]:
        """
        Read converted audio for playback

        Args:
            size: Number of samples to read

        Returns:
            Audio data or None if not enough buffered
        """
        if len(self.output_buffer) == 0:
            return None

        # Get oldest chunk
        chunk = self.output_buffer.popleft()

        # If requested size differs, handle it
        if len(chunk) >= size:
            return chunk[:size]
        else:
            return chunk  # Return what we have

    def get_buffer_health(self) -> dict:
        """
        Return buffer status for monitoring

        Returns:
            Dictionary with buffer statistics
        """
        return {
            'input_fill_percent': (self.input_write_pos / len(self.input_buffer)) * 100,
            'output_chunks_ready': len(self.output_buffer),
            'context_chunks': len(self.context_buffer),
            'total_latency_samples': len(self.output_buffer) * self.config.chunk_size,
            'total_latency_ms': (len(self.output_buffer) * self.config.chunk_size / self.config.sample_rate) * 1000
        }

    def clear(self) -> None:
        """Reset all buffers"""
        self.input_buffer.fill(0)
        self.input_write_pos = 0
        self.context_buffer.clear()
        self.output_buffer.clear()
        self.last_chunk_tail = None  # Reset crossfade state
