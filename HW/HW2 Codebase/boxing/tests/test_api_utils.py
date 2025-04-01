import pytest
from unittest.mock import patch, Mock
import requests
import random

from boxing.utils.api_utils import get_random


class TestGetRandom:
    """Test cases for the get_random API utility function."""

    @patch('requests.get')
    def test_get_random_success(self, mock_get):
        """Test that get_random successfully retrieves a random number when the API returns a valid response."""
        # Setup the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "0.42"
        mock_get.return_value = mock_response

        # Call the function under test
        result = get_random()

        # Assert the result
        assert result == 0.42
        # Verify the API was called with the expected URL and timeout
        mock_get.assert_called_once_with(
            'https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new',
            timeout=5
        )

    @patch('requests.get')
    @patch('random.random')
    def test_get_random_invalid_response(self, mock_random, mock_get):
        """Test that get_random uses the fallback when the API response is invalid."""
        # Setup the mock response with non-parseable content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "not a number"
        mock_get.return_value = mock_response

        # Setup fallback mock
        mock_random.return_value = 0.17

        # Call the function under test
        result = get_random()

        # Assert the result is from the fallback
        assert result == 0.17
        mock_random.assert_called_once()

    @patch('requests.get')
    @patch('random.random')
    def test_get_random_api_error(self, mock_random, mock_get):
        """Test that get_random uses the fallback when there's an API error."""
        # Setup the mock to raise an exception
        mock_get.side_effect = requests.RequestException("API error")

        # Setup fallback mock
        mock_random.return_value = 0.73

        # Call the function under test
        result = get_random()

        # Assert the result is from the fallback
        assert result == 0.73
        mock_random.assert_called_once()

    @patch('requests.get')
    @patch('random.random')
    def test_get_random_timeout(self, mock_random, mock_get):
        """Test that get_random uses the fallback when the API request times out."""
        # Setup the mock to raise a timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Setup fallback mock
        mock_random.return_value = 0.55

        # Call the function under test
        result = get_random()

        # Assert the result is from the fallback
        assert result == 0.55
        mock_random.assert_called_once()


class TestGetRandomSmoke:
    """Smoke tests for the get_random API utility function."""

    @patch('requests.get')
    def test_get_random_basic_operation(self, mock_get, caplog):
        """Smoke test for basic operation of get_random."""
        # Test with valid response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "0.7"
        mock_get.return_value = mock_response

        # Verify the function returns the expected result
        result = get_random()
        assert result == 0.7
        assert 0 <= result <= 1

        # Test with API error
        mock_get.side_effect = requests.RequestException("Connection error")
        
        # Should use fallback
        with patch('random.random', return_value=0.3):
            result = get_random()
            assert result == 0.3
            assert "Request to random.org failed" in caplog.text 