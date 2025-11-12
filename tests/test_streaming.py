"""
Tests for real-time streaming voice conversion module
"""

import pytest
import numpy as np
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from rwc.streaming import (
    ConversionBackend,
    ConversionConfig,
    ConversionMetrics,
    BufferManager,
    BufferConfig,
    StreamingPipeline,
    BatchConverter,
)


# Test fixtures

@pytest.fixture
def conversion_config():
    """Sample conversion configuration"""
    return ConversionConfig(
        model_path="models/test_model.pth",
        pitch_shift=0,
        index_rate=0.75,
        sample_rate=48000,
        use_rmvpe=True,
        chunk_size=4096
    )


@pytest.fixture
def buffer_config():
    """Sample buffer configuration"""
    return BufferConfig(
        chunk_size=4096,
        lookahead_chunks=0,
        context_chunks=0,
        sample_rate=48000,
        channels=1
    )


@pytest.fixture
def sample_audio_chunk():
    """Generate sample audio chunk"""
    return np.random.randn(4096).astype(np.float32)


@pytest.fixture
def mock_backend():
    """Mock conversion backend"""
    backend = Mock(spec=ConversionBackend)
    backend.metrics = ConversionMetrics()
    backend.convert_chunk.return_value = np.zeros(4096, dtype=np.float32)
    backend.get_latency_estimate_ms.return_value = 500.0
    return backend


# BufferManager Tests

class TestBufferManager:
    """Test BufferManager class"""

    def test_initialization(self, buffer_config):
        """Test buffer manager initialization"""
        buffer_mgr = BufferManager(buffer_config)

        assert buffer_mgr.config == buffer_config
        assert buffer_mgr.input_write_pos == 0
        assert len(buffer_mgr.output_buffer) == 0
        assert buffer_mgr.total_samples_received == 0

    def test_write_input(self, buffer_config, sample_audio_chunk):
        """Test writing audio to input buffer"""
        buffer_mgr = BufferManager(buffer_config)

        buffer_mgr.write_input(sample_audio_chunk)

        assert buffer_mgr.input_write_pos == len(sample_audio_chunk)
        assert buffer_mgr.total_samples_received == len(sample_audio_chunk)

    def test_has_chunk_ready(self, buffer_config, sample_audio_chunk):
        """Test chunk ready detection"""
        buffer_mgr = BufferManager(buffer_config)

        # Not ready initially
        assert not buffer_mgr.has_chunk_ready()

        # Ready after writing enough data
        buffer_mgr.write_input(sample_audio_chunk)
        assert buffer_mgr.has_chunk_ready()

    def test_read_chunk_for_processing(self, buffer_config, sample_audio_chunk):
        """Test reading chunk for processing"""
        buffer_mgr = BufferManager(buffer_config)
        buffer_mgr.write_input(sample_audio_chunk)

        chunk, context = buffer_mgr.read_chunk_for_processing()

        assert len(chunk) == buffer_config.chunk_size
        assert context is None  # No context in Phase 1
        assert buffer_mgr.input_write_pos == 0  # Buffer shifted

    def test_context_tracking(self):
        """Test context buffer tracking (Phase 2 feature)"""
        config = BufferConfig(
            chunk_size=1024,
            context_chunks=2,  # Track 2 previous chunks
            sample_rate=48000,
            channels=1
        )
        buffer_mgr = BufferManager(config)

        # Process first chunk (no context yet)
        buffer_mgr.write_input(np.zeros(1024, dtype=np.float32))
        chunk1, context1 = buffer_mgr.read_chunk_for_processing()
        assert context1 is None

        # Process second chunk (has context from chunk1)
        buffer_mgr.write_input(np.ones(1024, dtype=np.float32))
        chunk2, context2 = buffer_mgr.read_chunk_for_processing()
        assert context2 is not None
        assert len(context2) == 1024  # 1 chunk of context

    def test_write_and_read_output(self, buffer_config):
        """Test output buffer operations"""
        buffer_mgr = BufferManager(buffer_config)

        # Write converted audio
        converted = np.random.randn(4096).astype(np.float32)
        buffer_mgr.write_output(converted)

        assert len(buffer_mgr.output_buffer) == 1

        # Read output
        output = buffer_mgr.read_output(4096)
        assert output is not None
        assert len(output) == 4096
        assert len(buffer_mgr.output_buffer) == 0

    def test_read_output_when_empty(self, buffer_config):
        """Test reading from empty output buffer"""
        buffer_mgr = BufferManager(buffer_config)

        output = buffer_mgr.read_output(4096)
        assert output is None

    def test_buffer_health(self, buffer_config, sample_audio_chunk):
        """Test buffer health metrics"""
        buffer_mgr = BufferManager(buffer_config)
        buffer_mgr.write_input(sample_audio_chunk)

        health = buffer_mgr.get_buffer_health()

        assert 'input_fill_percent' in health
        assert 'output_chunks_ready' in health
        assert 'total_latency_ms' in health
        assert health['input_fill_percent'] > 0

    def test_buffer_overflow_handling(self, buffer_config):
        """Test buffer overflow behavior"""
        buffer_mgr = BufferManager(buffer_config)

        # Fill buffer beyond capacity
        large_chunk = np.random.randn(100000).astype(np.float32)
        buffer_mgr.write_input(large_chunk)

        # Should handle gracefully by shifting
        assert buffer_mgr.input_write_pos == len(buffer_mgr.input_buffer)

    def test_clear_buffers(self, buffer_config, sample_audio_chunk):
        """Test clearing all buffers"""
        buffer_mgr = BufferManager(buffer_config)
        buffer_mgr.write_input(sample_audio_chunk)
        buffer_mgr.write_output(sample_audio_chunk)

        buffer_mgr.clear()

        assert buffer_mgr.input_write_pos == 0
        assert len(buffer_mgr.output_buffer) == 0
        assert len(buffer_mgr.context_buffer) == 0


# ConversionConfig Tests

class TestConversionConfig:
    """Test ConversionConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = ConversionConfig(model_path="test.pth")

        assert config.pitch_shift == 0
        assert config.index_rate == 0.75
        assert config.sample_rate == 48000
        assert config.use_rmvpe is True
        assert config.chunk_size == 4096

    def test_custom_values(self):
        """Test custom configuration values"""
        config = ConversionConfig(
            model_path="test.pth",
            pitch_shift=2,
            index_rate=0.5,
            chunk_size=8192
        )

        assert config.pitch_shift == 2
        assert config.index_rate == 0.5
        assert config.chunk_size == 8192


# StreamingPipeline Tests

class TestStreamingPipeline:
    """Test StreamingPipeline orchestration"""

    def test_initialization(self, mock_backend, buffer_config):
        """Test pipeline initialization"""
        pipeline = StreamingPipeline(mock_backend, buffer_config)

        assert pipeline.backend == mock_backend
        assert pipeline.buffer is not None
        assert not pipeline.running

    def test_pipeline_lifecycle(self, mock_backend, buffer_config):
        """Test pipeline start/stop"""
        pipeline = StreamingPipeline(mock_backend, buffer_config)

        # Start pipeline
        pipeline.start()
        assert pipeline.running
        assert pipeline.conversion_thread is not None
        assert pipeline.conversion_thread.is_alive()

        # Give thread time to start
        time.sleep(0.1)

        # Stop pipeline
        pipeline.stop()
        assert not pipeline.running

        # Thread should stop
        time.sleep(0.5)
        assert not pipeline.conversion_thread.is_alive()

    def test_process_input(self, mock_backend, buffer_config, sample_audio_chunk):
        """Test processing input audio"""
        pipeline = StreamingPipeline(mock_backend, buffer_config)

        pipeline.process_input(sample_audio_chunk)

        assert pipeline.buffer.total_samples_received == len(sample_audio_chunk)

    def test_get_output(self, mock_backend, buffer_config):
        """Test getting output audio"""
        pipeline = StreamingPipeline(mock_backend, buffer_config)

        # Initially no output
        output = pipeline.get_output(1024)
        assert output is None

        # After writing to output buffer
        test_audio = np.zeros(1024, dtype=np.float32)
        pipeline.buffer.write_output(test_audio)
        output = pipeline.get_output(1024)
        assert output is not None
        assert len(output) == 1024

    def test_metrics_callback(self, mock_backend, buffer_config):
        """Test metrics callback"""
        metrics_called = []

        def metrics_callback(metrics):
            metrics_called.append(metrics)

        pipeline = StreamingPipeline(mock_backend, buffer_config, on_metrics_update=metrics_callback)
        pipeline.start()

        # Feed audio to trigger processing
        for _ in range(5):
            chunk = np.random.randn(4096).astype(np.float32)
            pipeline.process_input(chunk)
            time.sleep(0.1)

        # Wait for metrics update
        time.sleep(1.0)

        pipeline.stop()

        # Should have received at least one metrics update
        assert len(metrics_called) > 0
        assert 'processing_time_ms' in metrics_called[0]
        assert 'total_latency_ms' in metrics_called[0]

    def test_get_metrics(self, mock_backend, buffer_config):
        """Test getting pipeline metrics"""
        pipeline = StreamingPipeline(mock_backend, buffer_config)
        pipeline.start()

        time.sleep(0.2)

        metrics = pipeline.get_metrics()

        assert 'uptime_seconds' in metrics
        assert 'total_latency_ms' in metrics
        assert 'backend_metrics' in metrics
        assert 'buffer_metrics' in metrics

        pipeline.stop()

    def test_is_running(self, mock_backend, buffer_config):
        """Test is_running status"""
        pipeline = StreamingPipeline(mock_backend, buffer_config)

        assert not pipeline.is_running()

        pipeline.start()
        assert pipeline.is_running()

        pipeline.stop()
        time.sleep(0.5)
        assert not pipeline.is_running()


# BatchConverter Tests

class TestBatchConverter:
    """Test BatchConverter implementation"""

    def test_initialization(self, conversion_config):
        """Test BatchConverter initialization"""
        converter = BatchConverter(conversion_config)

        assert converter.config == conversion_config
        assert converter.temp_dir is None
        assert converter.voice_converter is None

    @pytest.mark.skip(reason="Requires VoiceConverter and actual RVC models")
    def test_initialize_and_cleanup(self, conversion_config):
        """Test initialization and cleanup (requires real models)"""
        converter = BatchConverter(conversion_config)

        # Initialize
        converter.initialize()
        assert converter.temp_dir is not None
        assert Path(converter.temp_dir).exists()
        assert converter.voice_converter is not None

        # Cleanup
        converter.cleanup()
        assert not Path(converter.temp_dir).exists()
        assert converter.voice_converter is None

    def test_latency_estimate(self, conversion_config):
        """Test latency estimation"""
        converter = BatchConverter(conversion_config)

        # Default estimate (no measured latency)
        estimate = converter.get_latency_estimate_ms()
        assert estimate > 0

        # Should be in expected range for Phase 1
        assert 400 <= estimate <= 1000

    @pytest.mark.skip(reason="Requires VoiceConverter and actual RVC models")
    def test_convert_chunk_integration(self, conversion_config, sample_audio_chunk):
        """Test chunk conversion (requires real models)"""
        converter = BatchConverter(conversion_config)
        converter.initialize()

        try:
            converted = converter.convert_chunk(sample_audio_chunk)

            # Should return same length
            assert len(converted) == len(sample_audio_chunk)
            # Metrics should be updated
            assert converter.metrics.total_chunks_processed == 1
            assert converter.metrics.processing_time_ms > 0
        finally:
            converter.cleanup()

    def test_metrics_tracking(self, conversion_config):
        """Test metrics tracking"""
        converter = BatchConverter(conversion_config)

        assert converter.metrics.total_chunks_processed == 0
        assert converter.metrics.dropped_chunks == 0
        assert converter.metrics.processing_time_ms == 0.0


# Integration Tests

@pytest.mark.skip(reason="Requires VoiceConverter and actual RVC models")
class TestStreamingIntegration:
    """Integration tests for complete streaming pipeline"""

    def test_end_to_end_conversion(self, conversion_config, buffer_config):
        """Test complete conversion pipeline"""
        backend = BatchConverter(conversion_config)
        pipeline = StreamingPipeline(backend, buffer_config)

        pipeline.start()

        try:
            # Feed several chunks of audio
            for _ in range(10):
                chunk = np.random.randn(1024).astype(np.float32)
                pipeline.process_input(chunk)
                time.sleep(0.05)

            # Wait for processing
            time.sleep(2.0)

            # Should have output available
            output = pipeline.get_output(1024)
            assert output is not None

            # Check metrics
            metrics = pipeline.get_metrics()
            assert metrics['backend_metrics']['chunks_processed'] > 0

        finally:
            pipeline.stop()

    def test_continuous_streaming(self, conversion_config, buffer_config):
        """Test continuous streaming for longer duration"""
        backend = BatchConverter(conversion_config)
        pipeline = StreamingPipeline(backend, buffer_config)

        pipeline.start()
        outputs_received = 0

        try:
            # Simulate 5 seconds of streaming
            duration_seconds = 5
            chunks_per_second = 48000 // 1024

            for _ in range(duration_seconds * chunks_per_second):
                # Input
                chunk = np.random.randn(1024).astype(np.float32)
                pipeline.process_input(chunk)

                # Output
                output = pipeline.get_output(1024)
                if output is not None:
                    outputs_received += 1

                time.sleep(1.0 / chunks_per_second)

            # Should have received some output
            assert outputs_received > 0

        finally:
            pipeline.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
