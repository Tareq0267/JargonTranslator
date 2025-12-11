"""
Unit tests for src/utils.py
"""

import pytest
from unittest.mock import patch, MagicMock
from src.utils import split_output_to_notifications, show_notification


class TestSplitOutputToNotifications:
    """Test cases for split_output_to_notifications function."""
    
    def test_basic_title_description_pair(self):
        """Test parsing a single title-description pair."""
        output = "AI:\nArtificial Intelligence"
        result = split_output_to_notifications(output)
        assert result == [("AI", "Artificial Intelligence")]
    
    def test_multiple_pairs(self):
        """Test parsing multiple title-description pairs."""
        output = """Machine Learning:
A type of AI that learns from data
Neural Network:
Computing system inspired by the brain"""
        result = split_output_to_notifications(output)
        assert result == [
            ("Machine Learning", "A type of AI that learns from data"),
            ("Neural Network", "Computing system inspired by the brain"),
        ]
    
    def test_empty_input(self):
        """Test with empty string input."""
        result = split_output_to_notifications("")
        assert result == []
    
    def test_whitespace_only_input(self):
        """Test with whitespace-only input."""
        result = split_output_to_notifications("   \n  \n  ")
        assert result == []
    
    def test_title_without_description(self):
        """Test title followed by another title (no description)."""
        output = """First Term:
Second Term:
This is the description"""
        result = split_output_to_notifications(output)
        assert result == [
            ("First Term", "No description provided."),
            ("Second Term", "This is the description"),
        ]
    
    def test_trailing_title_without_description(self):
        """Test when last line is a title without description."""
        output = """Completed Term:
Has a description
Orphan Title:"""
        result = split_output_to_notifications(output)
        assert result == [
            ("Completed Term", "Has a description"),
            ("Orphan Title", "No description provided."),
        ]
    
    def test_description_without_title_skipped(self):
        """Test that descriptions without preceding titles are skipped."""
        output = """Some random text without colon
Actual Title:
Actual Description"""
        result = split_output_to_notifications(output)
        assert result == [("Actual Title", "Actual Description")]
    
    def test_colon_in_middle_of_line(self):
        """Test that colons in the middle of lines don't create titles."""
        output = """API:
Application Programming Interface: a way to communicate"""
        result = split_output_to_notifications(output)
        # The description contains a colon but shouldn't be treated as title
        assert result == [("API", "Application Programming Interface: a way to communicate")]
    
    def test_preserves_title_text(self):
        """Test that title text is preserved correctly without trailing colon."""
        output = "Deep Learning:\nSubset of machine learning"
        result = split_output_to_notifications(output)
        assert result[0][0] == "Deep Learning"  # No colon
        assert ":" not in result[0][0]
    
    def test_handles_extra_whitespace(self):
        """Test that extra whitespace is handled correctly."""
        output = """  Term One:  
  Description with spaces  
  Term Two:  
  Another description  """
        result = split_output_to_notifications(output)
        assert result == [
            ("Term One", "Description with spaces"),
            ("Term Two", "Another description"),
        ]
    
    def test_multiline_descriptions_only_first_captured(self):
        """Test that only the first line after title is captured as description."""
        output = """Term:
First line of description
Second line should be ignored
Another Term:
Its description"""
        result = split_output_to_notifications(output)
        assert result == [
            ("Term", "First line of description"),
            ("Another Term", "Its description"),
        ]
    
    def test_real_world_example(self):
        """Test with realistic API output."""
        output = """Deep Learning:
A subset of machine learning using neural networks with multiple layers
API:
Application Programming Interface
GPU:
Graphics Processing Unit, used for parallel computing"""
        result = split_output_to_notifications(output)
        assert len(result) == 3
        assert result[0][0] == "Deep Learning"
        assert result[1][0] == "API"
        assert result[2][0] == "GPU"


class TestShowNotification:
    """Test cases for show_notification function."""
    
    @patch('src.utils.notification')
    def test_basic_notification(self, mock_notification):
        """Test that notification is called with correct parameters."""
        show_notification("Test Title", "Test Message")
        
        mock_notification.notify.assert_called_once_with(
            title="Test Title",
            message="Test Message",
            app_name="JargonTranslator",
            timeout=10,
        )
    
    @patch('src.utils.notification')
    def test_custom_timeout(self, mock_notification):
        """Test notification with custom timeout."""
        show_notification("Title", "Message", timeout=5)
        
        mock_notification.notify.assert_called_once()
        call_kwargs = mock_notification.notify.call_args[1]
        assert call_kwargs['timeout'] == 5
    
    @patch('src.utils.notification')
    def test_long_title_truncation(self, mock_notification):
        """Test that titles longer than 64 characters are truncated."""
        long_title = "A" * 100  # 100 characters
        show_notification(long_title, "Message")
        
        call_kwargs = mock_notification.notify.call_args[1]
        assert len(call_kwargs['title']) == 64
        assert call_kwargs['title'].endswith("...")
    
    @patch('src.utils.notification')
    def test_exactly_64_char_title_not_truncated(self, mock_notification):
        """Test that titles exactly 64 characters are not truncated."""
        title_64 = "A" * 64
        show_notification(title_64, "Message")
        
        call_kwargs = mock_notification.notify.call_args[1]
        assert call_kwargs['title'] == title_64
        assert len(call_kwargs['title']) == 64
    
    @patch('src.utils.notification')
    def test_empty_message(self, mock_notification):
        """Test notification with empty message."""
        show_notification("Title", "")
        
        mock_notification.notify.assert_called_once()
        call_kwargs = mock_notification.notify.call_args[1]
        assert call_kwargs['message'] == ""


# Fixtures for common test data
@pytest.fixture
def sample_api_output():
    """Sample API output for testing."""
    return """Machine Learning:
A type of artificial intelligence
Neural Network:
Computing system modeled after the brain
API:
Application Programming Interface"""


@pytest.fixture
def empty_api_output():
    """Empty API output."""
    return ""


def test_split_with_fixture(sample_api_output):
    """Test split function using fixture."""
    result = split_output_to_notifications(sample_api_output)
    assert len(result) == 3


def test_split_empty_with_fixture(empty_api_output):
    """Test split function with empty fixture."""
    result = split_output_to_notifications(empty_api_output)
    assert result == []
