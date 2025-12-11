"""
Refactored JargonTranslator with improved robustness and structure.

Real-time transcription and jargon translation tool.
"""

import argparse
import logging
import sys
from typing import Optional

import pyaudio
import numpy as np
from faster_whisper import WhisperModel

from src.config import (
    ConfigurationError,
    get_api_config,
    get_audio_config,
    get_whisper_config,
    AudioConfig,
    WhisperConfig,
)
from src.api_client import JamAIClient, APIError, create_client
from src.audio import (
    select_audio_device,
    is_silent,
    normalize_audio,
    print_available_devices,
)
from src.utils import split_output_to_notifications, show_notification


# Configure logging
def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


logger = logging.getLogger(__name__)


class JargonTranslator:
    """
    Main application class for real-time jargon translation.
    
    Captures system audio, transcribes it using Whisper,
    sends to JamAI for jargon explanation, and displays notifications.
    """
    
    def __init__(
        self,
        audio_config: AudioConfig,
        whisper_config: WhisperConfig,
        api_client: JamAIClient,
    ):
        """
        Initialize the JargonTranslator.
        
        Args:
            audio_config: Audio capture configuration.
            whisper_config: Whisper model configuration.
            api_client: Configured JamAI API client.
        """
        self.audio_config = audio_config
        self.whisper_config = whisper_config
        self.api_client = api_client
        self.model: Optional[WhisperModel] = None
        self.pyaudio: Optional[pyaudio.PyAudio] = None
        self.stream = None
    
    def _load_model(self) -> None:
        """Load the Whisper model."""
        logger.info(f"Loading Whisper model ({self.whisper_config.model_size})...")
        self.model = WhisperModel(
            self.whisper_config.model_size,
            device=self.whisper_config.device,
        )
        logger.info("Model loaded successfully.")
    
    def _setup_audio_stream(self) -> None:
        """Initialize PyAudio and open the audio stream."""
        self.pyaudio = pyaudio.PyAudio()
        
        device_index = select_audio_device(self.audio_config.device_index)
        logger.info(f"Using audio device index: {device_index}")
        
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.audio_config.channels,
            rate=self.audio_config.sample_rate,
            input=True,
            frames_per_buffer=self.audio_config.chunk_size,
            input_device_index=device_index,
        )
    
    def _process_transcription(self, transcription: str) -> None:
        """
        Process a transcription through the API and show notifications.
        
        Args:
            transcription: The transcribed text.
        """
        try:
            api_response = self.api_client.send_transcription(transcription)
            logger.debug(f"API Response: {api_response}")
            
            if api_response.strip():
                notifications = split_output_to_notifications(api_response)
                
                for title, description in notifications:
                    logger.info(f"Notification: {title}")
                    show_notification(title, description)
            else:
                logger.debug("Empty API response, no jargon detected.")
                
        except APIError as e:
            logger.error(f"API Error: {e}")
    
    def run(self) -> None:
        """
        Main loop for live transcription and translation.
        
        Captures audio, transcribes, sends to API, and displays notifications.
        """
        self._load_model()
        self._setup_audio_stream()
        
        logger.info("Live transcription started. Press Ctrl+C to stop.")
        
        audio_buffer = b""
        buffer_size = (
            self.audio_config.sample_rate *
            self.audio_config.channels *
            self.audio_config.buffer_duration * 2  # 2 bytes per sample (int16)
        )
        
        try:
            while True:
                # Read audio chunk
                audio_data = self.stream.read(
                    self.audio_config.chunk_size,
                    exception_on_overflow=False,
                )
                audio_buffer += audio_data
                
                # Process when buffer is full
                if len(audio_buffer) >= buffer_size:
                    # Normalize audio
                    audio_np = normalize_audio(audio_buffer)
                    
                    # Check for silence
                    if is_silent(audio_np, self.audio_config.silence_threshold):
                        logger.debug("Silence detected, skipping transcription.")
                        audio_buffer = b""
                        continue
                    
                    # Transcribe
                    segments, _ = self.model.transcribe(
                        audio_np,
                        beam_size=self.whisper_config.beam_size,
                    )
                    transcription = " ".join(seg.text for seg in segments).strip()
                    
                    if transcription and transcription not in (".", ""):
                        logger.info(f"Transcription: {transcription}")
                        self._process_transcription(transcription)
                    else:
                        logger.debug("Empty transcription, skipping.")
                    
                    # Clear buffer
                    audio_buffer = b""
                    
        except KeyboardInterrupt:
            logger.info("Transcription stopped by user.")
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.pyaudio:
            self.pyaudio.terminate()
        logger.info("Resources cleaned up.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="JargonTranslator - Real-time jargon translation tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "--device", "-d",
        type=int,
        default=None,
        help="Audio device index. Use --list-devices to see available devices.",
    )
    
    parser.add_argument(
        "--list-devices", "-l",
        action="store_true",
        help="List available audio devices and exit.",
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="tiny",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size.",
    )
    
    parser.add_argument(
        "--buffer", "-b",
        type=int,
        default=10,
        help="Buffer duration in seconds.",
    )
    
    parser.add_argument(
        "--silence-threshold", "-s",
        type=float,
        default=500.0,
        help="RMS threshold for silence detection.",
    )
    
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU (CUDA) for Whisper model.",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging.",
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Handle --list-devices
    if args.list_devices:
        print_available_devices()
        return
    
    try:
        # Load configurations
        api_config = get_api_config()
        
        audio_config = get_audio_config(device_index=args.device)
        audio_config.buffer_duration = args.buffer
        audio_config.silence_threshold = args.silence_threshold
        
        whisper_config = get_whisper_config(
            model_size=args.model,
            device="cuda" if args.gpu else "cpu",
        )
        
        # Create API client
        api_client = create_client(api_config)
        
        # Run the translator
        translator = JargonTranslator(
            audio_config=audio_config,
            whisper_config=whisper_config,
            api_client=api_client,
        )
        translator.run()
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
