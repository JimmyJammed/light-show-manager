#!/usr/bin/env python3
"""
Example demonstrating the can_run hook for conditional show execution.

Shows how to control when shows can run based on:
- Time of day
- Day of week
- Custom conditions
"""
import asyncio
from datetime import datetime, time as dt_time
from lightshow import Show, LightShowManager


# ========== EXAMPLE 1: Time-Based Restrictions ==========

def check_time_range(show, context):
    """Only allow shows between 6 PM and 11 PM."""
    current_time = datetime.now().time()
    start_time = dt_time(18, 0)  # 6:00 PM
    end_time = dt_time(23, 0)    # 11:00 PM

    if start_time <= current_time <= end_time:
        return (True, f"Within allowed time ({current_time.strftime('%H:%M')})")
    else:
        return (False, f"Outside allowed hours (6 PM - 11 PM), current: {current_time.strftime('%H:%M')}")


# ========== EXAMPLE 2: Day-Based Restrictions ==========

def check_weekend_only(show, context):
    """Only allow shows on weekends."""
    day = datetime.now().weekday()  # 0=Monday, 6=Sunday
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if day >= 5:  # Saturday or Sunday
        return (True, f"Weekend show allowed ({day_names[day]})")
    else:
        return (False, f"Weekday shows disabled ({day_names[day]})")


# ========== EXAMPLE 3: Component Check ==========

class ShowSystem:
    """Mock system with components that can be enabled/disabled."""
    def __init__(self):
        self.lights_enabled = True
        self.audio_enabled = True
        self.effects_enabled = False


def check_components(show, context):
    """Check if required components are enabled."""
    system = context.get("system")
    if not system:
        return (False, "System not provided in context")

    # Check all required components
    if not system.lights_enabled:
        return (False, "Lights are disabled")
    if not system.audio_enabled:
        return (False, "Audio is disabled")

    return (True, "All required components enabled")


# ========== EXAMPLE 4: Custom Logic ==========

def check_custom_conditions(show, context):
    """
    Complex custom logic for show execution.

    Can check anything:
    - Weather conditions
    - Number of viewers
    - System resources
    - External API status
    - etc.
    """
    # Example: Check if show has been run recently
    last_run = context.get("last_run_time")
    if last_run:
        # Don't run same show within 30 minutes
        time_since = (datetime.now() - last_run).total_seconds()
        if time_since < 1800:  # 30 minutes
            return (False, f"Show ran {int(time_since/60)} minutes ago, wait longer")

    # Example: Check custom flag
    force_run = context.get("force_run", False)
    if force_run:
        return (True, "Force run enabled")

    # Example: Check show-specific metadata
    if show.metadata.get("requires_approval") and not context.get("approved"):
        return (False, "Show requires approval")

    return (True, "All custom checks passed")


# ========== EXAMPLE 5: Async Check ==========

async def check_async_conditions(show, context):
    """
    Async can_run check (e.g., check external API).

    Useful for:
    - API calls
    - Database queries
    - Network checks
    """
    # Simulate async check (e.g., API call)
    await asyncio.sleep(0.1)

    # Example: Check external service
    # service_available = await check_service_health()
    service_available = True  # Mock

    if not service_available:
        return (False, "External service unavailable")

    return (True, "External checks passed")


# ========== DEMO ==========

def demo_time_check():
    """Demo: Time-based restrictions."""
    print("\n" + "="*60)
    print("DEMO 1: Time-Based Restrictions")
    print("="*60)

    show = Show("evening_show", duration=5.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show running!"))

    manager = LightShowManager(
        shows=[show],
        can_run=check_time_range  # Only 6 PM - 11 PM
    )

    print("\nAttempting to run show...")
    asyncio.run(manager.run_show("evening_show"))


def demo_component_check():
    """Demo: Component-based restrictions."""
    print("\n" + "="*60)
    print("DEMO 2: Component Check")
    print("="*60)

    # Create mock system
    system = ShowSystem()
    system.lights_enabled = True
    system.audio_enabled = False  # Audio disabled!

    show = Show("full_show", duration=5.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show running!"))

    manager = LightShowManager(
        shows=[show],
        can_run=check_components
    )

    print("\nAttempting to run with audio disabled...")
    asyncio.run(manager.run_show("full_show", context={"system": system}))

    print("\nEnabling audio and trying again...")
    system.audio_enabled = True
    asyncio.run(manager.run_show("full_show", context={"system": system}))


def demo_custom_check():
    """Demo: Custom conditions."""
    print("\n" + "="*60)
    print("DEMO 3: Custom Conditions")
    print("="*60)

    show = Show("special_show", duration=5.0)
    show.metadata["requires_approval"] = True
    show.add_sync_event(0.0, lambda: print("🎭 Show running!"))

    manager = LightShowManager(
        shows=[show],
        can_run=check_custom_conditions
    )

    print("\nAttempting to run without approval...")
    asyncio.run(manager.run_show("special_show", context={"approved": False}))

    print("\nAttempting with approval...")
    asyncio.run(manager.run_show("special_show", context={"approved": True}))


def demo_async_check():
    """Demo: Async can_run check."""
    print("\n" + "="*60)
    print("DEMO 4: Async Check")
    print("="*60)

    show = Show("online_show", duration=5.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show running!"))

    manager = LightShowManager(
        shows=[show],
        can_run=check_async_conditions  # Async check
    )

    print("\nRunning show with async can_run check...")
    asyncio.run(manager.run_show("online_show"))


def demo_no_check():
    """Demo: No can_run check (always runs)."""
    print("\n" + "="*60)
    print("DEMO 5: No Restrictions (Default)")
    print("="*60)

    show = Show("unrestricted_show", duration=5.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show running!"))

    manager = LightShowManager(
        shows=[show]
        # No can_run hook - always returns (True, "No restrictions")
    )

    print("\nRunning show without restrictions...")
    asyncio.run(manager.run_show("unrestricted_show"))


if __name__ == "__main__":
    print("\n🎬 can_run Hook Examples\n")

    # Run all demos
    demo_no_check()
    demo_time_check()
    demo_component_check()
    demo_custom_check()
    demo_async_check()

    print("\n" + "="*60)
    print("✅ All demos complete!")
    print("="*60 + "\n")
