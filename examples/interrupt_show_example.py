#!/usr/bin/env python3
"""
Example demonstrating show interruption and concurrent show prevention.

Shows how the manager:
- Blocks new shows while one is running (by default)
- Allows interrupting current show to start a new one (with interrupt=True)
- Properly runs post_show cleanup when interrupted
"""
import asyncio
from lightshow import Show, LightShowManager


# ========== EXAMPLE 1: Blocking Concurrent Shows (Default) ==========

async def demo_block_concurrent():
    """Demo: By default, new shows are blocked if one is already running."""
    print("\n" + "="*60)
    print("DEMO 1: Blocking Concurrent Shows (Default Behavior)")
    print("="*60)

    show1 = Show("long_show", duration=5.0)
    show1.add_sync_event(0.0, lambda: print("🎭 Long show started"))
    show1.add_sync_event(2.0, lambda: print("🎭 Long show: 2 seconds"))
    show1.add_sync_event(4.0, lambda: print("🎭 Long show: 4 seconds"))

    show2 = Show("short_show", duration=2.0)
    show2.add_sync_event(0.0, lambda: print("⚡ Short show started"))

    manager = LightShowManager(shows=[show1, show2])

    # Start long show in background
    print("\nStarting long_show (5 seconds)...")
    long_show_task = asyncio.create_task(manager.run_show("long_show"))

    # Wait a bit, then try to start short show
    await asyncio.sleep(1.0)
    print("\nTrying to start short_show while long_show is running...")
    await manager.run_show("short_show")  # This will be BLOCKED

    print("\nAs you can see, short_show was blocked!")
    print("Long show is still running...\n")

    # Wait for long show to finish
    await long_show_task
    print("\n✅ Long show completed naturally")


# ========== EXAMPLE 2: Interrupting Current Show ==========

async def demo_interrupt():
    """Demo: Using interrupt=True to stop current show and start new one."""
    print("\n" + "="*60)
    print("DEMO 2: Interrupting Current Show")
    print("="*60)

    show1 = Show("long_show", duration=5.0)
    show1.add_sync_event(0.0, lambda: print("🎭 Long show started"))
    show1.add_sync_event(2.0, lambda: print("🎭 Long show: 2 seconds"))
    show1.add_sync_event(4.0, lambda: print("🎭 Long show: 4 seconds (won't reach here)"))

    show2 = Show("priority_show", duration=2.0)
    show2.add_sync_event(0.0, lambda: print("⚡ Priority show started"))
    show2.add_sync_event(1.0, lambda: print("⚡ Priority show: 1 second"))

    def post_show_hook(show, context):
        print(f"🧹 Cleanup for '{show.name}'")

    manager = LightShowManager(shows=[show1, show2], post_show=post_show_hook)

    # Start long show in background
    print("\nStarting long_show (5 seconds)...")
    long_show_task = asyncio.create_task(manager.run_show("long_show"))

    # Wait a bit, then interrupt with priority show
    await asyncio.sleep(1.0)
    print("\nInterrupting long_show with priority_show...")
    await manager.run_show("priority_show", interrupt=True)

    print("\n✅ Priority show completed")
    print("   Notice: Long show was stopped and cleaned up!")

    # Clean up long show task
    try:
        await long_show_task
    except:
        pass


# ========== EXAMPLE 3: Manual Stop ==========

async def demo_manual_stop():
    """Demo: Manually stopping a running show."""
    print("\n" + "="*60)
    print("DEMO 3: Manually Stopping a Show")
    print("="*60)

    show = Show("stoppable_show", duration=10.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show started"))
    show.add_sync_event(2.0, lambda: print("🎭 2 seconds"))
    show.add_sync_event(4.0, lambda: print("🎭 4 seconds (won't reach here)"))

    def post_show_hook(show, context):
        print(f"🧹 Cleanup for '{show.name}'")

    manager = LightShowManager(shows=[show], post_show=post_show_hook)

    # Start show in background
    print("\nStarting show (10 seconds)...")
    show_task = asyncio.create_task(manager.run_show("stoppable_show"))

    # Wait a bit, then manually stop
    await asyncio.sleep(1.0)
    print("\nManually stopping show after 1 second...")
    await manager.stop_current_show()

    print("\n✅ Show stopped and cleaned up")

    # Clean up task
    try:
        await show_task
    except:
        pass


# ========== EXAMPLE 4: Checking if Show is Running ==========

async def demo_is_running():
    """Demo: Checking if a show is currently running."""
    print("\n" + "="*60)
    print("DEMO 4: Checking Show Status")
    print("="*60)

    show = Show("test_show", duration=2.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show started"))
    show.add_sync_event(1.0, lambda: print("🎭 Show midpoint"))

    manager = LightShowManager(shows=[show])

    print(f"\nIs running? {manager.is_running}")
    print(f"Current show: {manager.current_show_name}")

    # Start show in background
    print("\nStarting show...")
    show_task = asyncio.create_task(manager.run_show("test_show"))

    # Check status while running
    await asyncio.sleep(0.5)
    print(f"\nIs running? {manager.is_running}")
    print(f"Current show: {manager.current_show_name}")

    # Wait for completion
    await show_task

    # Check status after completion
    print(f"\nIs running? {manager.is_running}")
    print(f"Current show: {manager.current_show_name}")

    print("\n✅ Status checking complete")


# ========== RUN ALL DEMOS ==========

async def main():
    """Run all demo examples."""
    print("\n🎬 Show Interruption Examples\n")

    await demo_block_concurrent()
    await demo_interrupt()
    await demo_manual_stop()
    await demo_is_running()

    print("\n" + "="*60)
    print("✅ All demos complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
