"""Tests for LightShowManager class."""
import asyncio
import pytest
from lightshow import LightShowManager, Show
from lightshow.exceptions import ShowNotFoundError


# Test tracking variables
executed_commands = []
hook_calls = []


def reset_tracking():
    """Reset tracking variables."""
    global executed_commands, hook_calls
    executed_commands = []
    hook_calls = []


def sync_cmd(name):
    """Create a sync command that tracks execution."""
    def cmd():
        executed_commands.append(name)
        return name
    return cmd


def async_cmd(name):
    """Create an async command that tracks execution."""
    async def cmd():
        executed_commands.append(name)
        await asyncio.sleep(0.01)
        return name
    return cmd


def pre_hook(show, context):
    """Pre-show hook."""
    hook_calls.append(("pre_show", show.name))


def post_hook(show, context):
    """Post-show hook."""
    hook_calls.append(("post_show", show.name))


def event_hook(event, show, context):
    """Event hook."""
    hook_calls.append(("on_event", event.description))


def error_hook(error, event_or_show, context):
    """Error hook."""
    hook_calls.append(("on_error", str(error)))


class TestLightShowManager:
    """Test LightShowManager class."""

    def test_create_manager(self):
        """Test creating a manager."""
        show = Show("test", duration=1.0)
        manager = LightShowManager(shows=[show])
        assert len(manager.shows) == 1
        assert "test" in manager.shows

    def test_create_manager_multiple_shows(self):
        """Test creating manager with multiple shows."""
        show1 = Show("show1", duration=1.0)
        show2 = Show("show2", duration=2.0)
        manager = LightShowManager(shows=[show1, show2])
        assert len(manager.shows) == 2
        assert "show1" in manager.shows
        assert "show2" in manager.shows

    @pytest.mark.asyncio
    async def test_run_show_not_found(self):
        """Test running a non-existent show raises error."""
        show = Show("test", duration=1.0)
        manager = LightShowManager(shows=[show])

        with pytest.raises(ShowNotFoundError):
            await manager.run_show("nonexistent")

    @pytest.mark.asyncio
    async def test_run_simple_show(self):
        """Test running a simple show with sync events."""
        reset_tracking()

        show = Show("test", duration=1.0)
        show.add_sync_event(0.0, sync_cmd("cmd1"))
        show.add_sync_event(0.1, sync_cmd("cmd2"))

        manager = LightShowManager(shows=[show])
        await manager.run_show("test")

        assert "cmd1" in executed_commands
        assert "cmd2" in executed_commands

    @pytest.mark.asyncio
    async def test_run_show_with_async_events(self):
        """Test running show with async events."""
        reset_tracking()

        show = Show("test", duration=1.0)
        show.add_async_event(0.0, async_cmd("async1"))
        show.add_async_event(0.1, async_cmd("async2"))

        manager = LightShowManager(shows=[show])
        await manager.run_show("test")

        assert "async1" in executed_commands
        assert "async2" in executed_commands

    @pytest.mark.asyncio
    async def test_run_show_mixed_sync_async(self):
        """Test running show with mixed sync/async events."""
        reset_tracking()

        show = Show("test", duration=1.0)
        show.add_sync_event(0.0, sync_cmd("sync1"))
        show.add_async_event(0.1, async_cmd("async1"))
        show.add_sync_event(0.2, sync_cmd("sync2"))

        manager = LightShowManager(shows=[show])
        await manager.run_show("test")

        assert len(executed_commands) == 3
        assert "sync1" in executed_commands
        assert "async1" in executed_commands
        assert "sync2" in executed_commands

    @pytest.mark.asyncio
    async def test_pre_show_hook(self):
        """Test pre-show hook is called."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], pre_show=pre_hook)
        await manager.run_show("test")

        assert ("pre_show", "test") in hook_calls

    @pytest.mark.asyncio
    async def test_post_show_hook(self):
        """Test post-show hook is called."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], post_show=post_hook)
        await manager.run_show("test")

        assert ("post_show", "test") in hook_calls

    @pytest.mark.asyncio
    async def test_event_hook(self):
        """Test event hook is called for each event."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"), "Event 1")
        show.add_sync_event(0.1, sync_cmd("cmd2"), "Event 2")

        manager = LightShowManager(shows=[show], on_event=event_hook)
        await manager.run_show("test")

        assert ("on_event", "Event 1") in hook_calls
        assert ("on_event", "Event 2") in hook_calls

    @pytest.mark.asyncio
    async def test_all_hooks(self):
        """Test all hooks work together."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"), "Event 1")

        manager = LightShowManager(
            shows=[show],
            pre_show=pre_hook,
            post_show=post_hook,
            on_event=event_hook
        )
        await manager.run_show("test")

        assert ("pre_show", "test") in hook_calls
        assert ("on_event", "Event 1") in hook_calls
        assert ("post_show", "test") in hook_calls

    @pytest.mark.asyncio
    async def test_context_passed_to_hooks(self):
        """Test context is passed to hooks."""
        context_received = {}

        def hook_with_context(show, context):
            context_received.update(context)

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], pre_show=hook_with_context)
        await manager.run_show("test", context={"key": "value"})

        assert context_received == {"key": "value"}

    @pytest.mark.asyncio
    async def test_batch_execution(self):
        """Test batch events execute correctly."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_batch(0.0, [sync_cmd("b1"), sync_cmd("b2"), sync_cmd("b3")])

        manager = LightShowManager(shows=[show])
        await manager.run_show("test")

        assert "b1" in executed_commands
        assert "b2" in executed_commands
        assert "b3" in executed_commands

    @pytest.mark.asyncio
    async def test_error_in_event(self):
        """Test error handling in events."""
        reset_tracking()

        def error_cmd():
            raise ValueError("Test error")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, error_cmd, "Error event")

        manager = LightShowManager(shows=[show], on_error=error_hook)

        with pytest.raises(Exception):
            await manager.run_show("test")

        # Error hook should have been called
        assert any("on_error" in call for call in hook_calls)

    @pytest.mark.asyncio
    async def test_post_show_runs_on_error(self):
        """Test post-show hook runs even when there's an error."""
        reset_tracking()

        def error_cmd():
            raise ValueError("Test error")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, error_cmd)

        manager = LightShowManager(shows=[show], post_show=post_hook)

        try:
            await manager.run_show("test")
        except Exception:
            pass

        # Post-show should still be called
        assert ("post_show", "test") in hook_calls
