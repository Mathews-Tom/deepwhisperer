import hashlib
import io
import logging
import queue
import random
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from cachetools import TTLCache

from ._constants import (
    CONNECTION_MESSAGES,
    TIMESTAMP_PREFIX,
    TIMESTAMP_SUFFIX,
    TITLE,
    TITLE_PREFIX,
    TITLE_SUFFIX,
)

LOGGER = logging.getLogger(__name__)


class DeepWhisperer:
    """
    A class for sending Telegram notifications asynchronously with advanced message handling.

    DeepWhisperer provides a queue-based, non-blocking mechanism to send text messages, images,
    documents, videos, and other media via Telegram. It includes features such as:

    - **Asynchronous message handling** via a background thread.
    - **Retry logic** with exponential backoff for failed messages.
    - **Duplicate message filtering** using a TTL-based cache.
    - **Queue overflow handling** to prevent excessive message accumulation.
    - **Message batching** within a configurable time window to reduce API calls.
    - **Support for multiple media types** including photos, videos, audio, documents, and more.

    This class is useful for long-running scripts, monitoring tasks, and automated notifications.

    Args:
        access_token (str): Telegram bot API token.
        chat_id (str, optional): Target chat ID for sending messages. If None, the bot retrieves it dynamically.
        max_retries (int, optional): Maximum retry attempts for failed messages (default: 5).
        retry_delay (int, optional): Base delay in seconds for exponential backoff (default: 3).
        queue_size (int, optional): Maximum message queue size before new messages are discarded (default: 100).
        deduplication_ttl (int, optional): Time-to-live in seconds for duplicate message tracking (default: 300).
        batch_interval (int, optional): Time window in seconds to batch text messages before sending (default: 15).

    Attributes:
        access_token (str): The Telegram bot API token.
        chat_id (str): The target chat ID for sending messages.
        max_retries (int): Maximum retry attempts for failed messages.
        retry_delay (int): Base delay in seconds for exponential backoff.
        batch_interval (int): Time window in seconds for batching text messages.
        recent_messages (TTLCache): Cache for tracking sent messages to prevent duplication.
        message_queue (Queue): Queue for storing messages before they are processed.
        failed_messages (list): List of messages that failed after retry attempts.
        stop_event (threading.Event): Event to signal the processing thread to stop.
        executor (ThreadPoolExecutor): Thread pool executor for background processing.
        httpx_client (httpx.Client): HTTP client for making Telegram API requests.
    """

    def __init__(
        self,
        access_token: str,
        chat_id: Optional[str] = None,
        max_retries: int = 5,
        retry_delay: int = 3,
        queue_size: int = 100,
        deduplication_ttl: int = 300,
        batch_interval: int = 15,
    ) -> None:
        """
        Initializes the DeepWhisperer bot with Telegram API integration, asynchronous message handling,
        and retry logic.

        Args:
            access_token (str): Telegram bot API token.
            chat_id (str, optional): Target chat ID for sending messages. If None, it is retrieved dynamically.
            max_retries (int): Maximum retry attempts for failed messages.
            retry_delay (int): Base delay (seconds) for exponential backoff.
            queue_size (int): Maximum message queue size.
            deduplication_ttl (int): Time (seconds) to keep track of sent messages.
            batch_interval (int): Time window (seconds) to batch text messages before sending.
        """
        self.access_token = access_token
        self.httpx_client = httpx.Client(timeout=10)
        self.chat_id = chat_id if chat_id else self._get_chat_id()

        if not self.chat_id:
            raise ValueError("Failed to retrieve chat_id. Please provide it manually.")

        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_interval = batch_interval

        # Duplicate message tracking with automatic expiry
        self.recent_messages = TTLCache(maxsize=100, ttl=deduplication_ttl)

        # Initialize queues and threading components
        self.message_queue: queue.Queue[
            Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]
        ] = queue.Queue(maxsize=queue_size)
        self.failed_messages: List[Tuple[str, Dict[str, Any]]] = []
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.httpx_client = httpx.Client(timeout=10)

        # Start background processing thread
        self.executor.submit(self._process_queue)

        LOGGER.info(
            f"DeepWhisperer initialized with chat_id: {self.chat_id}, batch_interval: {self.batch_interval}s"
        )
        # Send initialization message
        self.send_message(self._get_connection_established_message())

    def _get_chat_id(self) -> Optional[str]:
        """
        Fetches the chat_id dynamically using the bot's getUpdates method.

        Returns:
            Optional[str]: The chat ID if found, otherwise None.
        """
        try:
            url = f"https://api.telegram.org/bot{self.access_token}/getUpdates"
            response = self.httpx_client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "result" in data and data["result"]:
                return data["result"][0]["message"]["chat"]["id"]
            else:
                LOGGER.error(
                    "Failed to fetch chat_id: No messages found in getUpdates."
                )
                return None
        except httpx.HTTPError as e:
            LOGGER.error(f"HTTP error retrieving chat_id: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"Unexpected error retrieving chat_id: {e}")
            return None

    @classmethod
    def _get_connection_established_message(cls):
        """Returns a randomly selected connection message."""
        return random.choice(CONNECTION_MESSAGES)

    @classmethod
    def _get_formatted_time(cls) -> str:
        """Returns the current date and time in GMT with a formatted string."""
        return f"{TIMESTAMP_PREFIX} {time.strftime('%Y-%m-%d | %H:%M:%S', time.gmtime())} | GMT {TIMESTAMP_SUFFIX}"

    @classmethod
    def _get_formatted_title(cls) -> str:
        """Returns the title with a formatted string."""
        return f"{TITLE_PREFIX} {TITLE} {TITLE_SUFFIX}"

    def _process_queue(self) -> None:
        """
        Processes queued messages asynchronously, batching them within a configurable
        interval and retrying failed messages.
        """
        while not self.stop_event.is_set():
            batch: List[Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]] = []
            collected_messages: List[str] = []
            start_time = time.time()

            try:
                while time.time() - start_time < self.batch_interval:
                    try:
                        item: Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]] = (
                            self.message_queue.get(timeout=0.5)
                        )
                        if item is None or item[0] == "STOP":
                            return

                        endpoint, payload, files = item

                        if endpoint == "sendMessage":
                            collected_messages.append(payload["text"])
                        else:
                            batch.append(item)

                        # Mark task as done
                        self.message_queue.task_done()

                    except queue.Empty:
                        continue

                if collected_messages:
                    combined_message = "\n\n".join(collected_messages)
                    batch.append(
                        (
                            "sendMessage",
                            {"chat_id": self.chat_id, "text": combined_message},
                            None,
                        )
                    )

                if batch:
                    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                        future_to_task = {
                            executor.submit(
                                self._send_request, endpoint, payload, files
                            ): (endpoint, payload)
                            for endpoint, payload, files in batch
                        }
                        for future in as_completed(future_to_task):
                            task = future_to_task[future]
                            try:
                                response = future.result()
                                if not response:
                                    self.failed_messages.append(task)
                            except Exception as e:
                                LOGGER.error("Error processing request: %s", e)
                                self.failed_messages.append(task)

                self._retry_failed_messages()
                time.sleep(0.5)

            except Exception:
                LOGGER.error("Error processing messages:\n%s", traceback.format_exc())

    def _retry_failed_messages(self) -> None:
        """Retries sending messages that previously failed."""
        if not self.failed_messages:
            return

        LOGGER.info("Retrying failed messages...")
        remaining_failed: List[
            Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]
        ] = []

        for endpoint, payload, files in self.failed_messages:
            try:
                response = self._send_request(endpoint, payload, files)
                if not response:
                    remaining_failed.append((endpoint, payload, files))
            except Exception as e:
                LOGGER.error(f"Retry failed: {e}")
                remaining_failed.append((endpoint, payload, files))

        self.failed_messages = remaining_failed

    def _send_request(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Optional[httpx.Response]:
        """Handles API requests with retries and exponential backoff."""

        url = f"https://api.telegram.org/bot{self.access_token}/{endpoint}"

        for attempt in range(self.max_retries):
            try:
                if files:
                    # Reset the file buffer to the beginning before each retry
                    for key, (_, file_obj, _) in files.items():
                        file_obj.seek(0)

                    response = self.httpx_client.post(url, data=payload, files=files)
                else:
                    response = self.httpx_client.post(url, data=payload)  # Fixed here

                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                LOGGER.warning(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    jitter = random.uniform(0.5, 1.5)
                    sleep_time = self.retry_delay * (2**attempt) * jitter
                    time.sleep(sleep_time)
                else:
                    LOGGER.error(
                        f"Max retries reached. Skipping request.\nError: {traceback.format_exc()}"
                    )
                    return None
            except Exception as e:
                LOGGER.error(f"Unexpected Error: {e}\n{traceback.format_exc()}")
                return None

    def _send_media(
        self,
        file_path: Path,
        endpoint: str,
        media_type: str,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """Generic method to send media files via Telegram bot."""

        if not file_path.exists():
            LOGGER.warning(f"File doesn't exist: {file_path}")
            return

        caption = caption or ""
        wrapped_caption = (
            f"{self._get_formatted_title()}\n{caption}\n{self._get_formatted_time()}"
        )

        payload = {
            "chat_id": self.chat_id,
            "caption": wrapped_caption,
            "disable_notification": disable_notification,
        }

        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            with open(file_path, "rb") as file:
                file_data = file.read()  # Read the file into memory

            mime_type = (
                f"{media_type}/{file_path.suffix[1:]}"
                if file_path.suffix
                else "application/octet-stream"
            )
            files = {
                media_type: (str(file_path.name), io.BytesIO(file_data), mime_type)
            }

            LOGGER.debug(f"Sending {media_type} {file_path} with payload {payload}")

            # Queue the media message
            self.message_queue.put_nowait((endpoint, payload, files))
            LOGGER.info(f"{media_type.capitalize()} queued successfully: {file_path}")

        except FileNotFoundError:
            LOGGER.error(f"File not found: {file_path}")
        except Exception as e:
            LOGGER.error(f"Error sending {media_type}: {e}\n{traceback.format_exc()}")

    def send_message(
        self, message: str, parse_mode: str = "Markdown", allow_duplicates: bool = False
    ) -> None:
        """
        Queues a text message for sending.

        Args:
            message (str): The text content of the message.
            parse_mode (str, optional): The parse mode for the message (e.g., 'Markdown', 'HTML'). Defaults to 'Markdown'.
            allow_duplicates (bool, optional): If True, allows sending duplicate messages. Defaults to False.
        """
        if not message.strip():
            LOGGER.warning("Attempted to send an empty message. Skipping.")
            return

        # Wrap message with title and timestamp
        wrapped_message = (
            f"{self._get_formatted_title()}\n{message}\n{self._get_formatted_time()}"
        )

        # Generate a hash for the message to prevent duplicates
        message_hash = hashlib.sha256(wrapped_message.encode()).hexdigest()

        # Check for duplicate messages within TTL
        if not allow_duplicates and message_hash in self.recent_messages:
            LOGGER.info(f"Skipping duplicate message: {wrapped_message}")
            return

        # Store only the hash in TTLCache to prevent duplicates
        self.recent_messages[message_hash] = True

        payload = {
            "chat_id": self.chat_id,
            "parse_mode": parse_mode,
            "text": wrapped_message,
        }

        try:
            # Attempt to queue the message
            self.message_queue.put_nowait(("sendMessage", payload, None))
            LOGGER.info(f"Message queued successfully: {message}")

        except queue.Full:
            LOGGER.warning(f"Message queue full. Dropping message: {message}")

        except Exception as e:
            LOGGER.error(f"Error queuing message: {e}\n{traceback.format_exc()}")

    def send_file(
        self,
        file_path: Path,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a file (document) via Telegram.

        Args:
            file_path (Path): The path to the file to send.
            caption (str, optional): The caption for the file. Defaults to None.
            disable_notification (bool, optional): If True, sends the file silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendDocument",
            "document",
            caption,
            disable_notification,
            reply_to_message_id,
        )

    def send_photo(
        self,
        file_path: Path,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a photo via Telegram.

        Args:
            file_path (Path): The path to the photo file.
            caption (str, optional): The caption for the photo. Defaults to None.
            disable_notification (bool, optional): If True, sends the photo silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendPhoto",
            "photo",
            caption,
            disable_notification,
            reply_to_message_id,
        )

    def send_audio(
        self,
        file_path: Path,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends an audio file via Telegram.

        Args:
            file_path (Path): The path to the audio file.
            caption (str, optional): The caption for the audio file. Defaults to None.
            disable_notification (bool, optional): If True, sends the audio silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendAudio",
            "audio",
            caption,
            disable_notification,
            reply_to_message_id,
        )

    def send_video(
        self,
        file_path: Path,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a video file via Telegram.

        Args:
            file_path (Path): The path to the video file.
            caption (str, optional): The caption for the video file. Defaults to None.
            disable_notification (bool, optional): If True, sends the video silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendVideo",
            "video",
            caption,
            disable_notification,
            reply_to_message_id,
        )

    def send_animation(
        self,
        file_path: Path,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends an animation (GIF) file via Telegram.

        Args:
            file_path (Path): The path to the animation file.
            caption (str, optional): The caption for the animation. Defaults to None.
            disable_notification (bool, optional): If True, sends the animation silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendAnimation",
            "animation",
            caption,
            disable_notification,
            reply_to_message_id,
        )

    def send_voice(
        self,
        file_path: Path,
        caption: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a voice message via Telegram.

        Args:
            file_path (Path): The path to the voice message file.
            caption (str, optional): The caption for the voice message. Defaults to None.
            disable_notification (bool, optional): If True, sends the voice message silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendVoice",
            "voice",
            caption,
            disable_notification,
            reply_to_message_id,
        )

    def send_video_note(
        self,
        file_path: Path,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a video note via Telegram.

        Args:
            file_path (Path): The path to the video note file.
            disable_notification (bool, optional): If True, sends the video note silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        self._send_media(
            file_path,
            "sendVideoNote",
            "video_note",
            None,  # Video notes do not support captions
            disable_notification,
            reply_to_message_id,
        )

    def send_media_group(
        self,
        media: List[Dict[str, Any]],
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a group of media files as an album via Telegram.

        Args:
            media (List[Dict[str, Any]]): A list of dictionaries, each representing a media file.
                                            Each dictionary must have:
                                            - 'type' (str): The type of the media ('photo', 'video').
                                            - 'media' (str): The media file id.
                                            - optionally 'caption' (str) : Add a caption to the media.
            disable_notification (bool, optional): If True, sends the media group silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        payload = {
            "chat_id": self.chat_id,
            "media": media,
            "disable_notification": disable_notification,
        }

        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            self.message_queue.put_nowait(("sendMediaGroup", payload, None))
            LOGGER.info("Media group queued.")
        except queue.Full:
            LOGGER.warning("Message queue full. Dropping media group.")
        except Exception:
            LOGGER.error(f"Error queuing media group:\n{traceback.format_exc()}")

    def send_location(
        self,
        latitude: float,
        longitude: float,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None,
    ) -> None:
        """
        Sends a location via Telegram.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            disable_notification (bool, optional): If True, sends the location silently. Defaults to False.
            reply_to_message_id (int, optional): If provided, replies to the specified message. Defaults to None.
        """
        payload = {
            "chat_id": self.chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "disable_notification": disable_notification,
        }

        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            self.message_queue.put_nowait(("sendLocation", payload, None))
            LOGGER.info(f"Location queued: lat={latitude}, long={longitude}")
        except queue.Full:
            LOGGER.warning(
                f"Message queue full. Dropping location: lat={latitude}, long={longitude}"
            )
        except Exception:
            LOGGER.error(f"Error queuing location:\n{traceback.format_exc()}")

    def stop(self) -> None:
        """Gracefully shuts down the notifier, ensuring all messages are processed before exiting."""
        LOGGER.info("Shutting down DeepWhisperer...")

        # Signal the processing thread to stop
        self.stop_event.set()

        try:
            # Drain the message queue to process remaining messages
            while not self.message_queue.empty():
                time.sleep(0.5)

            # Stop the executor gracefully
            self.executor.shutdown(wait=True)
            LOGGER.info("Executor shut down successfully.")

        except Exception as e:
            LOGGER.error(f"Error during shutdown: {e}\n{traceback.format_exc()}")

        finally:
            # Close the HTTP client session
            self.httpx_client.close()
            LOGGER.info("DeepWhisperer stopped.")


if __name__ == "__main__":
    pass
