"""Tests for Timeline class."""

import pytest
from lightshow.timeline import Timeline, TimelineEvent


def dummy_command():
    """Dummy command for testing."""
    pass


class TestTimelineEvent:
    """Test TimelineEvent class."""

    def test_create_event(self):
        """Test creating a timeline event."""
        event = TimelineEvent(
            timestamp=5.0,
            command=dummy_command,
            description="Test event",
            is_async=False,
            is_batch=False,
        )
        assert event.timestamp == 5.0
        assert event.command == dummy_command
        assert event.description == "Test event"
        assert not event.is_async
        assert not event.is_batch

    def test_event_comparison(self):
        """Test event comparison by timestamp."""
        event1 = TimelineEvent(1.0, dummy_command, "First", False, False)
        event2 = TimelineEvent(5.0, dummy_command, "Second", False, False)

        assert event1 < event2
        assert not event2 < event1

    def test_negative_timestamp_rejected(self):
        """Test that negative timestamps are rejected."""
        with pytest.raises(ValueError):
            TimelineEvent(-1.0, dummy_command, "Invalid", False, False)

    def test_batch_auto_detection(self):
        """Test that batch is auto-detected from list of commands."""
        event = TimelineEvent(1.0, [dummy_command, dummy_command], "Batch", False, False)
        assert event.is_batch

    def test_commands_property(self):
        """Test commands property returns list."""
        single_event = TimelineEvent(1.0, dummy_command, "Single", False, False)
        batch_event = TimelineEvent(1.0, [dummy_command, dummy_command], "Batch", False, False)

        assert len(single_event.commands) == 1
        assert len(batch_event.commands) == 2


class TestTimeline:
    """Test Timeline class."""

    def test_create_timeline(self):
        """Test creating an empty timeline."""
        timeline = Timeline()
        assert len(timeline) == 0

    def test_add_event(self):
        """Test adding an event to timeline."""
        timeline = Timeline()
        event = TimelineEvent(5.0, dummy_command, "Test", False, False)
        timeline.add(event)

        events = timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].timestamp == 5.0

    def test_add_event_method(self):
        """Test add_event convenience method."""
        timeline = Timeline()
        timeline.add_event(5.0, dummy_command, "Test", is_async=False)

        events = timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].timestamp == 5.0

    def test_add_batch_method(self):
        """Test add_batch convenience method."""
        timeline = Timeline()
        timeline.add_batch(5.0, [dummy_command, dummy_command], "Batch", is_async=False)

        events = timeline.get_sorted_events()
        assert len(events) == 1
        assert events[0].is_batch
        assert len(events[0].commands) == 2

    def test_add_multiple_events(self):
        """Test adding multiple events."""
        timeline = Timeline()

        for i in range(5):
            event = TimelineEvent(float(i), dummy_command, f"Event {i}", False, False)
            timeline.add(event)

        events = timeline.get_sorted_events()
        assert len(events) == 5

    def test_events_sorted(self):
        """Test that events are returned sorted by timestamp."""
        timeline = Timeline()

        # Add events out of order
        timeline.add(TimelineEvent(5.0, dummy_command, "5", False, False))
        timeline.add(TimelineEvent(1.0, dummy_command, "1", False, False))
        timeline.add(TimelineEvent(9.0, dummy_command, "9", False, False))
        timeline.add(TimelineEvent(0.0, dummy_command, "0", False, False))

        events = timeline.get_sorted_events()
        timestamps = [e.timestamp for e in events]
        assert timestamps == [0.0, 1.0, 5.0, 9.0]

    def test_clear_timeline(self):
        """Test clearing timeline."""
        timeline = Timeline()
        timeline.add(TimelineEvent(1.0, dummy_command, "Test", False, False))
        timeline.add(TimelineEvent(2.0, dummy_command, "Test", False, False))
        assert len(timeline) == 2

        timeline.clear()
        assert len(timeline) == 0

    def test_get_events_at(self):
        """Test getting events at specific timestamp."""
        timeline = Timeline()
        timeline.add(TimelineEvent(1.0, dummy_command, "1", False, False))
        timeline.add(TimelineEvent(1.001, dummy_command, "1.001", False, False))
        timeline.add(TimelineEvent(2.0, dummy_command, "2", False, False))

        events = timeline.get_events_at(1.0)
        assert len(events) >= 1  # Within tolerance

    def test_get_events_between(self):
        """Test getting events between timestamps."""
        timeline = Timeline()
        timeline.add(TimelineEvent(1.0, dummy_command, "1", False, False))
        timeline.add(TimelineEvent(5.0, dummy_command, "5", False, False))
        timeline.add(TimelineEvent(10.0, dummy_command, "10", False, False))

        events = timeline.get_events_between(2.0, 8.0)
        assert len(events) == 1
        assert events[0].timestamp == 5.0

    def test_iteration(self):
        """Test iterating over timeline events."""
        timeline = Timeline()
        timeline.add(TimelineEvent(1.0, dummy_command, "1", False, False))
        timeline.add(TimelineEvent(2.0, dummy_command, "2", False, False))

        count = 0
        for event in timeline:
            count += 1
        assert count == 2
