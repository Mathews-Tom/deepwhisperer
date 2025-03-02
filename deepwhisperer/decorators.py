from __future__ import annotations

import time
import traceback
from functools import wraps
from typing import Any, Callable

from .deepwhisperer import DeepWhisperer


def sentinel(
    notifier: DeepWhisperer, default_description: str = "Task"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    A decorator to send Telegram notifications before and after a function execution using the DeepWhisperer class.

    Args:
        notifier (DeepWhisperer): A shared instance of DeepWhisperer.
        default_description (str, optional): Default description for the function being executed.

    Returns:
        Callable[[Callable[..., Any]], Callable[..., Any]]: Wrapped function with Telegram notifications.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            description = kwargs.pop("description", default_description)
            do_notify = kwargs.pop("do_notify", True)

            if do_notify:
                start_time = time.time()
                notifier.send_message(f"🚀 {description} started: `{func.__name__}`")

            try:
                result = func(*args, **kwargs)

                if do_notify:
                    elapsed_time = int(time.time() - start_time)
                    hours, remainder = divmod(elapsed_time, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    success_message = (
                        f"✅ {description} completed: `{func.__name__}`\n"
                        f"⏱ Time Taken: {hours}h {minutes}m {seconds}s"
                    )
                    notifier.send_message(success_message)
                return result

            except Exception as e:
                if do_notify:
                    error_details = traceback.format_exc()
                    error_message = (
                        f"❌ {description} failed: `{func.__name__}`\n"
                        f"⚠️ Error: {str(e)}\n"
                        f"🔍 Traceback:\n```{error_details}```"
                    )
                    notifier.send_message(error_message)
                raise

        return wrapper

    return decorator
