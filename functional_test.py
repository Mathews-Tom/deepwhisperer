import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from deepwhisperer import DeepWhisperer

# Configure logging
logging.basicConfig(level=logging.INFO)

load_dotenv()
# Replace with your actual Telegram bot token and chat ID (o
# r let it be detected automatically)
BOT_TOKEN = os.getenv("DEEP_WHISPERER_API_KEY")
CHAT_ID = (
    None  # Optional: If you don't set it, it will try to retrieve it automatically.
)
FILE_PATH_IMAGE = Path("test_image.jpg")
FILE_PATH_VIDEO = Path("test_file.mp4")


def main():
    """
    Demonstrates the basic functionality of the DeepWhisperer class.
    """
    try:
        # Initialize DeepWhisperer
        whisperer = DeepWhisperer(access_token=BOT_TOKEN, chat_id=CHAT_ID)

        # Send some text messages
        whisperer.send_message("Hello from DeepWhisperer!")
        whisperer.send_message(
            "This is a test message with *Markdown*.", parse_mode="Markdown"
        )
        whisperer.send_message("Sending a duplicate message...", allow_duplicates=True)
        whisperer.send_message("Sending a duplicate message...", allow_duplicates=False)
        whisperer.send_message(
            "This is a message that will be dropped because it is duplicated.",
            allow_duplicates=False,
        )
        whisperer.send_message(
            "This is a message that will be dropped because it is duplicated.",
            allow_duplicates=False,
        )

        # Wait a little to ensure messages are processed
        time.sleep(10)

        # Create a dummy image file for testing (optional - you can use a real file)
        if not FILE_PATH_IMAGE.exists():
            with open(FILE_PATH_IMAGE, "wb") as file:
                file.write(
                    b"Dummy image content"
                )  # Replace with actual image data if using a real image

        # Create a dummy video file for testing (optional - you can use a real file)
        if not FILE_PATH_VIDEO.exists():
            with open(FILE_PATH_VIDEO, "wb") as file:
                file.write(
                    os.urandom(1024 * 1024)
                )  # Replace with actual video data if using a real video

        # Send a photo
        whisperer.send_photo(file_path=FILE_PATH_IMAGE, caption="Test Photo")

        # Send a document
        whisperer.send_file(file_path=FILE_PATH_VIDEO, caption="Test Document")

        whisperer.send_video(file_path=FILE_PATH_VIDEO, caption="Test Video")
        # Send a location
        whisperer.send_location(latitude=40.7128, longitude=-74.0060)

        # Wait some time for the messages to be processed
        time.sleep(10)

    except ValueError as e:
        logging.error(f"Error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        # Clean up the dummy image file if it was created
        if FILE_PATH_IMAGE.exists() and FILE_PATH_IMAGE.stat().st_size == len(
            b"Dummy image content"
        ):
            FILE_PATH_IMAGE.unlink()
        # Clean up the dummy video file if it was created
        if FILE_PATH_VIDEO.exists():
            FILE_PATH_VIDEO.unlink()

        # Stop the whisperer to correctly close the connection
        whisperer.stop()


if __name__ == "__main__":
    main()
