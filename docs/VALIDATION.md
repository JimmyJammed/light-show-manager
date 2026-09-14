# Validation — 2026-09-14

Local macOS arm64 validation. Baseline revision: 75a6ef8fa28fd88a0af794f98ccec2f3ac70b787. Results apply to the 2.0.0 modernization changes in this PR.

| Check | Result |
| --- | --- |
| Python 3.12.13 pytest --no-cov | 105 passed |
| Python 3.13.15 pytest --no-cov | 105 passed |
| Python 3.14.6 pytest --no-cov | 105 passed |
| Ruff: changed core files and lifecycle regressions | Passed |
| compileall: lightshow and examples | Passed |
| python -m build --no-isolation | Wheel and source distribution built |
| Wheel installed in a fresh virtual environment | Passed |
| python -m lightshow outside checkout | Passed |
| Mixed sync/async and restoration examples against installed wheel | Passed |

Tests include kernel lock contention across processes, cancellation during blocking commands, replacement waiting for cleanup, repeated runs, and injected-clock timing. Simulated time proves scheduling logic, not real-world latency.

Windows/Linux kernel locking and real audio/hardware were not run on this Mac. These are unverified, not test failures. No hosted Actions result is claimed. No registry publication was performed.
