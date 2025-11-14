"""
Command executor with support for sync and async operations.

Handles execution of timeline events with proper async/sync handling.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Any

logger = logging.getLogger(__name__)


class Executor:
    """
    Executes commands (sync or async) with concurrent batch support.

    Sync commands are run in a thread pool to avoid blocking the event loop.
    Async commands are awaited directly.
    """

    def __init__(self, max_workers: int = 20):
        """
        Initialize executor.

        Args:
            max_workers: Maximum number of worker threads for sync operations
        """
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._shutdown = False

    async def execute_sync(self, command: Callable) -> Any:
        """
        Execute a synchronous command in thread pool.

        Args:
            command: Sync callable to execute

        Returns:
            Result of command execution

        Raises:
            Exception: Any exception raised by command
        """
        if self._shutdown:
            raise RuntimeError("Executor has been shutdown")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, command)

    async def execute_async(self, command: Callable) -> Any:
        """
        Execute an asynchronous command.

        Args:
            command: Async callable to execute

        Returns:
            Result of command execution

        Raises:
            Exception: Any exception raised by command
        """
        if self._shutdown:
            raise RuntimeError("Executor has been shutdown")

        return await command()

    async def execute_sync_batch(self, commands: List[Callable]) -> List[Any]:
        """
        Execute multiple sync commands concurrently in thread pool.

        Args:
            commands: List of sync callables

        Returns:
            List of results (or exceptions if return_exceptions=True)
        """
        if self._shutdown:
            raise RuntimeError("Executor has been shutdown")

        tasks = [self.execute_sync(cmd) for cmd in commands]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def execute_async_batch(self, commands: List[Callable]) -> List[Any]:
        """
        Execute multiple async commands concurrently.

        Args:
            commands: List of async callables

        Returns:
            List of results (or exceptions if return_exceptions=True)
        """
        if self._shutdown:
            raise RuntimeError("Executor has been shutdown")

        tasks = [self.execute_async(cmd) for cmd in commands]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown executor and thread pool.

        Args:
            wait: Whether to wait for pending tasks to complete
        """
        self._shutdown = True
        self.thread_pool.shutdown(wait=wait)
        logger.info("Executor shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False
