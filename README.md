# Light Show Manager

[![Tests](https://github.com/JimmyJammed/light-show-manager/actions/workflows/test.yml/badge.svg)](https://github.com/JimmyJammed/light-show-manager/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/light-show-manager.svg)](https://badge.fury.io/py/light-show-manager)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A pure Python framework for orchestrating time-synchronized commands across any hardware or software system.

## Features

- **Timeline-Based**: Schedule events at precise timestamps
- **Sync & Async Support**: Separate methods for sync and async commands
- **Batch Operations**: Execute multiple commands simultaneously
- **Device State Management**: Automatic tracking and restoration of device states
- **Unified Logging**: Color-coded console output and timestamped log files
- **Lifecycle Hooks**: Pre-show setup, post-show cleanup, per-event callbacks
- **Graceful Shutdown**: Always runs cleanup on Ctrl+C or errors
- **Pure Python**: No dependencies (uses stdlib asyncio)
- **Hardware Agnostic**: Works with any devices/APIs/systems

## Installation

```bash
pip install light-show-manager
```

Or for development:

```bash
git clone https://github.com/JimmyJammed/light-show-manager.git
cd light-show-manager
pip install -e .
```

## Quick Start

```python
from lightshow import LightShowManager, Show
import asyncio

# Create a show
show = Show(name="demo", duration=10.0)

# Add SYNC events (run in thread pool)
show.add_sync_event(0.0, lambda: print("Start!"))
show.add_sync_batch(5.0, [cmd1, cmd2, cmd3])

# Add ASYNC events (awaited)
show.add_async_event(2.5, async_function)

# Create manager with lifecycle hooks
manager = LightShowManager(
    shows=[show],
    pre_show=setup,      # Runs before show
    post_show=cleanup    # ALWAYS runs after (even on error/interrupt)
)

# Run show
asyncio.run(manager.run_show("demo"))
```

## Core Concepts

### Sync vs Async - Separate Methods

The package uses **explicit separate methods** to distinguish between sync and async commands:

#### Sync Methods (Thread Pool Execution)
```python
# Single sync event
show.add_sync_event(timestamp, command, description)

# Batch of sync commands (all run concurrently in thread pool)
show.add_sync_batch(timestamp, [cmd1, cmd2, cmd3], description)
```

#### Async Methods (Direct Await)
```python
# Single async event
show.add_async_event(timestamp, async_command, description)

# Batch of async commands (all awaited concurrently)
show.add_async_batch(timestamp, [async1, async2, async3], description)
```

This design makes it **crystal clear** which execution mode you're using - no guessing, no auto-detection ambiguity.

## Complete API

### Creating Shows

```python
from lightshow import Show

show = Show(
    name="my_show",
    duration=180.0,  # 3 minutes
    description="My awesome show"
)
```

### Adding Sync Events

```python
# Sync functions (blocking I/O, GPIO, serial, etc.)
def turn_on_relay():
    GPIO.output(17, HIGH)
    time.sleep(0.1)

# Single event
show.add_sync_event(0.0, turn_on_relay, "Turn on relay")

# Batch (all fire at same time, run concurrently)
show.add_sync_batch(
    5.0,
    [
        lambda: lights1.on(),
        lambda: lights2.on(),
        lambda: motor.start()
    ],
    description="Turn on all devices"
)

# Bulk add
show.add_sync_events([
    (0.0, cmd1, "Event 1"),
    (5.0, cmd2, "Event 2"),
    (10.0, cmd3, "Event 3")
])
```

### Adding Async Events

```python
# Async functions
async def play_audio():
    await audio_player.play("song.mp3")

# Single event
show.add_async_event(0.0, play_audio, "Start music")

# Batch (all await concurrently)
show.add_async_batch(
    10.0,
    [
        async_lights1.on(),
        async_lights2.on(),
        async_audio.play("song.mp3")
    ],
    description="Async batch"
)

# Bulk add
show.add_async_events([
    (0.0, async1, "Event 1"),
    (5.0, async2, "Event 2"),
    (10.0, async3, "Event 3")
])
```

### Lifecycle Hooks

```python
def pre_show(show, context):
    """Setup before show starts."""
    print(f"Starting: {show.name}")
    # Turn off all lights
    # Play intro sound
    # Reset state

def post_show(show, context):
    """Cleanup after show (ALWAYS runs)."""
    print(f"Ending: {show.name}")
    # Turn off all lights
    # Stop motors
    # Restore GPIO states

def on_event(event, show, context):
    """Called after each event fires."""
    print(f"Event: {event.description}")

def on_error(error, event_or_show, context):
    """Called when errors occur."""
    print(f"Error: {error}")

manager = LightShowManager(
    shows=[show],
    pre_show=pre_show,
    post_show=post_show,  # ALWAYS runs
    on_event=on_event,
    on_error=on_error
)
```

**Note**: Hooks can be sync or async functions - the manager handles both automatically!

### Running Shows

```python
# Run single show
await manager.run_show("my_show")

# Run with context (passed to all hooks)
await manager.run_show("my_show", context={"volume": 75})

# Run rotation
await manager.run_rotation(["show1", "show2", "show3"])

# Run forever
await manager.run_rotation(["show1", "show2"], repeat=True)
```

### Graceful Shutdown

The manager automatically handles Ctrl+C and termination signals:

```python
manager = LightShowManager(
    shows=[show],
    post_show=cleanup  # ALWAYS runs, even on Ctrl+C
)

# User presses Ctrl+C during show
# → Show stops gracefully
# → post_show() runs
# → Clean exit
```

## Examples

### Example 1: Simple Sync Show

```python
import asyncio
from lightshow import LightShowManager, Show

# Define sync functions
def lights_on():
    print("Lights ON")

def lights_off():
    print("Lights OFF")

# Create show
show = Show("demo", duration=10.0)
show.add_sync_event(0.0, lights_on)
show.add_sync_event(5.0, lights_off)

# Run
manager = LightShowManager(shows=[show])
asyncio.run(manager.run_show("demo"))
```

### Example 2: Mixed Sync/Async

```python
import asyncio
from lightshow import LightShowManager, Show

# Sync function
def gpio_on():
    GPIO.output(17, HIGH)

# Async function
async def play_audio():
    await audio.play("song.mp3")

# Create show
show = Show("mixed", duration=20.0)
show.add_sync_event(0.0, gpio_on)      # Sync
show.add_async_event(1.0, play_audio)  # Async

# Both work together seamlessly!
manager = LightShowManager(shows=[show])
asyncio.run(manager.run_show("mixed"))
```

### Example 3: Device State Management

Automatically track and restore device states around shows:

```python
import asyncio
from lightshow import LightShowManager, Show, with_device_state_management
from govee import GoveeClient

# Initialize device client
govee_client = GoveeClient(api_key="your-key", prefer_lan=True)

# Create manager
manager = LightShowManager()

# Register state management hooks (once, in main.py)
def save_device_states(devices, context):
    """Save state using your device library."""
    device_client = context.get('device_client')
    if device_client:
        device_client.save_state(devices)

def restore_device_states(devices, context):
    """Restore state using your device library."""
    device_client = context.get('device_client')
    if device_client:
        device_client.restore_state(devices)

manager.hooks.save_device_states = save_device_states
manager.hooks.restore_device_states = restore_device_states

# Use decorator on show builders (automatically tracks device usage)
@with_device_state_management(
    govee_client,
    spotlight_devices=[spotlight1, spotlight2]  # Turn off before show
)
def build_my_show(show_manager, govee_client, config):
    show = show_manager.create_show("my_show", duration=120.0)

    # All device operations are tracked automatically
    await govee_client.apply_scene(garage_lights, scene1)
    await govee_client.set_music_mode(neon_lights, mode_value=1, sensitivity=50)

    return show  # Decorator handles state save/restore!
```

**What it does:**
- Automatically tracks all devices used during show construction
- Saves their state before show starts (via your hook)
- Restores state after show ends (via your hook)
- No manual device lists needed!

### Example 4: Unified Logging

The package includes a color-coded logging system with file output:

```python
from lightshow import Logger, configure_stdlib_logging
import logging

# Initialize logger with file logging
logger = Logger(log_dir="logs")

# Route Python's stdlib logging through lightshow Logger
# (catches logs from third-party libraries like govee-python)
configure_stdlib_logging(logger, level=logging.INFO)

# Use the logger
logger.info("Show system starting...")
logger.warn("Device not responding")
logger.error("Failed to initialize hardware")
logger.debug("Detailed debugging info")

# Console output is color-coded:
# INFO  = White
# WARN  = Yellow
# ERROR = Red
# DEBUG = Cyan

# File output goes to: logs/log_2025_11_13_20_00_00.log
# with caller info for easy debugging:
# 2025-11-13 20:00:00 [INFO] Show starting [main.py:123 in main()]
```

**Benefits:**
- Color-coded console for quick visual scanning
- Timestamped log files for debugging
- Automatic caller information (file, line, function)
- Third-party library integration via stdlib logging bridge
- Respects NO_COLOR environment variable

### Example 5: StrangerCourt Integration

```python
from lightshow import LightShowManager, Show
from govee import GoveeClient
import asyncio

# Initialize hardware
govee = GoveeClient(api_key="...", prefer_lan=True)
govee.load_devices("govee_devices.json")
audio = AudioPlayer()
motor = MotorController()

# Create show
starcourt = Show("starcourt", duration=180.0)

# Add events (all SYNC in this case)
starcourt.add_sync_event(0.0, lambda: audio.play("starcourt.mp3"))

starcourt.add_sync_batch(2.5, [
    lambda: govee.set_color(govee.get_device("Garage Left"), (255, 0, 0)),
    lambda: govee.set_color(govee.get_device("Garage Right"), (0, 0, 255)),
    lambda: govee.set_brightness_all(govee.get_all_devices(), 100)
])

starcourt.add_sync_event(5.0, lambda: motor.set_speed(50))

# Lifecycle hooks
def pre_show(show, context):
    audio.play("powerdown.mp3")
    govee.power_all(govee.get_all_devices(), on=False)

def post_show(show, context):
    govee.power_all(govee.get_all_devices(), on=False)
    motor.stop()
    audio.stop()

# Run
manager = LightShowManager(
    shows=[starcourt],
    pre_show=pre_show,
    post_show=post_show
)

asyncio.run(manager.run_show("starcourt"))
```

## Why Separate Methods?

We chose **explicit separate methods** over auto-detection for clarity:

### ✅ Benefits

1. **Crystal Clear**: No confusion about execution mode
2. **Self-Documenting**: Code shows intent explicitly
3. **IDE Friendly**: Better autocomplete and type hints
4. **No Surprises**: Behavior is predictable
5. **Easy to Learn**: Clear mental model

### ❌ Alternatives Considered

- **Auto-detection**: Requires understanding async introspection
- **Single method with flag**: Easy to forget the flag
- **Wrappers**: Extra boilerplate

## Architecture

```
User Code
    ↓
LightShowManager
    ↓
┌────────────┬──────────────┬───────────────┐
│  Timeline  │   Executor   │   Lifecycle   │
│  (When)    │   (How)      │   (Hooks)     │
└────────────┴──────────────┴───────────────┘
    ↓              ↓                ↓
Commands    Sync: Thread     Pre/Post Show
(Callables)  Async: Await    Event Callbacks
```

## Package Structure

```
light-show-manager/
├── lightshow/
│   ├── __init__.py
│   ├── manager.py          # LightShowManager
│   ├── show.py             # Show class
│   ├── timeline.py         # Timeline, TimelineEvent
│   ├── executor.py         # Async/sync executor
│   └── exceptions.py       # Custom exceptions
│
├── examples/
│   ├── simple_show.py      # Sync example
│   ├── async_show.py       # Async example
│   └── mixed_show.py       # Mixed sync/async
│
└── tests/
```

## Error Handling

```python
from lightshow.exceptions import (
    ShowNotFoundError,
    EventExecutionError,
    ShowInterruptedError
)

try:
    await manager.run_show("my_show")
except ShowNotFoundError:
    print("Show not found")
except EventExecutionError as e:
    print(f"Event failed: {e.event_description}")
except ShowInterruptedError:
    print("Show interrupted by user")
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Inspired by the StrangerCourt Halloween project
- Built for the maker/DIY automation community

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and version history.

### Recent Highlights

- **Logger Module** (Unreleased) - Color-coded console and file logging system
- **Logging Bridge** (Unreleased) - Integrate Python's standard logging with lightshow Logger
- **Device State Management** (0.2.0) - Automatic tracking and restoration decorator
- **Timeline-Based Shows** (0.1.0) - Precise timestamp synchronization

## Support

- GitHub Issues: https://github.com/JimmyJammed/light-show-manager/issues
- GitHub Discussions: https://github.com/JimmyJammed/light-show-manager/discussions
- Documentation: https://github.com/JimmyJammed/light-show-manager#readme
