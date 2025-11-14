"""
Custom exceptions for light-show-manager package.
"""


class LightShowError(Exception):
    """Base exception for all light show errors."""

    pass


class ShowNotFoundError(LightShowError):
    """Raised when a show cannot be found."""

    def __init__(self, show_name: str):
        self.show_name = show_name
        super().__init__(f"Show not found: {show_name}")


class InvalidTimestampError(LightShowError):
    """Raised when an invalid timestamp is provided."""

    def __init__(self, timestamp: float, reason: str = ""):
        self.timestamp = timestamp
        super().__init__(f"Invalid timestamp {timestamp}: {reason}")


class EventExecutionError(LightShowError):
    """Raised when an event fails to execute."""

    def __init__(self, event_description: str, original_error: Exception):
        self.event_description = event_description
        self.original_error = original_error
        super().__init__(f"Event '{event_description}' failed: {original_error}")


class ShowInterruptedError(LightShowError):
    """Raised when a show is interrupted (e.g., by user or system)."""

    def __init__(self, show_name: str, reason: str = ""):
        self.show_name = show_name
        super().__init__(f"Show '{show_name}' interrupted: {reason}")
