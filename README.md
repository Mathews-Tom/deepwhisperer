# DeepWhisperer

## Overview

**DeepWhisperer** is a Python package for sending **Telegram notifications asynchronously** with advanced message handling. It provides a queue-based, non-blocking mechanism to send messages, images, documents, and other media via Telegram. The package is designed to enhance the monitoring and communication of long-running tasks, ensuring efficient and reliable notifications without interrupting the main program flow.

### **Key Features**

- **🚀 Asynchronous Message Handling**: Messages are queued and processed in the background, allowing the main program to continue execution without waiting for notifications.

- **📦 Batch Processing with Configurable Interval**: Messages received within a specified time window (default: 10 seconds) are combined into a single message, reducing message spam and improving readability.

- **🔄 Retry Mechanism**: Failed messages are automatically retried using exponential backoff, enhancing reliability under unstable network conditions.

- **🚫 Duplicate Message Filtering**: Prevents sending identical messages within a configurable time-to-live (TTL) period, reducing redundancy.

- **⚠️ Queue Overflow Handling**: Limits the queue size to prevent excessive memory usage, gracefully handling overflow scenarios by discarding excess messages.

- **📷 Rich Media Support**: Supports sending images and documents alongside text messages, enabling seamless sharing of visual results or files.

- **✅ Function Execution Notification Decorator** (`deepwhisperer_sentinel`): Simplifies integrating Telegram notifications into your existing functions. The `deepwhisperer_sentinel` decorator automatically sends notifications when a function starts, completes successfully, or encounters an error. ing tasks.

---

## Prerequisite - Create a Telegram Bot

1. Open Telegram App on your device - To create a Telegram bot, you'll need to have the Telegram app installed on your computer. If you don't have it already, you can download it from the Telegram website.
2. Connect to BotFather - BotFather is a bot created by Telegram that allows you to create and manage your own bots. To connect to [BotFather](https://telegram.me/BotFather), search for `@BotFather` in the Telegram app and click on the result to start a conversation.

    ![Search for @BotFather](https://raw.githubusercontent.com/Mathews-Tom/deepwhisperer/refs/heads/main/assets/BotFather.jpeg)

3. Select the New Bot option - In the conversation with BotFather, select the "New Bot", `/newbot` option to start creating your new bot. BotFather will guide you through the rest of the process.

4. Add a bot name - Next, BotFather will ask you to provide a name for your bot. Choose a name that accurately reflects the purpose of your bot and is easy to remember.

5. Choose a username for your bot - Lastly, BotFather will ask you to choose a username for your bot. This username will be used to create a unique URL that people can use to access your bot. Choose a username that is easy to remember and related to your bot's purpose.

6. Get your Bots HTTP Token - If you send the command `/token` in BotFather and select the bot, you will get the HTTP Token needed to continue with the automation.

    ![Create new bot](https://raw.githubusercontent.com/Mathews-Tom/deepwhisperer/refs/heads/main/assets/CreateNewBot.jpeg)

## Installation

### **Using pip (Recommended)**

```sh
pip install deepwhisperer
```

### **From Source**

```sh
gh repo clone Mathews-Tom/deepwhisperer
cd deepwhisperer
pip install -e .
```

---

## Usage

### **1️⃣ Initializing DeepWhisperer**

```python
from deepwhisperer import DeepWhisperer

notifier = DeepWhisperer(access_token="your_telegram_bot_token")
notifier.send_message("Hello, Telegram!")
```

### **2️⃣ Using the Decorator for Function Execution Notifications**

```python
from deepwhisperer import DeepWhisperer, deepwhisperer_sentinel

notifier = DeepWhisperer(access_token="your_telegram_bot_token")

@deepwhisperer_sentinel(notifier, default_description="Data Processing Task")
def process_data():
    import time
    time.sleep(3)  # Simulating a task
    print("Task Completed")

process_data()
```

### **3️⃣ Sending Different Types of Messages**

```python
# Sending a photo
notifier.send_photo("path/to/photo.jpg", caption="Look at this!")

# Sending a document
notifier.send_file("path/to/document.pdf", caption="Important file")

# Sending a location
notifier.send_location(latitude=37.7749, longitude=-122.4194)

# Sending a video
notifier.send_video("path/to/video.mp4", caption="Watch this!")
```

---

## Configuration & Parameters

### **DeepWhisperer Class Arguments**

| Parameter          | Type     | Default | Description |
|-------------------|---------|---------|-------------|
| `access_token`    | `str`   | Required | Telegram Bot API token |
| `chat_id`         | `str`   | `None`   | Target chat ID (auto-detected if not provided) |
| `max_retries`     | `int`   | `5`      | Max retry attempts for failed messages |
| `retry_delay`     | `int`   | `3`      | Base delay for exponential backoff |
| `queue_size`      | `int`   | `100`    | Max message queue size before discarding |
| `deduplication_ttl` | `int` | `300`    | Time-to-live for duplicate message tracking |
| `batch_interval`  | `int`   | `15`     | Time window for batching text messages |

### **Decorator Parameters (`deepwhisperer_sentinel`)**

| Parameter             | Type           | Default  | Description |
|----------------------|---------------|----------|-------------|
| `notifier`           | `DeepWhisperer` | Required | Instance of `DeepWhisperer` |
| `default_description` | `str`          | "Task"   | Default function description |

---

## Dependencies

DeepWhisperer requires the following dependencies, which are automatically installed:

```toml
[dependencies]
httpx = "*"  # Handles Telegram API reques
cachetools = "*"  # Provides TTLCache for duplicate prevention
```

---

## Code Structure

```plaintext
deepwhisperer/
│── __init__.py
│── deepwhisperer.py  # Core class
│── decorators.py     # Function execution notifier
│── constants.py      # Store class-wide constants
│── tests/            # Test cases
│   ├── __init__.py
│   ├── test_deepwhisperer.py
│   ├── test_decorators.py    
│── pyproject.toml    # Project metadata
│── README.md         # Documentation
│── LICENSE           # License file
│── .gitignore        # Ignore unnecessary files
```

---

## License

This project is licensed under the **MIT License**. See `LICENSE` for details.

## Author

[Tom Mathews](https://github.com/Mathews-Tom)
