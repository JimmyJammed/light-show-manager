# Getting started

Follow the README virtual-environment commands. Python 3.12 or newer is required. Run `python -m lightshow --duration 2` first. Install `.[audio]` only when using pygame; macOS afplay requires macOS. `lightshow.audio.silent_backend.SilentBackend` simulates audio state without a device. It does not decode audio or simulate track completion.

Run tests using `python -m pytest`. Build distributables with `python -m pip install build` and `python -m build`. Install the generated wheel into another environment to verify consumer behavior.
