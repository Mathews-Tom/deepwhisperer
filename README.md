# DeepWhisperer

## Overview
**DeepWhisperer** is a Python package for sending **Telegram notifications asynchronously** with advanced message handling. It provides a queue-based, non-blocking mechanism to send messages, images, documents, and other media via Telegram.

### **Key Features**
- 🚀 **Asynchronous message handling** via background processing
- 🔁 **Retry logic** with exponential backoff for failed messages
- 🔄 **Duplicate message filtering** using a TTL-based cache
- 📦 **Queue overflow handling** to prevent excessive accumulation
- 📢 **Message batching** to reduce API calls
- 🖼 **Support for multiple media types** (photos, videos, audio, documents)
- ✅ **Function Execution Notification Decorator** (`deepwhisper_sentinel`)

---

## Installation

### **Using pip (Recommended)**
```sh
pip install deepwhisperer
```

### **From Source**
```sh
git clone https://github.com/yourusername/deepwhisperer.git
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
from deepwhisperer import DeepWhisperer, deepwhisper_sentinel

notifier = DeepWhisperer(access_token="your_telegram_bot_token")

@deepwhisper_sentinel(notifier, default_description="Data Processing Task")
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

### **Decorator Parameters (`deepwhisper_sentinel`)**
| Parameter             | Type           | Default  | Description |
|----------------------|---------------|----------|-------------|
| `notifier`           | `DeepWhisperer` | Required | Instance of `DeepWhisperer` |
| `default_description` | `str`          | "Task"   | Default function description |

---

## Dependencies
DeepWhisperer requires the following dependencies, which are automatically installed:
```toml
[dependencies]
httpx = "*"  # Handles Telegram API requests
cachetools = "*"  # Provides TTLCache for duplicate prevention
```

---

## Code Structure
To improve efficiency, helper functions have been refactored into `_helpers.py`.
```plaintext
deepwhisperer/
│── __init__.py
│── deepwhisperer.py  # Core class
│── _helpers.py       # Internal helper functions
│── decorators.py     # Function execution notifier
│── constants.py      # Store class-wide constants
│── tests/            # Test cases
│   ├── test_deepwhisperer.py
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
