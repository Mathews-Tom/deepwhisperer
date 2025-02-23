from pathlib import Path
from unittest.mock import MagicMock

import pytest

from deepwhisperer import DeepWhisperer


@pytest.fixture
def mock_notifier():
    """Fixture to create a mock DeepWhisperer instance."""
    notifier = MagicMock(spec=DeepWhisperer)
    return notifier


def test_send_message(mock_notifier):
    """Test that the send_message method correctly queues a message."""
    mock_notifier.send_message("Test message")
    mock_notifier.send_message.assert_called_once_with("Test message")


def test_send_file(mock_notifier):
    """Test that send_file is called correctly with a file path."""
    file_path = Path("test.txt")
    mock_notifier.send_file(file_path, "Test caption")
    mock_notifier.send_file.assert_called_once_with(file_path, "Test caption")


def test_send_photo(mock_notifier):
    """Test that send_photo is called correctly."""
    file_path = Path("photo.jpg")
    mock_notifier.send_photo(file_path, "Test caption")
    mock_notifier.send_photo.assert_called_once_with(file_path, "Test caption")
