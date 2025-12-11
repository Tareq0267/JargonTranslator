"""
Unit tests for src/api_client.py
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

from src.api_client import JamAIClient, APIError, create_client
from src.config import APIConfig


@pytest.fixture
def api_config():
    """Create a test API config."""
    return APIConfig(
        project_id="test_project",
        api_key="test_api_key",
        table_id="test_table",
        max_retries=3,
        retry_delay=0.01,  # Fast retries for testing
        timeout=5,
    )


@pytest.fixture
def client(api_config):
    """Create a test client."""
    return JamAIClient(api_config)


class TestJamAIClientInit:
    """Test JamAIClient initialization."""
    
    def test_headers_set_correctly(self, api_config):
        """Test that headers are set with correct values."""
        client = JamAIClient(api_config)
        
        assert client.headers["authorization"] == "Bearer test_api_key"
        assert client.headers["X-PROJECT-ID"] == "test_project"
        assert client.headers["content-type"] == "application/json"
        assert client.headers["accept"] == "application/json"
    
    def test_config_stored(self, api_config):
        """Test that config is stored."""
        client = JamAIClient(api_config)
        
        assert client.config == api_config


class TestSendTranscription:
    """Test send_transcription method."""
    
    @patch('src.api_client.requests.post')
    def test_successful_request(self, mock_post, client):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rows": [{
                "columns": {
                    "Output": {
                        "choices": [{
                            "message": {"content": "AI:\nArtificial Intelligence"}
                        }]
                    }
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = client.send_transcription("Test input")
        
        assert result == "AI:\nArtificial Intelligence"
        mock_post.assert_called_once()
    
    @patch('src.api_client.requests.post')
    def test_request_payload(self, mock_post, client):
        """Test that request payload is correct."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rows": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        client.send_transcription("My transcription")
        
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']
        
        assert payload['data'] == [{"input": "My transcription"}]
        assert payload['table_id'] == "test_table"
        assert payload['stream'] is False
    
    @patch('src.api_client.requests.post')
    def test_empty_rows_returns_empty_string(self, mock_post, client):
        """Test empty rows returns empty string."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rows": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = client.send_transcription("Test")
        
        assert result == ""
    
    @patch('src.api_client.requests.post')
    def test_retries_on_timeout(self, mock_post, client):
        """Test that timeouts trigger retries."""
        mock_post.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.Timeout("Timeout"),
            MagicMock(
                json=lambda: {"rows": [{"columns": {"Output": {"choices": [{"message": {"content": "Success"}}]}}}]},
                raise_for_status=MagicMock()
            ),
        ]
        
        result = client.send_transcription("Test")
        
        assert result == "Success"
        assert mock_post.call_count == 3
    
    @patch('src.api_client.requests.post')
    def test_retries_on_connection_error(self, mock_post, client):
        """Test that connection errors trigger retries."""
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            MagicMock(
                json=lambda: {"rows": [{"columns": {"Output": {"choices": [{"message": {"content": "OK"}}]}}}]},
                raise_for_status=MagicMock()
            ),
        ]
        
        result = client.send_transcription("Test")
        
        assert result == "OK"
        assert mock_post.call_count == 2
    
    @patch('src.api_client.requests.post')
    def test_raises_api_error_after_max_retries(self, mock_post, client):
        """Test APIError raised after exhausting retries."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        with pytest.raises(APIError) as exc_info:
            client.send_transcription("Test")
        
        assert "Failed after 3 attempts" in str(exc_info.value)
        assert mock_post.call_count == 3
    
    @patch('src.api_client.requests.post')
    def test_no_retry_on_4xx_error(self, mock_post, client):
        """Test that 4xx errors don't trigger retries."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
        mock_post.return_value = mock_response
        
        with pytest.raises(APIError):
            client.send_transcription("Test")
        
        # Should only try once for client errors
        assert mock_post.call_count == 1
    
    @patch('src.api_client.requests.post')
    def test_retry_on_5xx_error(self, mock_post, client):
        """Test that 5xx errors trigger retries."""
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        
        mock_response_ok = MagicMock()
        mock_response_ok.json.return_value = {"rows": [{"columns": {"Output": {"choices": [{"message": {"content": "OK"}}]}}}]}
        mock_response_ok.raise_for_status = MagicMock()
        
        mock_post.side_effect = [mock_response_500, mock_response_ok]
        
        result = client.send_transcription("Test")
        
        assert result == "OK"
        assert mock_post.call_count == 2


class TestParseResponse:
    """Test _parse_response method."""
    
    def test_valid_response(self, client):
        """Test parsing valid response."""
        response_data = {
            "rows": [{
                "columns": {
                    "Output": {
                        "choices": [{
                            "message": {"content": "Parsed content"}
                        }]
                    }
                }
            }]
        }
        
        result = client._parse_response(response_data)
        
        assert result == "Parsed content"
    
    def test_empty_rows(self, client):
        """Test parsing response with empty rows."""
        response_data = {"rows": []}
        
        result = client._parse_response(response_data)
        
        assert result == ""
    
    def test_missing_keys(self, client):
        """Test parsing response with missing keys."""
        response_data = {"rows": [{"columns": {}}]}
        
        result = client._parse_response(response_data)
        
        assert result == ""
    
    def test_malformed_response(self, client):
        """Test parsing malformed response."""
        response_data = {"unexpected": "structure"}
        
        result = client._parse_response(response_data)
        
        assert result == ""


class TestCreateClient:
    """Test create_client factory function."""
    
    def test_with_provided_config(self, api_config):
        """Test creating client with provided config."""
        client = create_client(api_config)
        
        assert isinstance(client, JamAIClient)
        assert client.config == api_config
    
    @patch('src.config.get_api_config')
    def test_loads_config_from_env(self, mock_get_config):
        """Test that config is loaded from env when not provided."""
        mock_config = APIConfig(
            project_id="env_project",
            api_key="env_key",
            table_id="env_table",
        )
        mock_get_config.return_value = mock_config
        
        client = create_client(None)
        
        assert client.config.project_id == "env_project"
        mock_get_config.assert_called_once()
