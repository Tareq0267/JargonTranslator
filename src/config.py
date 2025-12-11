"""
Configuration management for JargonTranslator.
Handles environment variables, validation, and default settings.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


@dataclass
class AudioConfig:
    """Audio recording configuration."""
    sample_rate: int = 16000  # Whisper works well with 16kHz
    channels: int = 1  # Mono audio
    chunk_size: int = 1024  # Frames per buffer
    buffer_duration: int = 10  # Process every N seconds
    device_index: Optional[int] = None  # None = auto-detect
    silence_threshold: float = 500.0  # RMS threshold for silence detection


@dataclass
class APIConfig:
    """JamAI API configuration."""
    project_id: str
    api_key: str
    table_id: str
    base_url: str = "https://api.jamaibase.com/api/v1/gen_tables/action/rows/add"
    max_retries: int = 3
    retry_delay: float = 1.0  # Base delay in seconds for exponential backoff
    timeout: int = 30  # Request timeout in seconds


@dataclass
class WhisperConfig:
    """Whisper model configuration."""
    model_size: str = "tiny"  # tiny, base, small, medium, large
    device: str = "cpu"  # cpu or cuda
    beam_size: int = 1  # Lower = faster


def validate_env_vars() -> None:
    """
    Validate that all required environment variables are set.
    
    Raises:
        ConfigurationError: If any required variable is missing.
    """
    required_vars = ["PROJECT_ID", "API_KEY", "TABLE_ID"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please check your .env file."
        )


def get_api_config() -> APIConfig:
    """
    Load and validate API configuration from environment.
    
    Returns:
        APIConfig instance with loaded values.
        
    Raises:
        ConfigurationError: If required variables are missing.
    """
    validate_env_vars()
    
    return APIConfig(
        project_id=os.getenv("PROJECT_ID"),
        api_key=os.getenv("API_KEY"),
        table_id=os.getenv("TABLE_ID"),
    )


def get_audio_config(device_index: Optional[int] = None) -> AudioConfig:
    """
    Get audio configuration with optional device override.
    
    Args:
        device_index: Override for audio device index.
        
    Returns:
        AudioConfig instance.
    """
    return AudioConfig(device_index=device_index)


def get_whisper_config(
    model_size: str = "tiny",
    device: str = "cpu"
) -> WhisperConfig:
    """
    Get Whisper model configuration.
    
    Args:
        model_size: Model size (tiny, base, small, medium, large).
        device: Compute device (cpu or cuda).
        
    Returns:
        WhisperConfig instance.
    """
    valid_sizes = ["tiny", "base", "small", "medium", "large"]
    if model_size not in valid_sizes:
        logger.warning(
            f"Invalid model size '{model_size}'. Using 'tiny'. "
            f"Valid options: {valid_sizes}"
        )
        model_size = "tiny"
    
    return WhisperConfig(model_size=model_size, device=device)
