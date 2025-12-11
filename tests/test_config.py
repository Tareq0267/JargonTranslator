"""
Unit tests for src/config.py
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from src.config import (
    ConfigurationError,
    AudioConfig,
    APIConfig,
    WhisperConfig,
    validate_env_vars,
    get_api_config,
    get_audio_config,
    get_whisper_config,
)


class TestAudioConfig:
    """Test AudioConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = AudioConfig()
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.chunk_size == 1024
        assert config.buffer_duration == 10
        assert config.device_index is None
        assert config.silence_threshold == 500.0
    
    def test_custom_values(self):
        """Test creating config with custom values."""
        config = AudioConfig(
            sample_rate=44100,
            channels=2,
            device_index=5,
        )
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.device_index == 5


class TestAPIConfig:
    """Test APIConfig dataclass."""
    
    def test_required_fields(self):
        """Test that required fields must be provided."""
        config = APIConfig(
            project_id="test_project",
            api_key="test_key",
            table_id="test_table",
        )
        assert config.project_id == "test_project"
        assert config.api_key == "test_key"
        assert config.table_id == "test_table"
    
    def test_default_optional_values(self):
        """Test default values for optional fields."""
        config = APIConfig(
            project_id="p",
            api_key="k",
            table_id="t",
        )
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout == 30
        assert "jamaibase.com" in config.base_url


class TestWhisperConfig:
    """Test WhisperConfig dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        config = WhisperConfig()
        assert config.model_size == "tiny"
        assert config.device == "cpu"
        assert config.beam_size == 1
    
    def test_gpu_config(self):
        """Test GPU configuration."""
        config = WhisperConfig(device="cuda")
        assert config.device == "cuda"


class TestValidateEnvVars:
    """Test validate_env_vars function."""
    
    @patch.dict(os.environ, {
        "PROJECT_ID": "test_project",
        "API_KEY": "test_key",
        "TABLE_ID": "test_table",
    })
    def test_valid_env_vars(self):
        """Test that validation passes with all vars set."""
        # Should not raise
        validate_env_vars()
    
    @patch.dict(os.environ, {
        "PROJECT_ID": "test",
        "API_KEY": "test",
    }, clear=True)
    def test_missing_table_id(self):
        """Test that missing TABLE_ID raises error."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_env_vars()
        assert "TABLE_ID" in str(exc_info.value)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_all_vars_missing(self):
        """Test that all missing vars are listed in error."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_env_vars()
        error_msg = str(exc_info.value)
        assert "PROJECT_ID" in error_msg
        assert "API_KEY" in error_msg
        assert "TABLE_ID" in error_msg
    
    @patch.dict(os.environ, {
        "PROJECT_ID": "",
        "API_KEY": "test",
        "TABLE_ID": "test",
    }, clear=True)
    def test_empty_string_treated_as_missing(self):
        """Test that empty string is treated as missing."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_env_vars()
        assert "PROJECT_ID" in str(exc_info.value)


class TestGetApiConfig:
    """Test get_api_config function."""
    
    @patch.dict(os.environ, {
        "PROJECT_ID": "my_project",
        "API_KEY": "my_key",
        "TABLE_ID": "my_table",
    })
    def test_loads_from_environment(self):
        """Test that config is loaded from environment."""
        config = get_api_config()
        assert config.project_id == "my_project"
        assert config.api_key == "my_key"
        assert config.table_id == "my_table"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_raises_on_missing_vars(self):
        """Test that missing vars raise ConfigurationError."""
        with pytest.raises(ConfigurationError):
            get_api_config()


class TestGetAudioConfig:
    """Test get_audio_config function."""
    
    def test_default_config(self):
        """Test default audio config."""
        config = get_audio_config()
        assert config.device_index is None
    
    def test_with_device_override(self):
        """Test config with device index override."""
        config = get_audio_config(device_index=3)
        assert config.device_index == 3


class TestGetWhisperConfig:
    """Test get_whisper_config function."""
    
    def test_default_config(self):
        """Test default whisper config."""
        config = get_whisper_config()
        assert config.model_size == "tiny"
        assert config.device == "cpu"
    
    def test_custom_model_size(self):
        """Test custom model size."""
        config = get_whisper_config(model_size="large")
        assert config.model_size == "large"
    
    def test_invalid_model_size_falls_back(self):
        """Test that invalid model size falls back to tiny."""
        config = get_whisper_config(model_size="invalid")
        assert config.model_size == "tiny"
    
    def test_cuda_device(self):
        """Test CUDA device selection."""
        config = get_whisper_config(device="cuda")
        assert config.device == "cuda"
