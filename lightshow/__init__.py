"""
Light Show Manager - Timeline-based show orchestration framework.

A pure Python framework for coordinating time-synchronized commands
across any hardware or software system.

Example:
    from lightshow import LightShowManager, Show

    # Create show
    show = Show("demo", duration=60.0)
    show.add_sync_event(0.0, lambda: print("Start!"))
    show.add_sync_batch(5.0, [cmd1, cmd2, cmd3])

    # Create manager
    manager = LightShowManager(
        shows=[show],
        pre_show=setup,
        post_show=cleanup
    )

    # Run show
    import asyncio
    asyncio.run(manager.run_show("demo"))
"""

__version__ = "0.2.0"
__author__ = "Jimmy Hickman"
__license__ = "MIT"

from lightshow.show import Show
from lightshow.manager import LightShowManager, LifecycleHooks
from lightshow.timeline import Timeline, TimelineEvent
from lightshow.executor import Executor
from lightshow.process_lock import ProcessLock, ProcessLockError
from lightshow.rotation import ShowRotation
from lightshow.volume_scheduler import VolumeScheduler
from lightshow.device_state import with_device_state_management
from lightshow.utils import normalize_show_name
from lightshow.exceptions import (
    LightShowError,
    ShowNotFoundError,
    InvalidTimestampError,
    EventExecutionError,
    ShowInterruptedError,
)

# Optional notification system (requires requests library for Pushover)
from lightshow.notifications import (
    NotificationManager,
    NotificationBackend,
    NotificationEvent,
    PushoverBackend,
    LoggingBackend,
)

# Audio module is available but not imported by default
# Users can import with: from lightshow.audio import AudioPlayer

__all__ = [
    # Main classes
    "Show",
    "LightShowManager",
    "LifecycleHooks",

    # Timeline classes
    "Timeline",
    "TimelineEvent",

    # Executor
    "Executor",

    # Process locking
    "ProcessLock",
    "ProcessLockError",

    # Show management
    "ShowRotation",
    "VolumeScheduler",

    # Device state management
    "with_device_state_management",

    # Notifications
    "NotificationManager",
    "NotificationBackend",
    "NotificationEvent",
    "PushoverBackend",
    "LoggingBackend",

    # Utilities
    "normalize_show_name",

    # Exceptions
    "LightShowError",
    "ShowNotFoundError",
    "InvalidTimestampError",
    "EventExecutionError",
    "ShowInterruptedError",

    # Version
    "__version__",
]
