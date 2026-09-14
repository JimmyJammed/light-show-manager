# API

`Show(name, duration, description="", metadata=None)` holds ordered cues. Add functions with `add_sync_event(timestamp, command, description)` or `add_async_event`; batch variants accept lists. A show retains its declared duration including silence after the final cue. Events execute in timestamp order; an overrun delays later cues rather than dropping them.

`LightShowManager(shows, pre_show=None, post_show=None, on_event=None, on_error=None, can_run=None, max_workers=20, time_precision=.05, notifier=None, clock=time.monotonic, sleep=asyncio.sleep)` owns execution. Hooks receive `(show, context)`, except on_event `(event, show, context)` and on_error `(error, show, context)`.

`await run_show(name, context=None, interrupt=False)` returns `RunResult(name, status, errors, reason)`. Status is completed, interrupted, blocked, or failed. A busy manager returns blocked unless interrupt is requested. Failure raises the original exception or an ExceptionGroup; inspect `last_result` after failure. Batch execution drains every command, then aggregates failures and stops the timeline. Cleanup errors are surfaced.

`stop()` requests interruption; `await stop_current_show()` awaits cleanup. Cancellation of the caller propagates only after cleanup finishes. `async with manager` calls `aclose()` automatically. Synchronous shutdown is permitted only when idle. `run_rotation` and `run_all_shows` remain available.

`with manager.signal_handlers()` opts into SIGINT/SIGTERM on the main thread and restores host handlers afterward. Construction does not modify signals or global logging configuration.

`ProcessLock(name, lock_dir=None)` is a context manager. `acquire(timeout=0)` raises on contention; positive timeouts return False when exhausted. Lock files persist; file existence or PID content does not indicate ownership. Never unlink a lock file while another process may be using it.

The legacy can_run hook retains fail-open behavior for errors/invalid responses; return False explicitly to block a show.
