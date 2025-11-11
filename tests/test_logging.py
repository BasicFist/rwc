"""Tests for logging configuration"""
import pytest
import logging
import os
from pathlib import Path
from rwc.utils.logging_config import (
    setup_logging,
    get_logger,
    log_function_call,
    log_performance,
    log_error_with_context,
    LOG_LEVELS,
)


class TestLoggingSetup:
    """Test logging setup and configuration"""

    def test_setup_logging_default(self):
        """Should create logger with default settings"""
        logger = setup_logging('test_logger')
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_with_level(self):
        """Should respect log level parameter"""
        logger = setup_logging('test_logger_debug', level='DEBUG')
        assert logger.level == logging.DEBUG

        logger = setup_logging('test_logger_error', level='ERROR')
        assert logger.level == logging.ERROR

    def test_setup_logging_all_levels(self):
        """Should support all log levels"""
        for level_name, level_value in LOG_LEVELS.items():
            logger = setup_logging(f'test_{level_name.lower()}', level=level_name)
            assert logger.level == level_value

    def test_setup_logging_with_file(self, temp_dir):
        """Should create file handler when log_file specified"""
        log_file = temp_dir / "test.log"
        logger = setup_logging('test_file_logger', log_file=str(log_file))

        # Write a log message
        logger.info("Test message")

        # Check file was created and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_no_propagation(self):
        """Should not propagate to root logger"""
        logger = setup_logging('test_no_prop')
        assert logger.propagate is False

    def test_setup_logging_console_off(self):
        """Should work with console logging disabled"""
        logger = setup_logging('test_no_console', console=False)
        assert logger.name == 'test_no_console'
        # Should have no console handlers
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        # May have file handlers, but no console handlers
        assert all(not hasattr(h, 'stream') or h.stream.name != '<stdout>' for h in console_handlers)

    def test_setup_logging_removes_duplicates(self):
        """Should remove existing handlers to avoid duplicates"""
        logger = setup_logging('test_dup')
        initial_count = len(logger.handlers)

        # Setup again
        logger = setup_logging('test_dup')
        final_count = len(logger.handlers)

        # Should not have duplicate handlers
        assert final_count == initial_count


class TestGetLogger:
    """Test get_logger functionality"""

    def test_get_logger_creates_new(self):
        """Should create new logger if doesn't exist"""
        logger = get_logger('test_new_logger')
        assert logger.name == 'test_new_logger'
        assert len(logger.handlers) > 0

    def test_get_logger_reuses_existing(self):
        """Should reuse existing logger"""
        logger1 = get_logger('test_reuse_logger')
        logger2 = get_logger('test_reuse_logger')
        assert logger1 is logger2

    def test_get_logger_hierarchical(self):
        """Should work with hierarchical logger names"""
        logger = get_logger('rwc.core.converter')
        assert logger.name == 'rwc.core.converter'


class TestLoggingHelpers:
    """Test helper functions"""

    def test_log_function_call(self, caplog):
        """Should log function calls with parameters"""
        logger = setup_logging('test_func_call', level='DEBUG', propagate=True)

        with caplog.at_level(logging.DEBUG, logger='test_func_call'):
            log_function_call(logger, 'test_function', param1='value1', param2=42)

        assert 'test_function' in caplog.text
        assert 'param1=value1' in caplog.text
        assert 'param2=42' in caplog.text

    def test_log_performance(self, caplog):
        """Should log performance metrics"""
        logger = setup_logging('test_perf', level='INFO', propagate=True)

        with caplog.at_level(logging.INFO, logger='test_perf'):
            log_performance(logger, 'test_operation', 1.234)

        assert 'Performance' in caplog.text
        assert 'test_operation' in caplog.text
        assert '1.23' in caplog.text  # Formatted to 2 decimal places

    def test_log_error_with_context(self, caplog):
        """Should log errors with context and stack trace"""
        logger = setup_logging('test_error', level='ERROR', propagate=True)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            with caplog.at_level(logging.ERROR, logger='test_error'):
                log_error_with_context(logger, e, "During test operation")

        assert 'During test operation' in caplog.text
        assert 'ValueError' in caplog.text
        assert 'Test error' in caplog.text


class TestEnvironmentVariables:
    """Test environment variable integration"""

    def test_log_level_from_env(self, monkeypatch):
        """Should read log level from RWC_LOG_LEVEL environment variable"""
        monkeypatch.setenv('RWC_LOG_LEVEL', 'DEBUG')
        logger = setup_logging('test_env_level')
        assert logger.level == logging.DEBUG

        monkeypatch.setenv('RWC_LOG_LEVEL', 'WARNING')
        logger = setup_logging('test_env_level2')
        assert logger.level == logging.WARNING

    def test_log_level_invalid_env(self, monkeypatch):
        """Should fallback to INFO for invalid log level"""
        monkeypatch.setenv('RWC_LOG_LEVEL', 'INVALID')
        logger = setup_logging('test_invalid_env')
        assert logger.level == logging.INFO


class TestLogFormatting:
    """Test log message formatting"""

    def test_file_format_detailed(self, temp_dir):
        """File logs should have detailed format"""
        log_file = temp_dir / "detailed.log"
        logger = setup_logging('test_detailed', log_file=str(log_file))

        logger.info("Test message")

        content = log_file.read_text()
        # Should include timestamp, logger name, level, function, line number
        assert 'test_detailed' in content
        assert 'INFO' in content
        assert 'Test message' in content

    def test_console_format_simple(self, caplog):
        """Console logs should have simple format"""
        logger = setup_logging('test_console', level='INFO', propagate=True)

        with caplog.at_level(logging.INFO, logger='test_console'):
            logger.info("Test message")

        # Simple format: timestamp - level - message
        assert 'INFO' in caplog.text
        assert 'Test message' in caplog.text


class TestLoggerIsolation:
    """Test logger isolation"""

    def test_loggers_isolated(self):
        """Different loggers should be isolated"""
        logger1 = setup_logging('logger1', level='DEBUG')
        logger2 = setup_logging('logger2', level='ERROR')

        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.ERROR
        assert logger1 is not logger2

    def test_no_root_pollution(self):
        """Should not pollute root logger"""
        root_logger = logging.getLogger()
        initial_handlers = len(root_logger.handlers)

        logger = setup_logging('test_no_pollution')
        logger.info("Test message")

        final_handlers = len(root_logger.handlers)
        assert final_handlers == initial_handlers
