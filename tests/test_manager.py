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
            shows=[show], pre_show=pre_hook, post_show=post_hook, on_event=event_hook
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

    @pytest.mark.asyncio
    async def test_can_run_default_allows(self):
        """Test default can_run behavior allows shows to run."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        # No can_run hook - should allow by default
        manager = LightShowManager(shows=[show])
        await manager.run_show("test")

        assert "cmd1" in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_sync_allows(self):
        """Test can_run hook that allows execution (sync)."""
        reset_tracking()

        def allow_check(show, context):
            return (True, "Test passed")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], can_run=allow_check)
        await manager.run_show("test")

        assert "cmd1" in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_sync_blocks(self):
        """Test can_run hook that blocks execution (sync)."""
        reset_tracking()

        def block_check(show, context):
            return (False, "Not allowed")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], can_run=block_check)
        await manager.run_show("test")

        # Command should not have executed
        assert "cmd1" not in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_async_allows(self):
        """Test can_run hook that allows execution (async)."""
        reset_tracking()

        async def allow_check(show, context):
            await asyncio.sleep(0.01)
            return (True, "Async check passed")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], can_run=allow_check)
        await manager.run_show("test")

        assert "cmd1" in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_async_blocks(self):
        """Test can_run hook that blocks execution (async)."""
        reset_tracking()

        async def block_check(show, context):
            await asyncio.sleep(0.01)
            return (False, "Async check failed")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], can_run=block_check)
        await manager.run_show("test")

        # Command should not have executed
        assert "cmd1" not in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_bool_only_return(self):
        """Test can_run hook with bool-only return (no reason string)."""
        reset_tracking()

        def bool_check(show, context):
            return True

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], can_run=bool_check)
        await manager.run_show("test")

        assert "cmd1" in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_bool_false_only(self):
        """Test can_run hook with False return (no reason string)."""
        reset_tracking()

        def bool_check(show, context):
            return False

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show], can_run=bool_check)
        await manager.run_show("test")

        # Command should not have executed
        assert "cmd1" not in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_with_context(self):
        """Test can_run hook receives context."""
        reset_tracking()
        context_received = {}

        def check_with_context(show, context):
            context_received.update(context)
            return (context.get("allowed", False), "Context checked")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        # First try: blocked
        manager = LightShowManager(shows=[show], can_run=check_with_context)
        await manager.run_show("test", context={"allowed": False})
        assert "cmd1" not in executed_commands
        assert context_received["allowed"] == False

        # Second try: allowed
        reset_tracking()
        context_received.clear()
        await manager.run_show("test", context={"allowed": True})
        assert "cmd1" in executed_commands
        assert context_received["allowed"] == True

    @pytest.mark.asyncio
    async def test_can_run_error_fails_open(self):
        """Test can_run hook errors fail open (allow show to run)."""
        reset_tracking()

        def error_check(show, context):
            raise ValueError("Check error")

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        # Error in can_run should allow show to run (fail-open)
        manager = LightShowManager(shows=[show], can_run=error_check)
        await manager.run_show("test")

        # Show should have run despite error
        assert "cmd1" in executed_commands

    @pytest.mark.asyncio
    async def test_can_run_invalid_return_fails_open(self):
        """Test can_run hook with invalid return fails open."""
        reset_tracking()

        def invalid_check(show, context):
            return "invalid"

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        # Invalid return should allow show to run (fail-open)
        manager = LightShowManager(shows=[show], can_run=invalid_check)
        await manager.run_show("test")

        # Show should have run despite invalid return
        assert "cmd1" in executed_commands

    @pytest.mark.asyncio
    async def test_blocks_concurrent_shows_by_default(self):
        """Test that starting a new show while one is running is blocked by default."""
        reset_tracking()

        show1 = Show("show1", duration=1.0)
        show1.add_sync_event(0.0, sync_cmd("show1_start"))
        show1.add_sync_event(0.5, sync_cmd("show1_mid"))

        show2 = Show("show2", duration=0.5)
        show2.add_sync_event(0.0, sync_cmd("show2_start"))

        manager = LightShowManager(shows=[show1, show2])

        # Start show1 in background
        show1_task = asyncio.create_task(manager.run_show("show1"))

        # Wait a bit for show1 to start
        await asyncio.sleep(0.1)

        # Try to start show2 - should be blocked
        await manager.run_show("show2")

        # Show2 should NOT have run
        assert "show2_start" not in executed_commands

        # Show1 should still be running
        assert manager.is_running
        assert manager.current_show_name == "show1"

        # Wait for show1 to finish
        await show1_task

        # Now show1 should be done
        assert not manager.is_running
        assert "show1_start" in executed_commands
        assert "show1_mid" in executed_commands

    @pytest.mark.asyncio
    async def test_interrupt_stops_current_show(self):
        """Test that interrupt=True stops the current show and starts new one."""
        reset_tracking()

        show1 = Show("show1", duration=5.0)
        show1.add_sync_event(0.0, sync_cmd("show1_start"))
        show1.add_sync_event(3.0, sync_cmd("show1_mid"))
        show1.add_sync_event(4.9, sync_cmd("show1_end"))

        show2 = Show("show2", duration=0.5)
        show2.add_sync_event(0.0, sync_cmd("show2_start"))
        show2.add_sync_event(0.4, sync_cmd("show2_end"))

        post_show_calls = []

        def post_hook(show, context):
            post_show_calls.append(show.name)

        manager = LightShowManager(shows=[show1, show2], post_show=post_hook)

        # Start show1 in background
        show1_task = asyncio.create_task(manager.run_show("show1"))

        # Wait for show1 to start but not reach mid event (mid is at 3.0s)
        await asyncio.sleep(0.3)

        # Verify show1 is running
        assert manager.is_running
        assert manager.current_show_name == "show1"
        assert "show1_start" in executed_commands

        # Interrupt show1 and start show2
        await manager.run_show("show2", interrupt=True)

        # Show1 should have been interrupted (mid and end events should NOT have run)
        # Mid is at 3.0s, we stopped at 0.3s, so mid should NOT have fired
        assert "show1_mid" not in executed_commands
        assert "show1_end" not in executed_commands

        # Show2 should have run completely
        assert "show2_start" in executed_commands
        assert "show2_end" in executed_commands

        # Post-show should have been called for show1 (cleanup)
        assert "show1" in post_show_calls

        # Clean up show1 task
        try:
            await show1_task
        except:
            pass  # Expected to be interrupted

    @pytest.mark.asyncio
    async def test_stop_current_show(self):
        """Test manually stopping a running show."""
        reset_tracking()

        show = Show("test", duration=5.0)
        show.add_sync_event(0.0, sync_cmd("start"))
        show.add_sync_event(3.0, sync_cmd("mid"))
        show.add_sync_event(4.9, sync_cmd("end"))

        post_show_called = []

        def post_hook(s, c):
            post_show_called.append(True)

        manager = LightShowManager(shows=[show], post_show=post_hook)

        # Start show in background
        show_task = asyncio.create_task(manager.run_show("test"))

        # Wait for show to start but not reach mid event (mid is at 3.0s)
        await asyncio.sleep(0.3)

        # Verify show is running
        assert manager.is_running
        assert manager.current_show_name == "test"
        assert "start" in executed_commands

        # Stop the show
        await manager.stop_current_show()

        # Show should have stopped
        assert not manager.is_running
        assert manager.current_show_name is None

        # Mid and end events should NOT have run (mid is at 3.0s, we stopped at 0.3s)
        assert "mid" not in executed_commands
        assert "end" not in executed_commands

        # Post-show should have been called
        assert len(post_show_called) == 1

        # Clean up task
        try:
            await show_task
        except:
            pass

    @pytest.mark.asyncio
    async def test_is_running_property(self):
        """Test is_running property."""
        reset_tracking()

        show = Show("test", duration=1.0)
        show.add_sync_event(0.0, sync_cmd("cmd1"))
        show.add_sync_event(0.5, sync_cmd("cmd2"))

        manager = LightShowManager(shows=[show])

        # Initially not running
        assert not manager.is_running
        assert manager.current_show_name is None

        # Start show in background
        show_task = asyncio.create_task(manager.run_show("test"))

        # Wait a bit for show to start
        await asyncio.sleep(0.2)

        # Should be running
        assert manager.is_running
        assert manager.current_show_name == "test"

        # Wait for show to complete
        await show_task

        # Should be done
        assert not manager.is_running
        assert manager.current_show_name is None

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test that stopping when no show is running doesn't crash."""
        reset_tracking()

        show = Show("test", duration=0.5)
        show.add_sync_event(0.0, sync_cmd("cmd1"))

        manager = LightShowManager(shows=[show])

        # Try to stop when nothing is running
        await manager.stop_current_show()  # Should not crash

        # Should still work normally
        await manager.run_show("test")
        assert "cmd1" in executed_commands
