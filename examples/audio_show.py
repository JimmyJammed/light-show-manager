#!/usr/bin/env python3
"""
Audio light show example.

Demonstrates integration of audio playback with light show timeline.
Works on macOS (built-in speakers) and Raspberry Pi (configured audio output).

Requires: pip install light-show-manager[audio]
"""
import asyncio
from pathlib import Path
from lightshow import LightShowManager, Show
from lightshow.audio import AudioPlayer


# Create an audio directory with a test file
def setup_audio_dir():
    """Create audio directory and check for test files."""
    audio_dir = Path("audio")
    audio_dir.mkdir(exist_ok=True)

    # Check if any audio files exist
    audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav"))

    if not audio_files:
        print("⚠️  No audio files found in 'audio/' directory")
        print("   Please add an MP3 or WAV file to test audio playback")
        print("   Example: audio/test.mp3")
        return None

    return audio_files[0].name


def main():
    """Run audio show example."""
    print("Audio Light Show Example")
    print("=" * 50)

    # Setup audio directory
    audio_file = setup_audio_dir()
    if not audio_file:
        # Use dummy backend for demonstration
        print("\n📢 Running in DEMO mode (no actual audio)")
        audio = AudioPlayer(audio_dir="audio", backend="dummy")
        audio_file = "demo.mp3"  # Dummy file for demo
    else:
        print(f"\n🎵 Found audio file: {audio_file}")
        # Initialize audio player (auto-detects platform)
        audio = AudioPlayer(audio_dir="audio")

    # Create show
    show = Show(name="audio_demo", duration=15.0, description="Audio demonstration")

    # Add audio events
    print("\n📋 Adding show events...")

    # Start audio at beginning
    show.add_sync_event(0.0, lambda: audio.play(audio_file, volume=0.8), "Play audio")

    # Volume changes during show
    show.add_sync_event(3.0, lambda: audio.set_volume(1.0), "Volume to 100%")
    show.add_sync_event(10.0, lambda: audio.set_volume(0.5), "Volume to 50%")
    show.add_sync_event(12.0, lambda: audio.set_volume(0.2), "Volume to 20% (fade out)")

    # Stop at end
    show.add_sync_event(14.5, lambda: audio.stop(), "Stop audio")

    # Lifecycle hooks
    def pre_show(show_obj, context):
        print(f"\n🎬 Starting show: {show_obj.name}")
        print(f"   Duration: {show_obj.duration}s")

    def post_show(show_obj, context):
        print(f"\n🛑 Ending show: {show_obj.name}")
        # Ensure audio is stopped
        audio.stop()

    def on_event(event, show_obj, context):
        print(f"   ⏱️  [{event.timestamp:5.1f}s] {event.description}")

    # Create manager
    manager = LightShowManager(
        shows=[show], pre_show=pre_show, post_show=post_show, on_event=on_event
    )

    # Run show
    print("\n▶️  Running show...")
    print("   (Press Ctrl+C to interrupt)\n")

    try:
        asyncio.run(manager.run_show("audio_demo"))
    except KeyboardInterrupt:
        print("\n\n⏹️  Show interrupted")
        audio.stop()

    print("\n✅ Demo complete!\n")


if __name__ == "__main__":
    main()
