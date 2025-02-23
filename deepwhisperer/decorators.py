import time
import traceback
from functools import wraps
from typing import Callable

from .deepwhisperer import DeepWhisperer


def deepwhisper_sentinel(
    notifier: DeepWhisperer, default_description: str = "Task"
) -> Callable:
    """
    A decorator to send Telegram notifications before and after a function execution using the DeepWhisperer class.

    Args:
        notifier (DeepWhisperer): A shared instance of DeepWhisperer.
        default_description (str, optional): Default description for the function being executed.

    Returns:
        function: Wrapped function with Telegram notifications.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            description = kwargs.pop(
                "description", default_description
            )  # Allow dynamic override
            do_notify = kwargs.pop("do_notify", True)  # Allow dynamic override

            if do_notify:
                # Notify function start
                start_time = time.time()
                notifier.send_message(f"🚀 {description} started: `{func.__name__}`")

            try:
                result = func(*args, **kwargs)  # Execute the original function

                if do_notify:
                    # Compute execution time
                    elapsed_time = int(time.time() - start_time)
                    hours, remainder = divmod(elapsed_time, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    # Notify success
                    success_message = (
                        f"✅ {description} completed: `{func.__name__}`\n"
                        f"⏱ Time Taken: {hours}h {minutes}m {seconds}s"
                    )
                    notifier.send_message(success_message)

                return result

            except Exception as e:
                if do_notify:
                    # Capture full error traceback
                    error_details = traceback.format_exc()
                    error_message = (
                        f"❌ {description} failed: `{func.__name__}`\n"
                        f"⚠️ Error: {str(e)}\n"
                        f"🔍 Traceback:\n```{error_details}```"
                    )
                    notifier.send_message(
                        error_message
                    )  # Send error details to Telegram
                raise  # Re-raise the exception

        return wrapper

    return decorator
