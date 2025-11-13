"""
Notification system for light show events.

Provides pluggable notification backends (Pushover, email, webhooks, custom)
with configurable event types. Fully optional and opt-in.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class NotificationEvent(str, Enum):
    """
    Types of events that can trigger notifications.

    - SHOW_START: Show started successfully
    - SHOW_END: Show completed successfully
    - SHOW_BLOCKED: Show didn't start because it didn't meet can_run conditions (no errors)
    - SHOW_FAILED: Show failed to start or failed mid-run due to actual error(s)
    """
    SHOW_START = "show_start"
    SHOW_END = "show_end"
    SHOW_BLOCKED = "show_blocked"
    SHOW_FAILED = "show_failed"


class NotificationBackend(ABC):
    """
    Abstract base class for notification backends.

    Implement this interface to create custom notification backends
    (email, webhooks, SMS, Slack, Discord, etc.)
    """

    @abstractmethod
    def send(self, title: str, message: str, priority: int = 0) -> bool:
        """
        Send a notification.

        Args:
            title: Notification title
            message: Notification message body
            priority: Priority level (backend-specific, typically -2 to 2)

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if backend is properly configured.

        Returns:
            True if backend can send notifications, False otherwise
        """
        pass


class PushoverBackend(NotificationBackend):
    """
    Pushover notification backend.

    Requires:
    - Pushover account (https://pushover.net)
    - API token (create an application)
    - User key (from your account)

    Example:
        backend = PushoverBackend(
            api_token="your_app_token",
            user_key="your_user_key"
        )
    """

    PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(
        self,
        api_token: str,
        user_key: str,
        device: Optional[str] = None,
        sound: Optional[str] = None
    ):
        """
        Initialize Pushover backend.

        Args:
            api_token: Your Pushover application API token
            user_key: Your Pushover user key
            device: Optional specific device name to send to
            sound: Optional notification sound (see Pushover docs for sounds)
        """
        self.api_token = api_token
        self.user_key = user_key
        self.device = device
        self.sound = sound

    def send(self, title: str, message: str, priority: int = 0) -> bool:
        """
        Send notification via Pushover.

        Args:
            title: Notification title
            message: Notification message
            priority: Priority (-2=lowest, -1=low, 0=normal, 1=high, 2=emergency)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("Pushover backend not properly configured")
            return False

        payload = {
            "token": self.api_token,
            "user": self.user_key,
            "title": title,
            "message": message,
            "priority": priority
        }

        if self.device:
            payload["device"] = self.device
        if self.sound:
            payload["sound"] = self.sound

        try:
            response = requests.post(self.PUSHOVER_API_URL, data=payload, timeout=10)

            if response.status_code == 200:
                logger.debug(f"Pushover notification sent: {title}")
                return True
            else:
                logger.error(
                    f"Pushover API error: {response.status_code} - {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"Failed to send Pushover notification: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if API token and user key are provided."""
        return bool(self.api_token and self.user_key)


class LoggingBackend(NotificationBackend):
    """
    Simple logging backend for testing/debugging.

    Writes notifications to the logger instead of sending externally.
    Useful for testing notification logic without external services.
    """

    def send(self, title: str, message: str, priority: int = 0) -> bool:
        """Log notification instead of sending."""
        logger.info(f"[NOTIFICATION] {title}: {message} (priority: {priority})")
        return True

    def is_configured(self) -> bool:
        """Logging backend is always configured."""
        return True


class NotificationManager:
    """
    Manages notifications for light show events.

    Features:
    - Pluggable backends (Pushover, email, custom, etc.)
    - Configurable event types
    - Per-event priority levels
    - Automatic integration with LightShowManager

    Event Types:
    - SHOW_START: Show started successfully
    - SHOW_END: Show completed successfully
    - SHOW_BLOCKED: Show didn't start due to can_run policy check (no errors)
    - SHOW_FAILED: Show failed due to actual error/exception

    Example:
        # Basic usage
        notifier = NotificationManager(
            backend=PushoverBackend(api_token="...", user_key="..."),
            events=[NotificationEvent.SHOW_START, NotificationEvent.SHOW_FAILED]
        )

        # Advanced usage with priorities
        notifier = NotificationManager(
            backend=PushoverBackend(api_token="...", user_key="..."),
            events=[
                NotificationEvent.SHOW_START,
                NotificationEvent.SHOW_END,
                NotificationEvent.SHOW_BLOCKED,
                NotificationEvent.SHOW_FAILED
            ],
            priorities={
                NotificationEvent.SHOW_FAILED: 1,  # High priority
                NotificationEvent.SHOW_BLOCKED: 0,  # Normal priority
                NotificationEvent.SHOW_START: -1,   # Low priority
                NotificationEvent.SHOW_END: -1      # Low priority
            }
        )

        # Use with manager
        manager = LightShowManager(
            shows=[...],
            notifier=notifier  # Optional parameter
        )
    """

    def __init__(
        self,
        backend: NotificationBackend,
        events: Optional[List[NotificationEvent]] = None,
        priorities: Optional[Dict[NotificationEvent, int]] = None,
        enabled: bool = True
    ):
        """
        Initialize notification manager.

        Args:
            backend: Notification backend to use (Pushover, email, custom, etc.)
            events: List of events to notify for (default: all events)
            priorities: Dict mapping events to priority levels (default: 0 for all)
            enabled: Whether notifications are enabled (default: True)
        """
        self.backend = backend
        self.enabled = enabled and backend.is_configured()

        # Configure events
        if events is None:
            # Default: notify for all events
            self.events: Set[NotificationEvent] = set(NotificationEvent)
        else:
            self.events = set(events)

        # Configure priorities
        self.priorities: Dict[NotificationEvent, int] = priorities or {}

        if not self.enabled:
            if not backend.is_configured():
                logger.warning("Notification backend not properly configured, notifications disabled")
            else:
                logger.info("Notifications explicitly disabled")
        else:
            logger.info(
                f"Notifications enabled for events: {[e.value for e in self.events]}"
            )

    def notify(
        self,
        event: NotificationEvent,
        title: str,
        message: str,
        priority: Optional[int] = None
    ) -> bool:
        """
        Send a notification for an event.

        Args:
            event: Event type
            title: Notification title
            message: Notification message
            priority: Optional priority override (uses event default if not provided)

        Returns:
            True if notification sent successfully (or skipped because event not enabled),
            False if sending failed
        """
        # Check if notifications are enabled
        if not self.enabled:
            logger.debug(f"Notifications disabled, skipping: {event.value}")
            return True

        # Check if this event type should be notified
        if event not in self.events:
            logger.debug(f"Event {event.value} not in enabled events, skipping")
            return True

        # Determine priority
        if priority is None:
            priority = self.priorities.get(event, 0)

        # Send notification
        logger.debug(f"Sending notification for {event.value}: {title}")
        return self.backend.send(title, message, priority)

    def notify_show_start(self, show_name: str, context: Dict = None) -> bool:
        """
        Notify that a show is starting.

        Args:
            show_name: Name of the show
            context: Optional context dict with additional info

        Returns:
            True if notification sent successfully, False otherwise
        """
        title = f"Show Starting: {show_name}"
        message = f"The '{show_name}' light show is starting."

        if context:
            # Add context details if available
            details = []
            if "volume" in context:
                details.append(f"Volume: {context['volume']}%")
            if "duration" in context:
                details.append(f"Duration: {context['duration']:.1f}s")

            if details:
                message += "\n" + ", ".join(details)

        return self.notify(NotificationEvent.SHOW_START, title, message)

    def notify_show_end(self, show_name: str, context: Dict = None) -> bool:
        """
        Notify that a show has ended.

        Args:
            show_name: Name of the show
            context: Optional context dict with additional info

        Returns:
            True if notification sent successfully, False otherwise
        """
        title = f"Show Completed: {show_name}"
        message = f"The '{show_name}' light show has completed successfully."

        return self.notify(NotificationEvent.SHOW_END, title, message)

    def notify_show_blocked(self, show_name: str, reason: str) -> bool:
        """
        Notify that a show was blocked from running (didn't meet can_run conditions).

        This is for policy/validation failures, not actual errors.
        For example: outside active hours, key in wrong position, etc.

        Args:
            show_name: Name of the show
            reason: Reason why show was blocked (from can_run check)

        Returns:
            True if notification sent successfully, False otherwise
        """
        title = f"Show Blocked: {show_name}"
        message = f"The '{show_name}' light show was blocked from running (did not meet can_run conditions).\n\nReason: {reason}"

        return self.notify(NotificationEvent.SHOW_BLOCKED, title, message)

    def notify_show_failed(self, show_name: str, error: str) -> bool:
        """
        Notify that a show failed with an actual error.

        This is for genuine errors/exceptions, not policy failures.
        For example: hardware failure, network error, exception during show, etc.

        Args:
            show_name: Name of the show
            error: Error message/exception details

        Returns:
            True if notification sent successfully, False otherwise
        """
        title = f"Show Failed: {show_name}"
        message = f"The '{show_name}' light show failed with an error.\n\nError: {error}"

        return self.notify(NotificationEvent.SHOW_FAILED, title, message)

    def disable(self) -> None:
        """Disable notifications."""
        self.enabled = False
        logger.info("Notifications disabled")

    def enable(self) -> None:
        """Enable notifications (if backend is configured)."""
        if self.backend.is_configured():
            self.enabled = True
            logger.info("Notifications enabled")
        else:
            logger.warning("Cannot enable notifications: backend not configured")
