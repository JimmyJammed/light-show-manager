"""Deterministic audio substitute for examples and device-free testing."""

import time

from .audio_player import AudioBackend


class SilentBackend(AudioBackend):
    def __init__(self):
        self._playing = False
        self._position = 0.0
        self._started = 0.0
        self.volume = 1.0

    def play(self, filepath, volume=1.0, loops=0):
        self._position = 0.0
        self._started = time.monotonic()
        self.volume = volume
        self._playing = True

    def stop(self):
        self._playing = False
        self._position = 0.0

    def pause(self):
        self._position = self.get_position()
        self._playing = False

    def resume(self):
        self._started = time.monotonic()
        self._playing = True

    def set_volume(self, volume):
        if not 0 <= volume <= 1:
            raise ValueError("Volume must be between zero and one")
        self.volume = volume

    def is_playing(self):
        return self._playing

    def get_position(self):
        return self._position + (time.monotonic() - self._started if self._playing else 0)
