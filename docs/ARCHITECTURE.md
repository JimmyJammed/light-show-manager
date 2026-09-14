# Architecture

Show/Timeline describe ordered commands. Manager owns a task for each run and serializes replacement requests. Executor runs blocking work on a pool and async work on the event loop. Cancellation drains blocking commands before cleanup. Cleanup is shielded from repeated interruption requests. ProcessLock uses flock on Unix and byte-range locks on Windows.

A monotonic clock prevents wall-clock adjustments from moving cues. Commands are sequential between timeline events and concurrent within explicit batches. This favors predictable ordering over unbounded overlapping operations.
