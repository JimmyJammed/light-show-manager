"""
Timeline management for light shows.

Handles time-based event scheduling with support for both sync and async commands.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Union
import bisect


@dataclass
class TimelineEvent:
    """
    Represents a single timeline event or batch of events.

    Attributes:
        timestamp: Time in seconds when event(s) should fire
        command: Single command or list of commands (for batch)
        description: Human-readable description of the event
        is_batch: Whether this is a batch of commands
        is_async: Whether commands are async (True) or sync (False)
        metadata: Additional metadata for the event
    """

    timestamp: float
    command: Union[Callable, List[Callable]]
    description: str = ""
    is_batch: bool = False
    is_async: bool = False
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate event after initialization."""
        if self.timestamp < 0:
            raise ValueError(f"Timestamp cannot be negative: {self.timestamp}")

        # Auto-detect batch
        if isinstance(self.command, list):
            self.is_batch = True

    @property
    def commands(self) -> List[Callable]:
        """Get commands as list (even if single command)."""
        if self.is_batch:
            return self.command
        return [self.command]

    def __lt__(self, other):
        """Enable sorting by timestamp."""
        if not isinstance(other, TimelineEvent):
            return NotImplemented
        return self.timestamp < other.timestamp

    def __repr__(self) -> str:
        mode = "async" if self.is_async else "sync"
        batch_info = f" (batch: {len(self.commands)})" if self.is_batch else ""
        return f"TimelineEvent({self.timestamp}s, {mode}{batch_info}, '{self.description}')"


class Timeline:
    """
    Manages a collection of timeline events sorted by timestamp.

    Provides efficient insertion and retrieval of events.
    """

    def __init__(self):
        """Initialize empty timeline."""
        self._events: List[TimelineEvent] = []

    def add(self, event: TimelineEvent) -> None:
        """
        Add event to timeline (maintains sorted order).

        Args:
            event: TimelineEvent to add
        """
        bisect.insort(self._events, event)

    def add_event(
        self,
        timestamp: float,
        command: Callable,
        description: str = "",
        is_async: bool = False,
        metadata: dict = None,
    ) -> None:
        """
        Add single event to timeline.

        Args:
            timestamp: Time in seconds when event should fire
            command: Callable to execute
            description: Event description
            is_async: Whether command is async
            metadata: Additional metadata
        """
        event = TimelineEvent(
            timestamp=timestamp,
            command=command,
            description=description,
            is_batch=False,
            is_async=is_async,
            metadata=metadata or {},
        )
        self.add(event)

    def add_batch(
        self,
        timestamp: float,
        commands: List[Callable],
        description: str = "",
        is_async: bool = False,
        metadata: dict = None,
    ) -> None:
        """
        Add batch of commands that fire simultaneously.

        Args:
            timestamp: Time when all commands fire
            commands: List of callables
            description: Batch description
            is_async: Whether commands are async
            metadata: Additional metadata
        """
        event = TimelineEvent(
            timestamp=timestamp,
            command=commands,
            description=description,
            is_batch=True,
            is_async=is_async,
            metadata=metadata or {},
        )
        self.add(event)

    def get_events_at(self, timestamp: float, tolerance: float = 0.001) -> List[TimelineEvent]:
        """
        Get all events at a specific timestamp (within tolerance).

        Args:
            timestamp: Time to query
            tolerance: Allowed time difference (seconds)

        Returns:
            List of events at that timestamp
        """
        return [event for event in self._events if abs(event.timestamp - timestamp) <= tolerance]

    def get_sorted_events(self) -> List[TimelineEvent]:
        """Get all events sorted by timestamp."""
        return self._events.copy()

    def get_events_between(self, start: float, end: float) -> List[TimelineEvent]:
        """
        Get events between start and end times (inclusive).

        Args:
            start: Start time (seconds)
            end: End time (seconds)

        Returns:
            List of events in range
        """
        return [event for event in self._events if start <= event.timestamp <= end]

    def clear(self) -> None:
        """Remove all events from timeline."""
        self._events.clear()

    def __len__(self) -> int:
        """Get number of events in timeline."""
        return len(self._events)

    def __iter__(self):
        """Iterate over events in chronological order."""
        return iter(self._events)

    def __repr__(self) -> str:
        return f"Timeline(events={len(self._events)})"
