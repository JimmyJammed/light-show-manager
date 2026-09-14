# Testing

Install `.[dev]`, then run `python -m pytest`. Lifecycle regression tests exercise cancellation, worker draining, clock injection, cleanup ordering, and process contention. Existing tests cover event construction, batches, audio mocks, and manager behavior.

Run the documented demo from an installed wheel outside the source tree. Test Python 3.12, 3.13, and 3.14. Kernel locking must also be checked on Windows; audio backends need separate physical playback checks. Do not count unavailable environments as passing.
