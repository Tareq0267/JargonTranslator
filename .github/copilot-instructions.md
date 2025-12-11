# JargonTranslator - AI Development Notes

## Project Overview
JargonTranslator is a real-time audio transcription tool that captures system audio, transcribes it using Whisper, sends the text to JamAI API for jargon explanation, and displays results as desktop notifications.

## Architecture
```
Audio Input (PyAudio) → Whisper Transcription → JamAI API → Desktop Notifications
```

## Key Modules
- `src/config.py` - Configuration management with environment validation
- `src/audio.py` - Audio capture, device discovery, silence detection
- `src/api_client.py` - JamAI API client with retry logic
- `src/utils.py` - Shared notification utilities
- `JargonTranslator_v2.py` - Main application entry point

## Coding Standards
- Use type hints for all functions
- Add docstrings with Args, Returns, Raises sections
- Use Python's `logging` module, not `print()`
- Write unit tests for new functionality in `tests/`
- Keep functions small and single-purpose

## API Integration
- JamAI Base API: https://api.jamaibase.com
- Authentication: Bearer token + Project ID header
- Always implement retry logic with exponential backoff
- Handle rate limiting gracefully

## Audio Processing
- Sample rate: 16kHz (Whisper optimal)
- Format: 16-bit mono
- Buffer duration: 10 seconds default
- Use RMS-based silence detection before processing

## Environment Variables Required
- `PROJECT_ID` - JamAI project identifier
- `API_KEY` - JamAI API key
- `TABLE_ID` - JamAI table identifier

## Testing
- Run tests: `pytest tests/ -v`
- All new code should have corresponding tests
- Use mocks for external API calls and PyAudio

### IMPORTANT: Comprehensive Testing Requirements
- **Always create comprehensive pytest tests** for any new feature or functionality
- **When fixing bugs or repeating issues**, add regression tests to prevent recurrence
- Tests should cover:
  - Happy path (normal operation)
  - Edge cases (empty inputs, boundary values)
  - Error handling (exceptions, invalid inputs)
  - Mock external dependencies (API calls, audio devices)
- Use pytest fixtures for common test data
- Test classes should be organized by module (e.g., `TestClassName` for each class)
- Aim for high code coverage on new code

## Common Patterns
```python
# Configuration loading
from src.config import get_api_config, ConfigurationError

# API calls
from src.api_client import create_client, APIError

# Notifications
from src.utils import split_output_to_notifications, show_notification
```

## Known Limitations
- Single-threaded (API calls block audio capture)
- Notification parsing relies on specific JamAI output format
- Windows Stereo Mix required for system audio capture
