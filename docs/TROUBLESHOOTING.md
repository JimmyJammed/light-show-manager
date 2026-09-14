# Troubleshooting

A slow stop normally means an in-flight blocking command or cleanup hook has not finished. Set timeouts in device adapters. Do not start replacement hardware operations before cleanup completes.

A remaining .lock file is normal. Use ProcessLock to check ownership. An active lock on a network filesystem is outside the supported locking contract; use a local filesystem.

Audio installation failures do not affect the core. Start with the silent backend. Import errors usually indicate the wrong virtual environment: inspect `python -m pip show light-show-manager`.
