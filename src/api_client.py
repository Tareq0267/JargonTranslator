"""
JamAI API client with retry logic and error handling.
"""

import logging
import time
from typing import Optional
import requests

from .config import APIConfig

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when API communication fails."""
    pass


class JamAIClient:
    """
    Client for interacting with the JamAI API.
    
    Features:
    - Automatic retry with exponential backoff
    - Proper error handling and logging
    - Configurable timeouts
    """
    
    def __init__(self, config: APIConfig):
        """
        Initialize the JamAI client.
        
        Args:
            config: APIConfig instance with credentials and settings.
        """
        self.config = config
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {config.api_key}",
            "X-PROJECT-ID": config.project_id,
        }
    
    def send_transcription(self, input_text: str) -> str:
        """
        Send transcription to JamAI API and get jargon explanations.
        
        Args:
            input_text: The transcribed text to analyze.
            
        Returns:
            The API response with jargon explanations.
            
        Raises:
            APIError: If all retry attempts fail.
        """
        payload = {
            "data": [{"input": input_text}],
            "table_id": self.config.table_id,
            "stream": False,
        }
        
        last_error = None
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                logger.debug(f"API request attempt {attempt}/{self.config.max_retries}")
                
                response = requests.post(
                    self.config.base_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                
                return self._parse_response(response.json())
                
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"API timeout (attempt {attempt}): {e}")
                
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"API connection error (attempt {attempt}): {e}")
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                logger.warning(f"API HTTP error (attempt {attempt}): {e}")
                
                # Don't retry on client errors (4xx)
                if response.status_code < 500:
                    break
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"API request error (attempt {attempt}): {e}")
            
            # Exponential backoff before retry
            if attempt < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
        
        # All retries exhausted
        raise APIError(f"Failed after {self.config.max_retries} attempts: {last_error}")
    
    def _parse_response(self, response_data: dict) -> str:
        """
        Parse the API response to extract the output.
        
        Args:
            response_data: The JSON response from the API.
            
        Returns:
            The extracted output string.
        """
        try:
            rows = response_data.get("rows", [])
            if rows:
                output = rows[0]["columns"]["Output"]["choices"][0]["message"]["content"]
                return output
            else:
                logger.warning("API returned empty rows")
                return ""
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing API response: {e}")
            logger.debug(f"Response data: {response_data}")
            return ""


def create_client(config: Optional[APIConfig] = None) -> JamAIClient:
    """
    Factory function to create a JamAI client.
    
    Args:
        config: Optional APIConfig. If None, loads from environment.
        
    Returns:
        Configured JamAIClient instance.
    """
    if config is None:
        from .config import get_api_config
        config = get_api_config()
    
    return JamAIClient(config)
