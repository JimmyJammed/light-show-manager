"""
Main LightShowManager class for orchestrating light shows.

Manages show execution with lifecycle hooks and graceful shutdown.
"""
import asyncio
import signal
import logging
import time
from typing import Dict, Optional, Callable, List, Any
from dataclasses import dataclass

from lightshow.show import Show
from lightshow.executor import Executor
from lightshow.timeline import TimelineEvent
from lightshow.exceptions import (
    ShowNotFoundError,
    EventExecutionError,
    ShowInterruptedError
)

logger = logging.getLogger(__name__)


@dataclass
class LifecycleHooks:
    """
    Container for lifecycle hook callbacks.

    All hooks receive the show object and optional context dict.
    Hooks can be sync or async functions.
    """
    pre_show: Optional[Callable] = None
    post_show: Optional[Callable] = None
    on_event: Optional[Callable] = None
    on_error: Optional[Callable] = None


class LightShowManager:
    """
    Manages execution of light shows with lifecycle hooks.

    Features:
    - Pre/post show hooks (always run)
    - Per-event callbacks
    - Error handling with hooks
    - Graceful shutdown (Ctrl+C)
    - Show rotation support
    - Concurrent event execution

    Example:
        manager = LightShowManager(
            shows=[show1, show2],
            pre_show=setup_function,
            post_show=cleanup_function
        )

        await manager.run_show("demo")
    """

    def __init__(
        self,
        shows: Optional[List[Show]] = None,
        pre_show: Optional[Callable] = None,
        post_show: Optional[Callable] = None,
        on_event: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        max_workers: int = 20,
        time_precision: float = 0.05,
        log_level: str = "INFO"
    ):
        """
        Initialize Light Show Manager.

        Args:
            shows: List of Show objects to manage
            pre_show: Callback before each show (receives: show, context)
            post_show: Callback after each show (ALWAYS runs, receives: show, context)
            on_event: Callback when each event fires (receives: event, show, context)
            on_error: Callback on error (receives: error, event/show, context)
            max_workers: Max concurrent workers for sync operations
            time_precision: Scheduling precision in seconds (default: 50ms)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.shows: Dict[str, Show] = {}
        if shows:
            for show in shows:
                self.shows[show.name] = show

        self.hooks = LifecycleHooks(
            pre_show=pre_show,
            post_show=post_show,
            on_event=on_event,
            on_error=on_error
        )

        self.executor = Executor(max_workers=max_workers)
        self.time_precision = time_precision

        # State management
        self._running = False
        self._current_show: Optional[Show] = None
        self._interrupted = False

        # Configure logging
        log_level_num = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level_num,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        logger.setLevel(log_level_num)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    # ========== SHOW MANAGEMENT ==========

    def add_show(self, show: Show) -> None:
        """Add a show to the manager."""
        self.shows[show.name] = show
        logger.info(f"Added show: {show.name}")

    def get_show(self, name: str) -> Show:
        """
        Get show by name.

        Raises:
            ShowNotFoundError: If show not found
        """
        if name not in self.shows:
            raise ShowNotFoundError(name)
        return self.shows[name]

    def remove_show(self, name: str) -> None:
        """Remove show from manager."""
        if name in self.shows:
            del self.shows[name]
            logger.info(f"Removed show: {name}")

    @property
    def show_names(self) -> List[str]:
        """Get list of all show names."""
        return list(self.shows.keys())

    # ========== SHOW EXECUTION ==========

    async def run_show(
        self,
        name: str,
        context: Optional[dict] = None
    ) -> None:
        """
        Run a specific show.

        Args:
            name: Show name
            context: Optional context dict passed to all hooks

        Raises:
            ShowNotFoundError: If show not found
            ShowInterruptedError: If show interrupted
        """
        show = self.get_show(name)
        context = context or {}

        self._running = True
        self._current_show = show
        self._interrupted = False

        logger.info(f"Starting show: {show.name}")

        try:
            # PRE-SHOW HOOK
            if self.hooks.pre_show:
                logger.debug("Running pre-show hook")
                await self._run_hook(self.hooks.pre_show, show, context)

            # RUN TIMELINE
            await self._run_timeline(show, context)

            logger.info(f"Show completed: {show.name}")

        except KeyboardInterrupt:
            logger.warning(f"Show interrupted by user: {show.name}")
            self._interrupted = True
            raise ShowInterruptedError(show.name, "User interrupt (Ctrl+C)")

        except Exception as e:
            logger.error(f"Show error: {show.name} - {e}", exc_info=True)

            # ERROR HOOK
            if self.hooks.on_error:
                try:
                    await self._run_hook(self.hooks.on_error, e, show, context)
                except Exception as hook_error:
                    logger.error(f"Error hook failed: {hook_error}", exc_info=True)

            raise

        finally:
            # POST-SHOW HOOK (ALWAYS RUNS)
            if self.hooks.post_show:
                logger.debug("Running post-show hook")
                try:
                    await self._run_hook(self.hooks.post_show, show, context)
                except Exception as hook_error:
                    logger.error(f"Post-show hook failed: {hook_error}", exc_info=True)

            self._running = False
            self._current_show = None

    async def run_rotation(
        self,
        show_names: List[str],
        repeat: bool = False,
        context: Optional[dict] = None
    ) -> None:
        """
        Run shows in rotation.

        Args:
            show_names: List of show names to run in order
            repeat: If True, loop forever
            context: Optional context dict

        Example:
            await manager.run_rotation(["show1", "show2", "show3"])
        """
        context = context or {}
        iteration = 0

        while True:
            iteration += 1
            logger.info(f"Starting rotation iteration {iteration}")

            for name in show_names:
                if self._interrupted:
                    logger.info("Rotation interrupted")
                    return

                await self.run_show(name, context)

            if not repeat:
                break

            logger.info(f"Rotation iteration {iteration} complete")

    # ========== CONTROL METHODS ==========

    def stop(self) -> None:
        """
        Stop the currently running show gracefully.

        Post-show hook will still run for cleanup.
        """
        if self._running:
            logger.info(f"Stopping show: {self._current_show.name if self._current_show else 'unknown'}")
            self._running = False
        else:
            logger.warning("No show is currently running")

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signals (Ctrl+C, SIGTERM)."""
        logger.warning("\nReceived interrupt signal, stopping gracefully...")
        self._interrupted = True
        self.stop()

    # ========== INTERNAL EXECUTION ==========

    async def _run_timeline(self, show: Show, context: dict) -> None:
        """Execute show timeline with precise timing."""
        events = show.get_events()

        if not events:
            logger.warning(f"Show '{show.name}' has no events")
            return

        start_time = time.time()

        for event in events:
            if not self._running or self._interrupted:
                logger.info("Timeline execution stopped")
                break

            # Wait until event timestamp
            current_time = time.time() - start_time
            wait_time = event.timestamp - current_time

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # Execute event
            try:
                await self._execute_event(event, show, context)

                # ON-EVENT HOOK
                if self.hooks.on_event:
                    try:
                        await self._run_hook(self.hooks.on_event, event, show, context)
                    except Exception as hook_error:
                        logger.error(f"Event hook failed: {hook_error}", exc_info=True)

            except Exception as e:
                error = EventExecutionError(event.description, e)
                logger.error(f"Event execution failed: {error}")

                # ERROR HOOK
                if self.hooks.on_error:
                    try:
                        await self._run_hook(self.hooks.on_error, error, event, show, context)
                    except Exception as hook_error:
                        logger.error(f"Error hook failed: {hook_error}", exc_info=True)

                # Re-raise to stop show
                raise error

    async def _execute_event(
        self,
        event: TimelineEvent,
        show: Show,
        context: dict
    ) -> None:
        """Execute a single event (sync or async, single or batch)."""
        logger.debug(
            f"Executing event at {event.timestamp}s: {event.description} "
            f"(type: {'async' if event.is_async else 'sync'}, "
            f"batch: {event.is_batch})"
        )

        if event.is_batch:
            # Execute batch
            if event.is_async:
                results = await self.executor.execute_async_batch(event.commands)
            else:
                results = await self.executor.execute_sync_batch(event.commands)

            # Check for exceptions in batch
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch command {i} failed: {result}")
                    raise result

        else:
            # Execute single command
            if event.is_async:
                await self.executor.execute_async(event.command)
            else:
                await self.executor.execute_sync(event.command)

    async def _run_hook(self, hook: Callable, *args, **kwargs) -> None:
        """
        Run a lifecycle hook (sync or async).

        Automatically detects if hook is async and handles accordingly.
        """
        if asyncio.iscoroutinefunction(hook):
            # Async hook - await it
            await hook(*args, **kwargs)
        else:
            # Sync hook - run in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: hook(*args, **kwargs))

    # ========== CLEANUP ==========

    def shutdown(self) -> None:
        """Shutdown manager and executor."""
        logger.info("Shutting down Light Show Manager")
        self.stop()
        self.executor.shutdown()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False
