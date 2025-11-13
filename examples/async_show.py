#!/usr/bin/env python3
"""
Async light show example demonstrating async events.

This example shows usage with asynchronous commands.
"""
import asyncio
import time
from lightshow import LightShowManager, Show


# Define async device control functions
async def async_play_music():
    """Async function - awaited directly."""
    print(f"[{time.time():.2f}] Async: Playing music...")
    await asyncio.sleep(0.1)  # Simulate async I/O
    print(f"[{time.time():.2f}] Async: Music started")


async def async_lights_on():
    """Async function - awaited directly."""
    print(f"[{time.time():.2f}] Async: Turning lights on...")
    await asyncio.sleep(0.05)
    print(f"[{time.time():.2f}] Async: Lights on")


async def async_lights_off():
    """Async function - awaited directly."""
    print(f"[{time.time():.2f}] Async: Turning lights off...")
    await asyncio.sleep(0.05)
    print(f"[{time.time():.2f}] Async: Lights off")


# Create show
async_show = Show(name="async_demo", duration=10.0, description="Async demo show")

# Add ASYNC events using add_async_event()
async_show.add_async_event(0.0, async_play_music, "Start music")
async_show.add_async_event(2.0, async_lights_on, "Lights on")
async_show.add_async_event(7.0, async_lights_off, "Lights off")

# Add ASYNC batch (all await concurrently)
async def async_cmd1():
    print("[ASYNC BATCH] Command 1")
    await asyncio.sleep(0.1)

async def async_cmd2():
    print("[ASYNC BATCH] Command 2")
    await asyncio.sleep(0.1)

async def async_cmd3():
    print("[ASYNC BATCH] Command 3")
    await asyncio.sleep(0.1)

async_show.add_async_batch(
    5.0,
    [async_cmd1, async_cmd2, async_cmd3],
    description="Async batch"
)


# Lifecycle hooks (can be sync or async)
async def async_pre_show(show, context):
    """Async pre-show hook."""
    print(f"\n{'='*50}")
    print(f"ASYNC PRE-SHOW: Setting up '{show.name}'")
    await asyncio.sleep(0.1)
    print(f"{'='*50}\n")


def sync_post_show(show, context):
    """Sync post-show hook (still works!)."""
    print(f"\n{'='*50}")
    print(f"SYNC POST-SHOW: Cleaning up '{show.name}'")
    print(f"{'='*50}\n")


# Create manager
manager = LightShowManager(
    shows=[async_show],
    pre_show=async_pre_show,  # Async hook
    post_show=sync_post_show,  # Sync hook (mixed!)
    log_level="INFO"
)

# Run show
print("Starting async demo show...\n")
asyncio.run(manager.run_show("async_demo"))
print("\nAsync demo complete!")
