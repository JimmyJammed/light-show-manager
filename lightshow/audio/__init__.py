"""
Audio support for light-show-manager.

Provides built-in audio playback with platform detection and
support for custom audio implementations.

Example:
    from lightshow import Show, LightShowManager
    from lightshow.audio import AudioPlayer

    audio = AudioPlayer(audio_dir="audio")

    show = Show("demo", duration=10.0)
    show.add_sync_event(0.0, lambda: audio.play("song.mp3"))

    manager = LightShowManager(
        shows=[show],
        post_show=lambda s, c: audio.stop()
    )
"""

from lightshow.audio.audio_player import AudioPlayer, AudioBackend
from lightshow.audio.afplay_backend import AfplayBackend
from lightshow.audio.exceptions import (
    AudioError,
    AudioNotAvailableError,
    AudioFileNotFoundError,
    AudioBackendError,
)

__all__ = [
    "AudioPlayer",
    "AudioBackend",
    "AfplayBackend",
    "AudioError",
    "AudioNotAvailableError",
    "AudioFileNotFoundError",
    "AudioBackendError",
]
