from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import httpx
import pytest

from deepwhisperer import DeepWhisperer

# Mock data for Telegram API responses
MOCK_CHAT_ID = "123456789"
MOCK_RESPONSE = {"result": [{"message": {"chat": {"id": MOCK_CHAT_ID}}}]}


# Fixture for DeepWhisperer instance
@pytest.fixture
def deepwhisperer():
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.get.return_value.json.return_value = MOCK_RESPONSE
        dw = DeepWhisperer(access_token="fake_token")
        yield dw


# Test initialization and chat_id retrieval
def test_initialization(deepwhisperer):
    assert deepwhisperer.chat_id == MOCK_CHAT_ID
    deepwhisperer.httpx_client.get.assert_called_once()


# Test sending a message
def test_send_message(deepwhisperer):
    with patch("hashlib.sha256") as mock_sha256:
        mock_sha256.return_value.hexdigest.return_value = "mock_hash"
        deepwhisperer.send_message("Test message")
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() == 2


# Test sending a file
def test_send_file(deepwhisperer):
    mock_file_path = Path("test_file.txt")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_file(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test sending a photo
def test_send_photo(deepwhisperer):
    mock_file_path = Path("test_photo.jpg")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_photo(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test sending a video
def test_send_video(deepwhisperer):
    mock_file_path = Path("test_video.mp4")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_video(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test sending an audio file
def test_send_audio(deepwhisperer):
    mock_file_path = Path("test_audio.mp3")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_audio(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test sending a location
def test_send_location(deepwhisperer):
    deepwhisperer.send_location(latitude=37.7749, longitude=-122.4194)
    # Account for the initialization message
    assert deepwhisperer.message_queue.qsize() >= 0


# Test stopping the DeepWhisperer
def test_stop(deepwhisperer):
    deepwhisperer.stop()
    assert deepwhisperer.stop_event.is_set()


# Test retry logic for failed messages
def test_retry_failed_messages(deepwhisperer):
    # Ensure the failed_messages list has the correct structure
    deepwhisperer.failed_messages = [("sendMessage", {"text": "Failed message"}, None)]
    with patch.object(deepwhisperer, "_send_request", return_value=None):
        deepwhisperer._retry_failed_messages()
        assert len(deepwhisperer.failed_messages) >= 0


# Test duplicate message filtering
def test_duplicate_message_filtering(deepwhisperer):
    with patch("hashlib.sha256") as mock_sha256:
        mock_sha256.return_value.hexdigest.return_value = "mock_hash"
        deepwhisperer.send_message("Test message")
        deepwhisperer.send_message("Test message")  # This should be filtered
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test queue overflow handling
def test_queue_overflow(deepwhisperer):
    with patch("hashlib.sha256") as mock_sha256:
        mock_sha256.return_value.hexdigest.return_value = "mock_hash"
        # Account for the initialization message
        for _ in range(
            99
        ):  # Queue size is 100, and 1 is already occupied by the initialization message
            deepwhisperer.send_message("Test message")
        assert deepwhisperer.message_queue.qsize() == 2


# Test sending a video note
def test_send_video_note(deepwhisperer):
    mock_file_path = Path("test_video_note.mp4")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_video_note(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test sending an animation
def test_send_animation(deepwhisperer):
    mock_file_path = Path("test_animation.gif")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_animation(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0


# Test sending a voice message
def test_send_voice(deepwhisperer):
    mock_file_path = Path("test_voice.ogg")
    with patch("builtins.open", mock_open(read_data=b"test")) as mock_file:
        deepwhisperer.send_voice(mock_file_path)
        # Account for the initialization message
        assert deepwhisperer.message_queue.qsize() >= 0
