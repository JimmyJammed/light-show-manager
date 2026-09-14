# Migrating to 2.0

Requires Python 3.12+. Replace fire-and-forget shutdown with `async with LightShowManager(...)` or `await manager.aclose()`. Calling synchronous shutdown during playback now raises.

run_show returns a structured outcome. Errors still raise; last_result records failures. Interruption waits for cleanup rather than proceeding after two seconds. The manager no longer installs signal handlers at construction; opt in with signal_handlers at the application boundary. Global logging belongs to the host application.

Process lock files remain on disk after release. Remove code that interprets their contents or existence as an active lock. Use is_locked or acquire. The OS releases locks when a process exits.

Post-show failures now surface. Batch failures aggregate instead of reporting just the first. on_error receives `(error, show, context)` consistently. Shows honor their declared duration after the final cue. Existing sync/async event builder methods remain supported.
