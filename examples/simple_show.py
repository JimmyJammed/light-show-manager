#!/usr/bin/env python3
"""
Simple light show example demonstrating sync events.

This example shows basic usage with synchronous commands.
"""
import asyncio
import time
from lightshow import LightShowManager, Show


# Define your device control functions
def turn_on_lights():
    """Sync function - runs in thread pool."""
    print(f"[{time.time():.2f}] Lights ON")
    time.sleep(0.1)  # Simulate hardware delay


def turn_off_lights():
    """Sync function - runs in thread pool."""
    print(f"[{time.time():.2f}] Lights OFF")


def play_music():
    """Sync function - runs in thread pool."""
    print(f"[{time.time():.2f}] Playing music...")


def stop_music():
    """Sync function - runs in thread pool."""
    print(f"[{time.time():.2f}] Stopping music")


# Create a show
demo_show = Show(name="demo", duration=10.0, description="Simple demo show")

# Add SYNC events using add_sync_event()
demo_show.add_sync_event(0.0, play_music, "Start music")
demo_show.add_sync_event(1.0, turn_on_lights, "Turn on lights")
demo_show.add_sync_event(8.0, turn_off_lights, "Turn off lights")
demo_show.add_sync_event(9.0, stop_music, "Stop music")

# Add SYNC batch (all fire simultaneously)
demo_show.add_sync_batch(
    5.0,
    [
        lambda: print("[BATCH] Command 1"),
        lambda: print("[BATCH] Command 2"),
        lambda: print("[BATCH] Command 3"),
    ],
    description="Synchronized batch"
)


# Define lifecycle hooks
def pre_show(show, context):
    """Pre-show setup (runs before show starts)."""
    print(f"\n{'='*50}")
    print(f"PRE-SHOW: Setting up for '{show.name}'")
    print(f"{'='*50}\n")


def post_show(show, context):
    """Post-show cleanup (ALWAYS runs, even on error/interrupt)."""
    print(f"\n{'='*50}")
    print(f"POST-SHOW: Cleaning up after '{show.name}'")
    print(f"{'='*50}\n")


def on_event(event, show, context):
    """Called after each event fires."""
    print(f"  → Event completed: {event.description}")


# Create manager
manager = LightShowManager(
    shows=[demo_show],
    pre_show=pre_show,
    post_show=post_show,
    on_event=on_event,
    log_level="INFO"
)

# Run show
print("Starting demo show...")
print("Press Ctrl+C to interrupt (post_show will still run)\n")

asyncio.run(manager.run_show("demo"))

print("\nDemo complete!")
