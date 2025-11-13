"""Tests for Executor class."""
import asyncio
import pytest
from lightshow.executor import Executor


# Test commands
def sync_command():
    """Sync command that returns a value."""
    return "sync_result"


def sync_command_slow():
    """Sync command with sleep."""
    import time
    time.sleep(0.1)
    return "slow_result"


async def async_command():
    """Async command that returns a value."""
    return "async_result"


async def async_command_slow():
    """Async command with sleep."""
    await asyncio.sleep(0.1)
    return "slow_async_result"


def sync_command_error():
    """Sync command that raises an error."""
    raise ValueError("Sync error")


async def async_command_error():
    """Async command that raises an error."""
    raise ValueError("Async error")


class TestExecutor:
    """Test Executor class."""

    @pytest.mark.asyncio
    async def test_execute_sync_command(self):
        """Test executing a sync command."""
        executor = Executor()
        result = await executor.execute_sync(sync_command)
        assert result == "sync_result"
        executor.shutdown()

    @pytest.mark.asyncio
    async def test_execute_async_command(self):
        """Test executing an async command."""
        executor = Executor()
        result = await executor.execute_async(async_command)
        assert result == "async_result"
        executor.shutdown()

    @pytest.mark.asyncio
    async def test_execute_sync_batch(self):
        """Test executing a batch of sync commands."""
        executor = Executor()
        commands = [sync_command, sync_command, sync_command]
        results = await executor.execute_sync_batch(commands)
        assert len(results) == 3
        assert all(r == "sync_result" for r in results)
        executor.shutdown()

    @pytest.mark.asyncio
    async def test_execute_async_batch(self):
        """Test executing a batch of async commands."""
        executor = Executor()
        commands = [async_command, async_command]
        results = await executor.execute_async_batch(commands)
        assert len(results) == 2
        assert all(r == "async_result" for r in results)
        executor.shutdown()

    @pytest.mark.asyncio
    async def test_sync_command_runs_in_thread_pool(self):
        """Test that sync commands run concurrently in thread pool."""
        executor = Executor()

        # Start multiple slow commands
        start = asyncio.get_event_loop().time()
        tasks = [
            executor.execute_sync(sync_command_slow),
            executor.execute_sync(sync_command_slow),
            executor.execute_sync(sync_command_slow),
        ]
        await asyncio.gather(*tasks)
        end = asyncio.get_event_loop().time()

        # Should take ~0.1s (parallel) not ~0.3s (sequential)
        # Use 0.25s as threshold to account for overhead
        assert (end - start) < 0.25

        executor.shutdown()

    @pytest.mark.asyncio
    async def test_async_commands_run_concurrently(self):
        """Test that async commands run concurrently."""
        executor = Executor()

        start = asyncio.get_event_loop().time()
        tasks = [
            executor.execute_async(async_command_slow),
            executor.execute_async(async_command_slow),
            executor.execute_async(async_command_slow),
        ]
        await asyncio.gather(*tasks)
        end = asyncio.get_event_loop().time()

        # Should take ~0.1s (concurrent) not ~0.3s (sequential)
        assert (end - start) < 0.25

        executor.shutdown()

    @pytest.mark.asyncio
    async def test_sync_command_error_propagates(self):
        """Test that errors in sync commands propagate."""
        executor = Executor()
        with pytest.raises(ValueError, match="Sync error"):
            await executor.execute_sync(sync_command_error)
        executor.shutdown()

    @pytest.mark.asyncio
    async def test_async_command_error_propagates(self):
        """Test that errors in async commands propagate."""
        executor = Executor()
        with pytest.raises(ValueError, match="Async error"):
            await executor.execute_async(async_command_error)
        executor.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test executor shutdown."""
        executor = Executor()
        await executor.execute_sync(sync_command)
        executor.shutdown()
        # Should complete without errors

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test executor context manager."""
        with Executor() as executor:
            result = await executor.execute_sync(sync_command)
            assert result == "sync_result"
        # Executor should be shutdown after context

    @pytest.mark.asyncio
    async def test_shutdown_prevents_execution(self):
        """Test that shutdown prevents further execution."""
        executor = Executor()
        executor.shutdown()

        with pytest.raises(RuntimeError):
            await executor.execute_sync(sync_command)
