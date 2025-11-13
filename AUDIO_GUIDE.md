# Audio Support Guide

Light Show Manager includes built-in audio playback support for synchronizing audio with your shows.

## Quick Start

### Installation

Install with audio support:
```bash
pip install light-show-manager[audio]
```

This includes the `pygame` library for cross-platform audio playback.

### Basic Usage

```python
from lightshow import Show, LightShowManager
from lightshow.audio import AudioPlayer
import asyncio

# Initialize audio player
audio = AudioPlayer(audio_dir="audio")

# Create show
show = Show("my_show", duration=30.0)

# Add audio events
show.add_sync_event(0.0, lambda: audio.play("song.mp3"))
show.add_sync_event(25.0, lambda: audio.set_volume(0.3))  # Fade out
show.add_sync_event(29.0, lambda: audio.stop())

# Run with cleanup
manager = LightShowManager(
    shows=[show],
    post_show=lambda s, c: audio.stop()  # Always stop audio
)

asyncio.run(manager.run_show("my_show"))
```

## Platform Support

### macOS (Development)
- **Output**: Built-in speakers (default)
- **Setup**: No configuration needed
- **Backend**: pygame (auto-detected)

### Raspberry Pi (Production)
- **Output**: Configurable (e.g., Amp4 Pro)
- **Setup**: Configure ALSA (see below)
- **Backend**: pygame (auto-detected)

#### Raspberry Pi Audio Configuration

1. **Find your audio device**:
   ```bash
   aplay -l
   ```

2. **Set default output** (one-time setup):
   ```bash
   sudo nano /etc/asound.conf
   ```

   Add:
   ```
   pcm.!default {
       type hw
       card 0  # Your audio device card number
   }
   ```

3. **Test**:
   ```bash
   speaker-test -t wav -c 2
   ```

## API Reference

### AudioPlayer

```python
from lightshow.audio import AudioPlayer

# Initialize with custom directory
audio = AudioPlayer(audio_dir="path/to/audio")

# Basic playback
audio.play("song.mp3")
audio.play("song.mp3", volume=0.8, loops=2)

# Control
audio.pause()
audio.resume()
audio.stop()

# Volume control
audio.set_volume(0.5)  # 50% volume

# Status
if audio.is_playing():
    print(f"Position: {audio.get_position()}s")
```

### Async Usage

```python
# Use async methods for non-blocking playback
show.add_async_event(0.0, lambda: audio.play_async("song.mp3"))

# Or fade volume asynchronously
show.add_async_event(
    10.0,
    lambda: audio.fade_volume_async(target_volume=0.0, duration=5.0)
)
```

## Custom Audio Backends

Implement your own audio system by subclassing `AudioBackend`:

```python
from lightshow.audio import AudioBackend, AudioPlayer
from pathlib import Path

class MyAudioBackend(AudioBackend):
    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0):
        # Your implementation (hardware player, network streaming, etc.)
        pass

    def stop(self):
        # Your implementation
        pass

    # ... implement other methods ...

# Use custom backend
audio = AudioPlayer(audio_dir="audio", backend=MyAudioBackend())
```

## Examples

### Example 1: Simple Audio Show

```python
from lightshow import Show, LightShowManager
from lightshow.audio import AudioPlayer
import asyncio

audio = AudioPlayer(audio_dir="audio")

show = Show("concert", duration=180.0)
show.add_sync_event(0.0, lambda: audio.play("song.mp3"))
show.add_sync_event(175.0, lambda: audio.set_volume(0.3))  # Fade

manager = LightShowManager(
    shows=[show],
    post_show=lambda s, c: audio.stop()
)

asyncio.run(manager.run_show("concert"))
```

### Example 2: Audio + Lights

```python
from lightshow import Show, LightShowManager
from lightshow.audio import AudioPlayer
from govee import GoveeClient
import asyncio

# Setup
audio = AudioPlayer(audio_dir="audio")
govee = GoveeClient(api_key="...", prefer_lan=True)
govee.load_devices("devices.json")
devices = govee.get_all_devices()

# Create show
show = Show("light_show", duration=60.0)

# Audio
show.add_sync_event(0.0, lambda: audio.play("theme.mp3"))

# Lights synchronized with audio
show.add_sync_event(2.0, lambda: govee.power_all(devices, True))
show.add_sync_event(5.0, lambda: govee.set_color_all(devices, (255, 0, 0)))
show.add_sync_event(10.0, lambda: govee.set_color_all(devices, (0, 255, 0)))
show.add_sync_event(15.0, lambda: govee.set_color_all(devices, (0, 0, 255)))

# Fade out audio and lights
show.add_sync_event(55.0, lambda: audio.set_volume(0.5))
show.add_sync_event(58.0, lambda: audio.set_volume(0.2))
show.add_sync_event(59.0, lambda: govee.power_all(devices, False))

# Cleanup
def cleanup(show, ctx):
    audio.stop()
    govee.power_all(devices, False)

manager = LightShowManager(shows=[show], post_show=cleanup)
asyncio.run(manager.run_show("light_show"))
```

### Example 3: Testing Without Audio

```python
from lightshow.audio import AudioPlayer

# Use dummy backend for testing (no actual audio)
audio = AudioPlayer(audio_dir="audio", backend="dummy")

# All operations work but just log (no sound)
audio.play("test.mp3")  # Logs: [DUMMY] Playing: test.mp3
audio.stop()            # Logs: [DUMMY] Stopped
```

## Supported Audio Formats

Via pygame:
- **MP3**: Yes
- **WAV**: Yes
- **OGG**: Yes
- **FLAC**: Limited (depends on system)

## Troubleshooting

### "pygame not found"
```bash
pip install light-show-manager[audio]
# or
pip install pygame
```

### "Audio file not found"
- Check `audio_dir` path
- Ensure file exists in the directory
- Use relative filenames: `audio.play("song.mp3")` not `audio.play("audio/song.mp3")`

### Raspberry Pi: No sound
1. Check ALSA configuration: `aplay -l`
2. Test with: `speaker-test -t wav -c 2`
3. Verify volume: `alsamixer`
4. Check device permissions

### macOS: Choppy audio
- Reduce buffer size (requires pygame init customization)
- Close other audio applications
- Check system audio settings

## Performance Tips

- **Use MP3/OGG** for smaller file sizes
- **WAV files** for lowest latency
- **Pre-load audio** if playing multiple files
- **Use sync events** for simple playback (runs in thread pool)
- **Use async events** for complex audio operations

## Optional: Without Audio Support

If you don't need audio, install without it:
```bash
pip install light-show-manager
```

The package remains dependency-free and audio features are simply not available.

## See Also

- [examples/audio_show.py](examples/audio_show.py) - Complete audio example
- [examples/custom_audio_backend.py](examples/custom_audio_backend.py) - Custom backend example
- [Audio API Documentation](README.md#audio-support)
