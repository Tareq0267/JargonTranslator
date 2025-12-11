"""
Audio capture and processing utilities.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import pyaudio
import numpy as np

logger = logging.getLogger(__name__)

# Constant for audio normalization
INT16_MAX = 32768.0  # Maximum value for 16-bit signed integer audio


def list_audio_devices() -> List[Dict[str, Any]]:
    """
    List all available audio input devices.
    
    Returns:
        List of dictionaries containing device info with keys:
        - index: Device index
        - name: Device name
        - max_input_channels: Number of input channels
        - default_sample_rate: Default sample rate
    """
    devices = []
    p = pyaudio.PyAudio()
    
    try:
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:  # Only input devices
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'max_input_channels': info['maxInputChannels'],
                    'default_sample_rate': info['defaultSampleRate'],
                })
    finally:
        p.terminate()
    
    return devices


def find_loopback_device() -> Optional[int]:
    """
    Automatically find a loopback/stereo mix device.
    
    Returns:
        Device index if found, None otherwise.
    """
    devices = list_audio_devices()
    
    # Common loopback device names
    loopback_keywords = [
        'stereo mix', 'loopback', 'what u hear', 
        'wave out', 'system audio', 'wasapi'
    ]
    
    for device in devices:
        name_lower = device['name'].lower()
        for keyword in loopback_keywords:
            if keyword in name_lower:
                logger.info(f"Found loopback device: {device['name']} (index {device['index']})")
                return device['index']
    
    logger.warning("No loopback device found automatically. Please specify device index.")
    return None


def select_audio_device(device_index: Optional[int] = None) -> int:
    """
    Select an audio device, with auto-detection fallback.
    
    Args:
        device_index: Explicit device index, or None for auto-detect.
        
    Returns:
        Selected device index.
        
    Raises:
        ValueError: If no valid device can be found.
    """
    if device_index is not None:
        # Validate the provided index
        devices = list_audio_devices()
        valid_indices = [d['index'] for d in devices]
        
        if device_index in valid_indices:
            return device_index
        else:
            raise ValueError(
                f"Invalid device index {device_index}. "
                f"Valid indices: {valid_indices}"
            )
    
    # Try auto-detection
    auto_device = find_loopback_device()
    if auto_device is not None:
        return auto_device
    
    # Fall back to first available input device
    devices = list_audio_devices()
    if devices:
        logger.warning(f"Using first available device: {devices[0]['name']}")
        return devices[0]['index']
    
    raise ValueError("No audio input devices found.")


def is_silent(audio_data: np.ndarray, threshold: float = 500.0) -> bool:
    """
    Check if audio data is silent based on RMS threshold.
    
    Args:
        audio_data: NumPy array of audio samples.
        threshold: RMS threshold below which audio is considered silent.
        
    Returns:
        True if the audio is silent, False otherwise.
    """
    # Calculate RMS (Root Mean Square)
    rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float64))))
    return rms < threshold


def normalize_audio(audio_buffer: bytes) -> np.ndarray:
    """
    Convert raw audio bytes to normalized float32 array.
    
    Args:
        audio_buffer: Raw audio bytes (int16 format).
        
    Returns:
        Normalized float32 NumPy array with values in [-1.0, 1.0].
    """
    audio_np = np.frombuffer(audio_buffer, dtype=np.int16)
    return audio_np.astype(np.float32) / INT16_MAX


def print_available_devices() -> None:
    """Print all available audio devices to console."""
    devices = list_audio_devices()
    
    if not devices:
        print("No audio input devices found.")
        return
    
    print("\nAvailable Audio Input Devices:")
    print("-" * 60)
    for device in devices:
        print(f"  Index {device['index']}: {device['name']}")
        print(f"    Channels: {device['max_input_channels']}, "
              f"Sample Rate: {device['default_sample_rate']}")
    print("-" * 60)
