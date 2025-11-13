#!/usr/bin/env python3
"""
Custom audio backend example.

Demonstrates how to implement a custom AudioBackend
for specialized audio requirements.
"""
import asyncio
from pathlib import Path
from lightshow import LightShowManager, Show
from lightshow.audio import AudioPlayer, AudioBackend


class CustomAudioBackend(AudioBackend):
    """
    Custom audio backend example.

    This could be replaced with any audio system:
    - Hardware audio player
    - Network audio streaming
    - Multi-channel audio output
    - Custom audio processing
    """

    def __init__(self):
        """Initialize custom backend."""
        self._is_playing = False
        self._volume = 1.0
        self._current_file = None
        print("🎵 Custom audio backend initialized")

    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0) -> None:
        """Play audio file (custom implementation)."""
        self._current_file = filepath
        self._volume = volume
        self._is_playing = True
        print(f"   ▶️  Playing: {filepath.name} (vol={volume:.1f}, loops={loops})")

        # Your custom audio implementation here
        # Example: send command to hardware audio player
        # self.hardware_player.play(filepath)

    def stop(self) -> None:
        """Stop audio playback."""
        self._is_playing = False
        print(f"   ⏹️  Stopped: {self._current_file.name if self._current_file else 'N/A'}")

        # Your custom stop implementation here
        # self.hardware_player.stop()

    def pause(self) -> None:
        """Pause audio playback."""
        print(f"   ⏸️  Paused")
        # Your custom pause implementation here

    def resume(self) -> None:
        """Resume audio playback."""
        print(f"   ▶️  Resumed")
        # Your custom resume implementation here

    def set_volume(self, volume: float) -> None:
        """Set playback volume."""
        self._volume = volume
        print(f"   🔊 Volume: {volume:.1f}")
        # Your custom volume implementation here

    def is_playing(self) -> bool:
        """Check if audio is playing."""
        return self._is_playing

    def get_position(self) -> float:
        """Get playback position."""
        return 0.0  # Your implementation here


def main():
    """Run custom backend example."""
    print("Custom Audio Backend Example")
    print("=" * 50)

    # Create audio player with custom backend
    custom_backend = CustomAudioBackend()
    audio = AudioPlayer(audio_dir="audio", backend=custom_backend)

    # Create show
    show = Show(name="custom_audio", duration=10.0)

    # Add audio events
    show.add_sync_event(0.0, lambda: audio.play("song.mp3", volume=0.8))
    show.add_sync_event(2.0, lambda: audio.set_volume(1.0))
    show.add_sync_event(5.0, lambda: audio.pause())
    show.add_sync_event(6.0, lambda: audio.resume())
    show.add_sync_event(8.0, lambda: audio.set_volume(0.3))
    show.add_sync_event(9.5, lambda: audio.stop())

    # Create manager
    manager = LightShowManager(
        shows=[show], post_show=lambda s, c: audio.stop()
    )

    # Run show
    print("\n▶️  Running show with custom backend...\n")
    asyncio.run(manager.run_show("custom_audio"))
    print("\n✅ Demo complete!\n")


if __name__ == "__main__":
    main()
