"""Tests for Show class."""

import pytest
from lightshow import Show
from lightshow.exceptions import InvalidTimestampError


def sync_command():
    """Simple sync command for testing."""
    return "sync_result"


async def async_command():
    """Simple async command for testing."""
    return "async_result"


class TestShow:
    """Test Show class functionality."""

    def test_create_show(self):
        """Test creating a basic show."""
        show = Show(name="test_show", duration=10.0, description="Test show")
        assert show.name == "test_show"
        assert show.duration == 10.0
        assert show.description == "Test show"

    def test_create_show_negative_duration(self):
        """Test that negative duration raises error."""
        with pytest.raises(ValueError):
            Show("test", duration=-1.0)

    def test_add_sync_event(self):
        """Test adding a sync event."""
        show = Show("test", duration=10.0)
        show.add_sync_event(0.0, sync_command, "Test event")

        events = show.timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].timestamp == 0.0
        assert events[0].description == "Test event"
        assert not events[0].is_async

    def test_add_async_event(self):
        """Test adding an async event."""
        show = Show("test", duration=10.0)
        show.add_async_event(5.0, async_command, "Async event")

        events = show.timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].timestamp == 5.0
        assert events[0].description == "Async event"
        assert events[0].is_async

    def test_add_sync_batch(self):
        """Test adding a sync batch event."""
        show = Show("test", duration=10.0)
        commands = [sync_command, sync_command, sync_command]
        show.add_sync_batch(2.0, commands, "Batch event")

        events = show.timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].timestamp == 2.0
        assert events[0].is_batch
        assert not events[0].is_async

    def test_add_async_batch(self):
        """Test adding an async batch event."""
        show = Show("test", duration=10.0)
        commands = [async_command, async_command]
        show.add_async_batch(3.0, commands, "Async batch")

        events = show.timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].timestamp == 3.0
        assert events[0].is_batch
        assert events[0].is_async

    def test_add_sync_events_bulk(self):
        """Test adding multiple sync events at once."""
        show = Show("test", duration=10.0)
        events_data = [
            (0.0, sync_command, "Event 1"),
            (2.0, sync_command, "Event 2"),
            (5.0, sync_command, "Event 3"),
        ]
        show.add_sync_events(events_data)

        events = show.timeline.get_sorted_events()
        assert len(events) == 3
        assert events[0].description == "Event 1"
        assert events[1].description == "Event 2"
        assert events[2].description == "Event 3"

    def test_add_async_events_bulk(self):
        """Test adding multiple async events at once."""
        show = Show("test", duration=10.0)
        events_data = [
            (1.0, async_command, "Async 1"),
            (3.0, async_command, "Async 2"),
        ]
        show.add_async_events(events_data)

        events = show.timeline.get_sorted_events()
        assert len(events) == 2
        assert all(event.is_async for event in events)

    def test_invalid_timestamp_negative(self):
        """Test that negative timestamps raise error."""
        show = Show("test", duration=10.0)
        with pytest.raises(InvalidTimestampError):
            show.add_sync_event(-1.0, sync_command)

    def test_invalid_timestamp_exceeds_duration(self):
        """Test that timestamps exceeding duration raise error."""
        show = Show("test", duration=10.0)
        with pytest.raises(InvalidTimestampError):
            show.add_sync_event(11.0, sync_command)

    def test_timestamp_at_duration_is_valid(self):
        """Test that timestamp exactly at duration is valid."""
        show = Show("test", duration=10.0)
        # Should not raise
        show.add_sync_event(10.0, sync_command)

    def test_mixed_sync_async_events(self):
        """Test show with both sync and async events."""
        show = Show("test", duration=10.0)
        show.add_sync_event(0.0, sync_command, "Sync")
        show.add_async_event(2.0, async_command, "Async")
        show.add_sync_batch(5.0, [sync_command, sync_command], "Sync batch")
        show.add_async_batch(7.0, [async_command], "Async batch")

        events = show.timeline.get_sorted_events()
        assert len(events) == 4
        assert not events[0].is_async
        assert events[1].is_async
        assert not events[2].is_async and events[2].is_batch
        assert events[3].is_async and events[3].is_batch

    def test_events_sorted_by_timestamp(self):
        """Test that events are sorted by timestamp."""
        show = Show("test", duration=10.0)
        show.add_sync_event(5.0, sync_command, "Second")
        show.add_sync_event(0.0, sync_command, "First")
        show.add_sync_event(9.0, sync_command, "Third")

        events = show.timeline.get_sorted_events()
        assert events[0].description == "First"
        assert events[1].description == "Second"
        assert events[2].description == "Third"

    def test_show_metadata(self):
        """Test show metadata."""
        metadata = {"artist": "Test", "genre": "Demo"}
        show = Show("test", duration=10.0, metadata=metadata)
        assert show.metadata == metadata

    def test_show_repr(self):
        """Test show string representation."""
        show = Show("test", duration=10.0)
        show.add_sync_event(0.0, sync_command)
        show.add_sync_event(5.0, sync_command)

        repr_str = repr(show)
        assert "test" in repr_str
        assert "10.0" in repr_str or "2" in repr_str  # Duration or event count
