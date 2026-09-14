"""
Main LightShowManager class for orchestrating light shows.

Manages show execution with lifecycle hooks and graceful shutdown.
"""

import asyncio
import inspect
import logging
import signal
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from lightshow.exceptions import EventExecutionError, ShowNotFoundError
from lightshow.executor import Executor
from lightshow.show import Show
from lightshow.timeline import TimelineEvent

logger = logging.getLogger(__name__)


@dataclass
class LifecycleHooks:
    """
    Container for lifecycle hook callbacks.

    All hooks receive the show object and optional context dict.
    Hooks can be sync or async functions.
    """

    can_run: Callable | None = None
    pre_show: Callable | None = None
    post_show: Callable | None = None
    on_event: Callable | None = None
    on_error: Callable | None = None


@dataclass
class RunResult:
    """Outcome; failures are also raised and available through last_result."""

    name: str
    status: str = "completed"
    errors: list[Exception] = field(default_factory=list)
    reason: str = ""


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
        shows: list[Show] | None = None,
        can_run: Callable | None = None,
        pre_show: Callable | None = None,
        post_show: Callable | None = None,
        on_event: Callable | None = None,
        on_error: Callable | None = None,
        max_workers: int = 20,
        time_precision: float = 0.05,
        log_level: str = "INFO",
        notifier: Any | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable = asyncio.sleep,
    ):
        """
        Initialize Light Show Manager.

        Args:
            shows: List of Show objects to manage
            can_run: Check if show can run (receives: show, context; returns: bool, str)
                     Return (True, "reason") to allow, (False, "reason") to block
                     Default: always returns (True, "No restrictions")
            pre_show: Callback before each show (receives: show, context)
            post_show: Callback after each show (ALWAYS runs, receives: show, context)
            on_event: Callback when each event fires (receives: event, show, context)
            on_error: Callback on error (receives: error, event/show, context)
            max_workers: Max concurrent workers for sync operations
            time_precision: Scheduling precision in seconds (default: 50ms)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            notifier: Optional NotificationManager for event notifications
        """
        self.shows: dict[str, Show] = {}
        if shows:
            for show in shows:
                self.shows[show.name] = show

        self.hooks = LifecycleHooks(
            can_run=can_run,
            pre_show=pre_show,
            post_show=post_show,
            on_event=on_event,
            on_error=on_error,
        )

        self.executor = Executor(max_workers=max_workers)
        self.time_precision = time_precision
        self.notifier = notifier

        # State management
        self._running = False
        self._current_show: Show | None = None
        self._interrupted = False

        self._clock = clock
        self._sleep = sleep
        self._start_lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._closed = False
        self._started = False
        self.last_result: RunResult | None = None
        if time_precision <= 0:
            raise ValueError("time_precision must be positive")

    @contextmanager
    def signal_handlers(self):
        """Opt in from the main thread; restore host signal handlers on exit."""
        previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
        try:
            for signum in previous:
                signal.signal(signum, self._handle_interrupt)
            yield self
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)

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
    def show_names(self) -> list[str]:
        """Get list of all show names."""
        return list(self.shows.keys())

    @property
    def is_running(self) -> bool:
        """Check if a show is currently running."""
        return self._running

    @property
    def current_show_name(self) -> str | None:
        """Get name of currently running show, or None if no show is running."""
        return self._current_show.name if self._current_show else None

    async def stop_current_show(self) -> None:
        """Cancel the active timeline and await its cleanup without a timeout."""
        task = self._task
        if task is None or task.done():
            return
        if task is asyncio.current_task():
            self._interrupted = True
            return
        self.stop()
        await asyncio.shield(task)

    async def run_show(
        self, name: str, context: dict | None = None, interrupt: bool = False
    ) -> RunResult:
        if self._closed:
            raise RuntimeError("Manager is closed")
        show = self.get_show(name)
        context = context if context is not None else {}
        async with self._start_lock:
            if self._task is not None and not self._task.done():
                if not interrupt:
                    return RunResult(name, "blocked", reason="Another show is running")
                await self.stop_current_show()
            self._interrupted = False
            self._running = True
            self._current_show = show
            self._started = False
            task = asyncio.create_task(self._run_owned(show, context))
            self._task = task
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # A canceled caller must not leave hardware or cleanup running behind it.
            if not task.done():
                self.stop()
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
            # Retrieve exceptions, while preserving caller cancellation.
            if not task.cancelled():
                task.exception()
            raise

    async def _run_owned(self, show: Show, context: dict) -> RunResult:
        result = RunResult(show.name)
        self._started = True
        try:
            if self._interrupted:
                raise asyncio.CancelledError
            allowed, reason = await self._check_can_run(show, context)
            if not allowed:
                result.status, result.reason = "blocked", reason
                return result
            if self.notifier:
                self.notifier.notify_show_start(show.name, context)
            if self.hooks.pre_show:
                await self._run_hook(self.hooks.pre_show, show, context)
            await self._run_timeline(show, context)
            if self._interrupted:
                result.status = "interrupted"
        except asyncio.CancelledError:
            result.status = "interrupted"
        except Exception as error:  # noqa: BLE001 - preserve user command failures
            result.status = "failed"
            result.errors.append(error)
            if self.hooks.on_error:
                try:
                    await self._run_hook(self.hooks.on_error, error, show, context)
                except Exception as hook_error:  # noqa: BLE001 - aggregate cleanup failures
                    result.errors.append(hook_error)
        finally:
            # Run cleanup in a separate task so repeated stop requests cannot abort it.
            async def cleanup():
                if result.status != "blocked" and self.hooks.post_show:
                    await self._run_hook(self.hooks.post_show, show, context)

            cleanup_task = asyncio.create_task(cleanup())
            while not cleanup_task.done():
                try:
                    await asyncio.shield(cleanup_task)
                except asyncio.CancelledError:
                    result.status = "interrupted"
                except Exception:  # noqa: BLE001 - retrieved and surfaced below
                    break
            if not cleanup_task.cancelled() and cleanup_task.exception():
                result.errors.append(cleanup_task.exception())
                result.status = "failed"
            self._running = False
            self._current_show = None
            self.last_result = result
        if self.notifier:
            if result.errors:
                self.notifier.notify_show_failed(show.name, str(result.errors[0]))
            elif result.status == "completed":
                self.notifier.notify_show_end(show.name, context)
        if result.errors:
            if len(result.errors) == 1:
                raise result.errors[0]
            raise ExceptionGroup("Show and cleanup failures", result.errors)
        return result

    async def run_rotation(
        self, show_names: list[str], repeat: bool = False, context: dict | None = None
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

    async def run_all_shows(
        self, delay_between: float = 5.0, context: dict | None = None, repeat: bool = False
    ) -> None:
        """
        Run all registered shows sequentially.

        Useful for testing/demo purposes to showcase all shows.

        Args:
            delay_between: Seconds to wait between shows (default: 5.0)
            context: Optional context dict passed to all shows
            repeat: If True, loop through all shows repeatedly

        Example:
            # Run all shows once with 5 second delays
            await manager.run_all_shows()

            # Run all shows repeatedly with 10 second delays
            await manager.run_all_shows(delay_between=10.0, repeat=True)
        """
        if not self.shows:
            logger.warning("No shows registered, cannot run all shows")
            return

        show_names = list(self.shows.keys())
        logger.info(f"Running all {len(show_names)} shows with {delay_between}s delay between")

        context = context or {}
        iteration = 0

        while True:
            iteration += 1
            if repeat:
                logger.info(f"Starting all-shows iteration {iteration}")

            for i, name in enumerate(show_names, 1):
                if self._interrupted:
                    logger.info("All-shows loop interrupted")
                    return

                logger.info(f"[{i}/{len(show_names)}] Running show: {name}")
                await self.run_show(name, context)

                # Add delay between shows (but not after the last show)
                if i < len(show_names) and delay_between > 0:
                    logger.debug(f"Waiting {delay_between}s before next show...")
                    await asyncio.sleep(delay_between)

            if not repeat:
                logger.info(f"Completed all {len(show_names)} shows")
                break

            logger.info(f"All-shows iteration {iteration} complete, repeating...")

    # ========== CONTROL METHODS ==========

    def stop(self) -> None:
        """Request interruption; use stop_current_show to await cleanup."""
        if self._task is not None and not self._task.done() and not self._interrupted:
            self._interrupted = True
            if self._started:
                self._task.cancel()

    def _handle_interrupt(self, signum, frame):
        self.stop()

    # ========== INTERNAL EXECUTION ==========

    async def _run_timeline(self, show: Show, context: dict) -> None:
        """Execute show timeline with precise timing."""
        events = show.get_events()

        start_time = self._clock()

        for event in events:
            if not self._running or self._interrupted:
                logger.info("Timeline execution stopped")
                break

            # Wait until event timestamp
            current_time = self._clock() - start_time
            wait_time = event.timestamp - current_time

            # Sleep in small intervals to check for interrupts frequently
            if wait_time > 0:
                check_interval = self.time_precision  # Check for interrupts every 100ms
                while wait_time > 0 and not self._interrupted:
                    sleep_time = min(wait_time, check_interval)
                    await self._sleep(sleep_time)
                    current_time = self._clock() - start_time
                    wait_time = event.timestamp - current_time

            # Check if interrupted during wait
            if self._interrupted:
                logger.info("Timeline execution stopped")
                break

            # Execute event
            try:
                await self._execute_event(event, show, context)

                # ON-EVENT HOOK
                if self.hooks.on_event:
                    await self._run_hook(self.hooks.on_event, event, show, context)

            except Exception as error:
                raise EventExecutionError(event.description, error) from error

        # Duration includes silence after the final cue, using the same clock.
        remaining = show.duration - (self._clock() - start_time)
        if remaining > 0 and not self._interrupted:
            await self._sleep(remaining)

    async def _execute_event(self, event: TimelineEvent, show: Show, context: dict) -> None:
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

            failures = [r for r in results if isinstance(r, Exception)]
            if failures:
                raise ExceptionGroup("Batch command failures", failures)

        else:
            # Execute single command
            if event.is_async:
                await self.executor.execute_async(event.command)
            else:
                await self.executor.execute_sync(event.command)

    async def _check_can_run(self, show: Show, context: dict) -> tuple[bool, str]:
        """
        Check if show can run using the can_run hook.

        Args:
            show: The show to check
            context: Context dict

        Returns:
            Tuple of (can_run: bool, reason: str)
            - If no hook: (True, "No restrictions")
            - If hook returns bool: (result, "Check passed/failed")
            - If hook returns (bool, str): Use that tuple
        """
        if not self.hooks.can_run:
            return (True, "No restrictions")

        try:
            # Run the hook
            if inspect.iscoroutinefunction(self.hooks.can_run):
                result = await self.hooks.can_run(show, context)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: self.hooks.can_run(show, context))

            # Handle different return types
            if isinstance(result, tuple) and len(result) == 2:
                # Hook returned (bool, str)
                can_run, reason = result
                return (bool(can_run), str(reason))
            elif isinstance(result, bool):
                # Hook returned just bool
                if result:
                    return (True, "Check passed")
                else:
                    return (False, "Check failed")
            else:
                # Invalid return type - treat as True
                logger.warning(
                    f"can_run hook returned invalid type {type(result)}, "
                    "expected (bool, str) or bool. Allowing show to run."
                )
                return (True, "Invalid check result, defaulting to allow")

        except Exception as e:
            logger.exception("can_run hook failed")
            # On error, allow show to run (fail-open)
            return (True, f"Check error (allowing): {e}")

    async def _run_hook(self, hook: Callable, *args, **kwargs) -> None:
        """
        Run a lifecycle hook (sync or async).

        Automatically detects if hook is async and handles accordingly.
        """
        if inspect.iscoroutinefunction(hook):
            # Async hook - await it
            await hook(*args, **kwargs)
        else:
            # Sync hook - run in thread pool
            await self.executor.execute_sync(lambda: hook(*args, **kwargs))

    # ========== CLEANUP ==========

    def shutdown(self) -> None:
        """Shutdown manager and executor."""
        logger.info("Shutting down Light Show Manager")
        if self._running:
            raise RuntimeError("Use await manager.aclose() while a show is running")
        self._closed = True
        self.executor.shutdown()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False

    async def aclose(self):
        await self.stop_current_show()
        self.shutdown()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
