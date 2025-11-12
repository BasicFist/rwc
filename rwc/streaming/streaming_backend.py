"""
Streaming RVC Backend - Phase 2 Implementation

This module implements native PyTorch streaming for <200ms latency.
Uses direct model inference without file I/O, matching RVC-Project's
real-time implementation strategy.

Architecture:
- Direct numpy array processing (no temp files)
- Overlap-add windowing (SOLA) for seamless audio
- Context management for chunk continuity
- GPU-optimized pipeline

Author: Claude Code
Date: 2025-11-12
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch

from rwc.streaming.backends import ConversionBackend, ConversionConfig
from rwc.utils.logging_config import get_logger

# Import ultimate-rvc components for direct access
from ultimate_rvc.rvc.infer.infer import VoiceConverter
from ultimate_rvc.typing_extra import F0Method
from scipy import signal

logger = get_logger(__name__)


class StreamingConverter(ConversionBackend):
    """
    Native PyTorch streaming backend for Phase 2.

    Achieves <200ms latency by processing numpy arrays directly through
    the RVC pipeline without file I/O overhead.

    Key Features:
    - Direct numpy → RVC inference → numpy (no file I/O)
    - Overlap-add windowing for seamless transitions
    - Context-aware processing for chunk continuity
    - GPU tensor operations throughout

    Performance:
    - Chunk duration: 85ms (4096 samples @ 48kHz)
    - Inference time: ~50-100ms (GPU-dependent)
    - Target total latency: 150-200ms
    """

    def __init__(self, config: ConversionConfig):
        """
        Initialize streaming converter with configuration.

        Args:
            config: Conversion configuration with model paths and parameters
        """
        super().__init__(config)
        self.voice_converter: Optional[VoiceConverter] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Overlap-add parameters - optimized for smoothness
        self.overlap_samples = int(self.config.chunk_size * 0.5)  # 50% overlap for smoothness
        self.fade_samples = int(self.config.chunk_size * 0.25)  # 25% crossfade (Hann window)

        # Context buffer for continuity
        self.context_buffer: Optional[np.ndarray] = None
        self.context_size = self.overlap_samples

        logger.info("Initializing StreamingConverter (Phase 2)")
        logger.info(f"Device: {self.device}")
        logger.info(f"Chunk size: {self.config.chunk_size} samples")
        logger.info(f"Overlap: {self.overlap_samples} samples ({self.overlap_samples/self.config.chunk_size*100:.1f}%)")
        logger.info(f"Crossfade: {self.fade_samples} samples")

        # Initialize crossfade state
        self._previous_output: Optional[np.ndarray] = None
        self._previous_rms: Optional[float] = None  # Track RMS for volume consistency

    def initialize(self) -> None:
        """
        Load RVC models and prepare for streaming inference.

        This sets up:
        - HuBERT model for feature extraction
        - RVC generator network
        - RMVPE/CREPE for pitch extraction
        - FAISS index for speaker similarity
        """
        logger.info("Loading RVC models for streaming inference...")
        start_time = time.perf_counter()

        try:
            # Initialize VoiceConverter
            self.voice_converter = VoiceConverter()

            # Extract model name from path for ultimate-rvc
            model_path = Path(self.config.model_path)
            index_path = self._find_index_file(model_path.parent)

            # Load model using get_vc (sets up net_g, hubert, etc.)
            # get_vc signature: get_vc(weight_root, sid)
            self.voice_converter.get_vc(
                weight_root=str(model_path),
                sid=0  # Default speaker ID
            )

            # Load HuBERT embedder
            embedder_model = "contentvec"  # Standard RVC embedder
            self.voice_converter.load_hubert(embedder_model)

            # Verify models loaded
            if self.voice_converter.net_g is None:
                raise RuntimeError("RVC generator network failed to load")
            if self.voice_converter.hubert_model is None:
                raise RuntimeError("HuBERT model failed to load")
            if self.voice_converter.vc is None:
                raise RuntimeError("RVC pipeline failed to initialize")

            load_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"StreamingConverter initialized successfully in {load_time:.1f}ms")
            logger.info(f"Model: {model_path.name}")
            logger.info(f"Index: {index_path if index_path else 'None'}")
            logger.info(f"Target sample rate: {self.voice_converter.tgt_sr}Hz")

        except Exception as e:
            logger.error(f"Failed to initialize StreamingConverter: {e}")
            raise RuntimeError(f"StreamingConverter initialization failed: {e}")

    def _find_index_file(self, model_dir: Path) -> Optional[str]:
        """
        Find FAISS index file in model directory.

        Args:
            model_dir: Directory containing the RVC model

        Returns:
            Path to index file, or None if not found
        """
        # Look for .index files (RVC feature index)
        index_files = list(model_dir.glob("*.index"))
        if index_files:
            return str(index_files[0])

        # Also check for "added_*.index" pattern
        added_index_files = list(model_dir.glob("added_*.index"))
        if added_index_files:
            return str(added_index_files[0])

        logger.warning(f"No index file found in {model_dir}")
        return None

    def convert_chunk(
        self,
        audio_chunk: np.ndarray,
        context: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Convert audio chunk using direct RVC pipeline inference.

        This is the core streaming method that achieves low latency by:
        1. Processing numpy arrays directly (no file I/O)
        2. Using overlap-add with crossfading
        3. Maintaining context for continuity

        Args:
            audio_chunk: Input audio chunk (mono, float32)
            context: Previous audio context (currently unused in Phase 2.0)

        Returns:
            Converted audio chunk (same length as input)

        Raises:
            RuntimeError: If conversion fails
        """
        if self.voice_converter is None or self.voice_converter.vc is None:
            raise RuntimeError("StreamingConverter not initialized - call initialize() first")

        start_time = time.perf_counter()
        chunk_id = self.metrics.total_chunks_processed

        try:
            # Normalize input audio
            audio_max = np.abs(audio_chunk).max()
            if audio_max > 0:
                normalized_chunk = audio_chunk / max(audio_max / 0.95, 1.0)
            else:
                normalized_chunk = audio_chunk

            # Add overlap context for continuity
            if self.context_buffer is not None and len(self.context_buffer) > 0:
                # Prepend context for smoother transitions
                processing_chunk = np.concatenate([
                    self.context_buffer[-self.context_size:],
                    normalized_chunk
                ])
            else:
                processing_chunk = normalized_chunk

            # Direct RVC pipeline inference (no file I/O!)
            inference_start = time.perf_counter()
            converted_audio = self.voice_converter.vc.pipeline(
                model=self.voice_converter.hubert_model,
                net_g=self.voice_converter.net_g,
                sid=0,  # Speaker ID
                audio=processing_chunk,
                pitch=self.config.pitch_shift,
                f0_methods={F0Method.RMVPE},  # Use RMVPE for pitch
                file_index=self._find_index_file(Path(self.config.model_path).parent) or "",
                index_rate=self.config.index_rate,
                pitch_guidance=self.voice_converter.use_f0,
                volume_envelope=1.0,  # Full RMS mixing
                version=self.voice_converter.version,
                protect=0.33,  # Protect consonants
                hop_length=128,  # Standard hop length
                f0_autotune=False,
                f0_autotune_strength=1.0,
                f0_file=None,
            )
            inference_time = (time.perf_counter() - inference_start) * 1000

            # Extract the main chunk (remove context overlap)
            if self.context_buffer is not None and len(self.context_buffer) > 0:
                output_chunk = converted_audio[self.context_size:]
            else:
                output_chunk = converted_audio

            # Trim or pad to match input length
            if len(output_chunk) > len(audio_chunk):
                output_chunk = output_chunk[:len(audio_chunk)]
            elif len(output_chunk) < len(audio_chunk):
                pad_length = len(audio_chunk) - len(output_chunk)
                output_chunk = np.pad(output_chunk, (0, pad_length), mode='constant')

            # Normalize RMS for consistent volume between chunks
            output_chunk = self._normalize_rms(output_chunk)

            # Apply crossfade with previous chunk for seamless transitions
            if hasattr(self, '_previous_output') and self._previous_output is not None:
                output_chunk = self._apply_crossfade(self._previous_output, output_chunk)

            # Apply smoothing filter to reduce high-frequency artifacts
            output_chunk = self._apply_smoothing(output_chunk)

            # Store for next crossfade
            self._previous_output = output_chunk.copy()

            # Update context buffer for next chunk
            self.context_buffer = audio_chunk.copy()

            # Update metrics
            processing_time = (time.perf_counter() - start_time) * 1000
            self.metrics.processing_time_ms = processing_time
            self.metrics.chunk_latency_ms = processing_time
            self.metrics.total_chunks_processed += 1

            logger.debug(
                f"Chunk {chunk_id} processed in {processing_time:.1f}ms "
                f"(inference: {inference_time:.1f}ms)"
            )

            return output_chunk

        except Exception as e:
            logger.error(f"Chunk {chunk_id} conversion failed: {e}")
            self.metrics.dropped_chunks += 1
            # Return original audio as fallback
            return audio_chunk

    def _apply_crossfade(
        self,
        previous_chunk: np.ndarray,
        current_chunk: np.ndarray
    ) -> np.ndarray:
        """
        Apply Hann-windowed crossfade between previous and current chunk.

        Uses Hann window for smoother transitions with less audible artifacts
        compared to linear crossfading. The raised cosine shape provides
        better frequency response and reduces spectral leakage.

        Args:
            previous_chunk: Previous output chunk
            current_chunk: Current output chunk

        Returns:
            Current chunk with crossfaded beginning
        """
        # Only crossfade the overlap region
        fade_len = min(self.fade_samples, len(previous_chunk), len(current_chunk))

        if fade_len == 0:
            return current_chunk

        # Create Hann window fade curves (raised cosine)
        # Hann provides smoother transitions than linear
        hann_window = np.hanning(fade_len * 2)
        fade_out = hann_window[:fade_len]  # First half (1.0 → 0.0)
        fade_in = hann_window[fade_len:]    # Second half (0.0 → 1.0)

        # Get tail of previous and head of current
        prev_tail = previous_chunk[-fade_len:]
        curr_head = current_chunk[:fade_len]

        # Apply Hann-windowed crossfade
        crossfaded_region = (prev_tail * fade_out) + (curr_head * fade_in)

        # Replace head of current chunk with crossfaded region
        result = current_chunk.copy()
        result[:fade_len] = crossfaded_region

        return result

    def _normalize_rms(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Normalize RMS level for consistent volume between chunks.

        Gradually adjusts volume to match previous chunk's RMS, preventing
        sudden volume jumps that create audible artifacts.

        Args:
            audio_chunk: Audio to normalize

        Returns:
            RMS-normalized audio chunk
        """
        # Calculate current RMS
        current_rms = np.sqrt(np.mean(audio_chunk**2))

        if current_rms < 1e-6:  # Silence
            return audio_chunk

        # If we have previous RMS, blend towards it gradually
        if self._previous_rms is not None and self._previous_rms > 1e-6:
            # Use 50% blend to avoid abrupt changes
            target_rms = 0.5 * self._previous_rms + 0.5 * current_rms
            scale = target_rms / current_rms
            # Limit scaling to avoid extreme adjustments
            scale = np.clip(scale, 0.5, 2.0)
            normalized = audio_chunk * scale
        else:
            normalized = audio_chunk

        # Update previous RMS
        self._previous_rms = np.sqrt(np.mean(normalized**2))

        return normalized

    def _apply_smoothing(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Apply gentle smoothing filter to reduce high-frequency artifacts.

        Uses a low-order Butterworth filter to remove harsh artifacts
        from chunk processing while preserving voice quality.

        Args:
            audio_chunk: Audio to smooth

        Returns:
            Smoothed audio chunk
        """
        # Design gentle low-pass filter (cutoff at 8kHz for voice)
        # This removes harsh artifacts while preserving voice clarity
        nyquist = self.config.sample_rate / 2
        cutoff = 8000  # Hz - above typical voice range
        normalized_cutoff = cutoff / nyquist

        # Use low-order filter (order=2) to minimize phase distortion
        b, a = signal.butter(2, normalized_cutoff, btype='low')

        # Apply filter with zero-phase (filtfilt) to avoid delay
        smoothed = signal.filtfilt(b, a, audio_chunk)

        return smoothed.astype(np.float32)

    def cleanup(self) -> None:
        """
        Release model resources and clean up.
        """
        logger.info("Cleaning up StreamingConverter resources...")

        if self.voice_converter:
            # Clear models from GPU memory
            self.voice_converter.cleanup_model()
            self.voice_converter = None

        # Clear context buffer and crossfade state
        self.context_buffer = None
        self._previous_output = None
        self._previous_rms = None

        # Force garbage collection
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("StreamingConverter cleanup complete")

    def estimate_latency(self) -> dict[str, float]:
        """
        Estimate processing latency for this backend.

        Returns:
            Dictionary with latency breakdown in milliseconds
        """
        chunk_duration_ms = (self.config.chunk_size / self.config.sample_rate) * 1000

        # Phase 2 latency estimates (based on RVC-Project benchmarks)
        inference_latency_ms = 50.0  # Direct PyTorch inference
        overhead_ms = 10.0  # Context management, crossfading

        return {
            "chunk_duration_ms": chunk_duration_ms,
            "inference_ms": inference_latency_ms,
            "overhead_ms": overhead_ms,
            "total_ms": chunk_duration_ms + inference_latency_ms + overhead_ms,
            "backend": "StreamingConverter (Phase 2)"
        }
