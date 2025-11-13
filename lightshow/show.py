"""
Show class for defining light shows with timeline events.

Provides separate methods for sync and async events for clarity.
"""
from typing import Callable, List, Optional, Tuple
from lightshow.timeline import Timeline, TimelineEvent
from lightshow.exceptions import InvalidTimestampError


class Show:
    """
    Represents a light show with timeline events.

    A show consists of:
    - Name and duration
    - Timeline of events (commands to execute at specific times)
    - Support for both sync and async commands
    - Batch events that fire simultaneously

    Example:
        show = Show(name="demo", duration=60.0)

        # Sync events (run in thread pool)
        show.add_sync_event(0.0, lambda: print("Start"))
        show.add_sync_batch(5.0, [cmd1, cmd2, cmd3])

        # Async events (awaited)
        show.add_async_event(10.0, async_function)
        show.add_async_batch(15.0, [async1, async2])
    """

    def __init__(
        self,
        name: str,
        duration: float,
        description: str = "",
        metadata: Optional[dict] = None
    ):
        """
        Initialize a show.

        Args:
            name: Show name (unique identifier)
            duration: Total duration in seconds
            description: Human-readable description
            metadata: Additional metadata (e.g., artist, genre, etc.)

        Raises:
            ValueError: If duration is negative
        """
        if duration < 0:
            raise ValueError(f"Duration cannot be negative: {duration}")

        self.name = name
        self.duration = duration
        self.description = description
        self.metadata = metadata or {}
        self.timeline = Timeline()

    # ========== SYNC EVENT METHODS ==========

    def add_sync_event(
        self,
        timestamp: float,
        command: Callable,
        description: str = ""
    ) -> None:
        """
        Add a synchronous event at timestamp.

        The command will be executed in a thread pool to avoid blocking.

        Args:
            timestamp: Time in seconds when event should fire
            command: Sync callable to execute
            description: Event description

        Raises:
            InvalidTimestampError: If timestamp is invalid

        Example:
            def turn_on_lights():
                GPIO.output(17, HIGH)

            show.add_sync_event(0.0, turn_on_lights, "Turn on lights")
        """
        self._validate_timestamp(timestamp)
        self.timeline.add_event(
            timestamp=timestamp,
            command=command,
            description=description,
            is_async=False
        )

    def add_sync_batch(
        self,
        timestamp: float,
        commands: List[Callable],
        description: str = ""
    ) -> None:
        """
        Add a batch of synchronous commands that fire simultaneously.

        All commands run concurrently in thread pool.

        Args:
            timestamp: Time when all commands fire
            commands: List of sync callables
            description: Batch description

        Raises:
            InvalidTimestampError: If timestamp is invalid
            ValueError: If commands list is empty

        Example:
            show.add_sync_batch(5.0, [
                lambda: lights1.on(),
                lambda: lights2.on(),
                lambda: motor.start()
            ], "Turn on all devices")
        """
        self._validate_timestamp(timestamp)
        if not commands:
            raise ValueError("Commands list cannot be empty")

        self.timeline.add_batch(
            timestamp=timestamp,
            commands=commands,
            description=description,
            is_async=False
        )

    # ========== ASYNC EVENT METHODS ==========

    def add_async_event(
        self,
        timestamp: float,
        command: Callable,
        description: str = ""
    ) -> None:
        """
        Add an asynchronous event at timestamp.

        The command will be awaited directly.

        Args:
            timestamp: Time in seconds when event should fire
            command: Async callable to execute
            description: Event description

        Raises:
            InvalidTimestampError: If timestamp is invalid

        Example:
            async def play_audio():
                await audio_player.play("song.mp3")

            show.add_async_event(0.0, play_audio, "Start music")
        """
        self._validate_timestamp(timestamp)
        self.timeline.add_event(
            timestamp=timestamp,
            command=command,
            description=description,
            is_async=True
        )

    def add_async_batch(
        self,
        timestamp: float,
        commands: List[Callable],
        description: str = ""
    ) -> None:
        """
        Add a batch of asynchronous commands that fire simultaneously.

        All commands are awaited concurrently.

        Args:
            timestamp: Time when all commands fire
            commands: List of async callables
            description: Batch description

        Raises:
            InvalidTimestampError: If timestamp is invalid
            ValueError: If commands list is empty

        Example:
            show.add_async_batch(10.0, [
                async_lights1.on(),
                async_lights2.on(),
                async_audio.play("song.mp3")
            ], "Synchronized async operations")
        """
        self._validate_timestamp(timestamp)
        if not commands:
            raise ValueError("Commands list cannot be empty")

        self.timeline.add_batch(
            timestamp=timestamp,
            commands=commands,
            description=description,
            is_async=True
        )

    # ========== BULK ADD METHODS ==========

    def add_sync_events(
        self,
        events: List[Tuple[float, Callable, str]]
    ) -> None:
        """
        Add multiple sync events at once.

        Args:
            events: List of (timestamp, command, description) tuples

        Example:
            show.add_sync_events([
                (0.0, cmd1, "Event 1"),
                (5.0, cmd2, "Event 2"),
                (10.0, cmd3, "Event 3")
            ])
        """
        for timestamp, command, description in events:
            self.add_sync_event(timestamp, command, description)

    def add_async_events(
        self,
        events: List[Tuple[float, Callable, str]]
    ) -> None:
        """
        Add multiple async events at once.

        Args:
            events: List of (timestamp, command, description) tuples

        Example:
            show.add_async_events([
                (0.0, async_cmd1, "Event 1"),
                (5.0, async_cmd2, "Event 2"),
                (10.0, async_cmd3, "Event 3")
            ])
        """
        for timestamp, command, description in events:
            self.add_async_event(timestamp, command, description)

    # ========== UTILITY METHODS ==========

    def _validate_timestamp(self, timestamp: float) -> None:
        """Validate timestamp is within show duration."""
        if timestamp < 0:
            raise InvalidTimestampError(
                timestamp,
                "Timestamp cannot be negative"
            )
        if timestamp > self.duration:
            raise InvalidTimestampError(
                timestamp,
                f"Timestamp {timestamp}s exceeds show duration {self.duration}s"
            )

    def get_events(self) -> List[TimelineEvent]:
        """Get all events in chronological order."""
        return self.timeline.get_sorted_events()

    def get_events_between(self, start: float, end: float) -> List[TimelineEvent]:
        """Get events between start and end times."""
        return self.timeline.get_events_between(start, end)

    @property
    def total_events(self) -> int:
        """Get total number of events in show."""
        return len(self.timeline)

    @property
    def has_events(self) -> bool:
        """Check if show has any events."""
        return len(self.timeline) > 0

    def clear_events(self) -> None:
        """Remove all events from show."""
        self.timeline.clear()

    def __repr__(self) -> str:
        return (
            f"Show(name='{self.name}', duration={self.duration}s, "
            f"events={self.total_events})"
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.duration}s, {self.total_events} events)"
