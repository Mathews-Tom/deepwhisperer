from unittest.mock import MagicMock

import pytest

from deepwhisperer import DeepWhisperer, deepwhisperer_sentinel


@pytest.fixture
def mock_notifier():
    """Fixture to create a mock DeepWhisperer instance."""
    notifier = MagicMock(spec=DeepWhisperer)
    return notifier


def test_deepwhisperer_sentinel_decorator(mock_notifier):
    """Test the decorator's behavior on function execution success."""

    @deepwhisperer_sentinel(mock_notifier, default_description="Sample Task")
    def sample_function():
        return "Success"

    result = sample_function()

    mock_notifier.send_message.assert_any_call(
        "🚀 Sample Task started: `sample_function`"
    )
    mock_notifier.send_message.assert_any_call(
        "✅ Sample Task completed: `sample_function`\n⏱ Time Taken: 0h 0m 0s"
    )
    assert result == "Success"


def test_deepwhisperer_sentinel_decorator_exception(mock_notifier):
    """Test the decorator's behavior when an exception occurs."""

    @deepwhisperer_sentinel(mock_notifier, default_description="Error Task")
    def failing_function():
        raise ValueError("Test Error")

    with pytest.raises(ValueError, match="Test Error"):
        failing_function()

    mock_notifier.send_message.assert_any_call(
        "🚀 Error Task started: `failing_function`"
    )
    assert any(
        "❌ Error Task failed: `failing_function`" in call.args[0]
        for call in mock_notifier.send_message.call_args_list
    )
