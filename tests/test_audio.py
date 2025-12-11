"""
Unit tests for src/audio.py
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.audio import (
    list_audio_devices,
    find_loopback_device,
    select_audio_device,
    is_silent,
    normalize_audio,
    INT16_MAX,
)


class TestIsSilent:
    """Test is_silent function."""
    
    def test_silent_audio(self):
        """Test that very low amplitude audio is detected as silent."""
        # Create near-zero amplitude audio
        silent_audio = np.zeros(1000, dtype=np.float32)
        assert is_silent(silent_audio) == True
    
    def test_loud_audio(self):
        """Test that loud audio is not detected as silent."""
        # Create loud audio (sine wave)
        loud_audio = np.sin(np.linspace(0, 10 * np.pi, 1000)).astype(np.float32) * 10000
        assert is_silent(loud_audio) == False
    
    def test_custom_threshold(self):
        """Test with custom silence threshold."""
        # Audio with RMS around 100
        audio = np.ones(1000, dtype=np.float32) * 100

        # Should be silent with high threshold
        assert is_silent(audio, threshold=200) == True
        
        # Should not be silent with low threshold
        assert is_silent(audio, threshold=50) == False
    
    def test_threshold_boundary(self):
        """Test behavior at threshold boundary."""
        # Create audio with known RMS
        rms_value = 500.0
        audio = np.ones(1000, dtype=np.float32) * rms_value

        # Exactly at threshold - should be silent (< comparison)
        assert is_silent(audio, threshold=rms_value) == False
        assert is_silent(audio, threshold=rms_value + 1) == True
    
    def test_negative_values(self):
        """Test that negative values are handled correctly."""
        # Negative values should contribute to RMS
        audio = np.ones(1000, dtype=np.float32) * -1000
        assert is_silent(audio) == False
    
    def test_empty_array(self):
        """Test with empty array (edge case)."""
        empty_audio = np.array([], dtype=np.float32)
        # np.mean of empty array returns nan, sqrt(nan) is nan
        # nan < threshold is False
        result = is_silent(empty_audio)
        # Result will be False due to NaN comparison
        assert result == False
class TestNormalizeAudio:
    """Test normalize_audio function."""
    
    def test_max_positive_value(self):
        """Test that max int16 normalizes to ~1.0."""
        # Max int16 value
        audio_bytes = np.array([32767], dtype=np.int16).tobytes()
        normalized = normalize_audio(audio_bytes)
        assert normalized[0] == pytest.approx(1.0, abs=0.0001)
    
    def test_max_negative_value(self):
        """Test that min int16 normalizes to ~-1.0."""
        audio_bytes = np.array([-32768], dtype=np.int16).tobytes()
        normalized = normalize_audio(audio_bytes)
        assert normalized[0] == pytest.approx(-1.0, abs=0.0001)
    
    def test_zero_value(self):
        """Test that zero normalizes to zero."""
        audio_bytes = np.array([0], dtype=np.int16).tobytes()
        normalized = normalize_audio(audio_bytes)
        assert normalized[0] == 0.0
    
    def test_output_dtype(self):
        """Test that output is float32."""
        audio_bytes = np.array([1000, 2000, 3000], dtype=np.int16).tobytes()
        normalized = normalize_audio(audio_bytes)
        assert normalized.dtype == np.float32
    
    def test_preserves_length(self):
        """Test that output has same length as input samples."""
        samples = [100, 200, 300, 400, 500]
        audio_bytes = np.array(samples, dtype=np.int16).tobytes()
        normalized = normalize_audio(audio_bytes)
        assert len(normalized) == len(samples)
    
    def test_normalization_range(self):
        """Test that all values are in [-1.0, 1.0] range."""
        # Random int16 values
        np.random.seed(42)
        random_samples = np.random.randint(-32768, 32768, 1000, dtype=np.int16)
        audio_bytes = random_samples.tobytes()
        
        normalized = normalize_audio(audio_bytes)
        
        assert np.all(normalized >= -1.0)
        assert np.all(normalized <= 1.0)


class TestListAudioDevices:
    """Test list_audio_devices function."""
    
    @patch('src.audio.pyaudio.PyAudio')
    def test_returns_input_devices_only(self, mock_pyaudio_class):
        """Test that only input devices are returned."""
        mock_pa = MagicMock()
        mock_pyaudio_class.return_value = mock_pa
        
        # Setup mock devices
        mock_pa.get_device_count.return_value = 3
        mock_pa.get_device_info_by_index.side_effect = [
            {'name': 'Output Only', 'maxInputChannels': 0, 'defaultSampleRate': 44100},
            {'name': 'Input Device', 'maxInputChannels': 2, 'defaultSampleRate': 48000},
            {'name': 'Stereo Mix', 'maxInputChannels': 2, 'defaultSampleRate': 44100},
        ]
        
        devices = list_audio_devices()
        
        assert len(devices) == 2
        assert devices[0]['name'] == 'Input Device'
        assert devices[1]['name'] == 'Stereo Mix'
    
    @patch('src.audio.pyaudio.PyAudio')
    def test_terminates_pyaudio(self, mock_pyaudio_class):
        """Test that PyAudio is properly terminated."""
        mock_pa = MagicMock()
        mock_pyaudio_class.return_value = mock_pa
        mock_pa.get_device_count.return_value = 0
        
        list_audio_devices()
        
        mock_pa.terminate.assert_called_once()
    
    @patch('src.audio.pyaudio.PyAudio')
    def test_empty_when_no_devices(self, mock_pyaudio_class):
        """Test empty list when no devices available."""
        mock_pa = MagicMock()
        mock_pyaudio_class.return_value = mock_pa
        mock_pa.get_device_count.return_value = 0
        
        devices = list_audio_devices()
        
        assert devices == []


class TestFindLoopbackDevice:
    """Test find_loopback_device function."""
    
    @patch('src.audio.list_audio_devices')
    def test_finds_stereo_mix(self, mock_list):
        """Test finding Stereo Mix device."""
        mock_list.return_value = [
            {'index': 0, 'name': 'Microphone'},
            {'index': 1, 'name': 'Stereo Mix'},
        ]
        
        result = find_loopback_device()
        
        assert result == 1
    
    @patch('src.audio.list_audio_devices')
    def test_finds_loopback(self, mock_list):
        """Test finding device with 'loopback' in name."""
        mock_list.return_value = [
            {'index': 0, 'name': 'Microphone'},
            {'index': 2, 'name': 'WASAPI Loopback'},
        ]
        
        result = find_loopback_device()
        
        assert result == 2
    
    @patch('src.audio.list_audio_devices')
    def test_returns_none_when_not_found(self, mock_list):
        """Test None returned when no loopback device found."""
        mock_list.return_value = [
            {'index': 0, 'name': 'Microphone'},
            {'index': 1, 'name': 'Line In'},
        ]
        
        result = find_loopback_device()
        
        assert result is None
    
    @patch('src.audio.list_audio_devices')
    def test_case_insensitive(self, mock_list):
        """Test that search is case insensitive."""
        mock_list.return_value = [
            {'index': 0, 'name': 'STEREO MIX (Realtek)'},
        ]
        
        result = find_loopback_device()
        
        assert result == 0


class TestSelectAudioDevice:
    """Test select_audio_device function."""
    
    @patch('src.audio.list_audio_devices')
    def test_validates_provided_index(self, mock_list):
        """Test that provided index is validated."""
        mock_list.return_value = [
            {'index': 0, 'name': 'Device 0'},
            {'index': 2, 'name': 'Device 2'},
        ]
        
        result = select_audio_device(device_index=2)
        
        assert result == 2
    
    @patch('src.audio.list_audio_devices')
    def test_raises_on_invalid_index(self, mock_list):
        """Test ValueError raised for invalid index."""
        mock_list.return_value = [
            {'index': 0, 'name': 'Device 0'},
        ]
        
        with pytest.raises(ValueError) as exc_info:
            select_audio_device(device_index=5)
        
        assert "Invalid device index" in str(exc_info.value)
    
    @patch('src.audio.find_loopback_device')
    def test_auto_detects_when_none_provided(self, mock_find):
        """Test auto-detection when no index provided."""
        mock_find.return_value = 3
        
        result = select_audio_device(device_index=None)
        
        assert result == 3
    
    @patch('src.audio.find_loopback_device')
    @patch('src.audio.list_audio_devices')
    def test_falls_back_to_first_device(self, mock_list, mock_find):
        """Test fallback to first device when no loopback found."""
        mock_find.return_value = None
        mock_list.return_value = [
            {'index': 1, 'name': 'Microphone'},
        ]
        
        result = select_audio_device(device_index=None)
        
        assert result == 1
    
    @patch('src.audio.find_loopback_device')
    @patch('src.audio.list_audio_devices')
    def test_raises_when_no_devices(self, mock_list, mock_find):
        """Test ValueError when no devices available."""
        mock_find.return_value = None
        mock_list.return_value = []
        
        with pytest.raises(ValueError) as exc_info:
            select_audio_device(device_index=None)
        
        assert "No audio input devices found" in str(exc_info.value)


class TestInt16MaxConstant:
    """Test INT16_MAX constant."""
    
    def test_value(self):
        """Test that constant has correct value."""
        assert INT16_MAX == 32768.0
    
    def test_is_float(self):
        """Test that constant is a float (for division)."""
        assert isinstance(INT16_MAX, float)
