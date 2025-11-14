#!/usr/bin/env python3
"""
Example demonstrating process-level locking to prevent duplicate instances.

This prevents multiple terminal windows from running the same show simultaneously.
"""
import asyncio
import sys
from lightshow import Show, LightShowManager, ProcessLock, ProcessLockError


# ========== EXAMPLE 1: Basic Usage ==========

def example_basic():
    """Basic process lock usage."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Process Lock")
    print("="*60)

    # Create a lock for your application
    lock = ProcessLock("my_light_show")

    # Try to acquire the lock
    try:
        lock.acquire()
        print("✅ Lock acquired! This instance is running.")

        # Your application code here
        print("   Running show...")
        import time
        time.sleep(2)

        print("   Show complete!")

    except ProcessLockError as e:
        print(f"❌ {e}")
        print("   Another instance is already running.")
        sys.exit(1)

    finally:
        # Always release the lock
        lock.release()
        print("🔓 Lock released")


# ========== EXAMPLE 2: Context Manager (Recommended) ==========

def example_context_manager():
    """Using lock as context manager (automatic cleanup)."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Context Manager (Recommended)")
    print("="*60)

    try:
        # Lock is automatically released when block exits
        with ProcessLock("my_light_show"):
            print("✅ Lock acquired via context manager")
            print("   Running show...")
            import time
            time.sleep(2)
            print("   Show complete!")
        print("🔓 Lock automatically released")

    except ProcessLockError as e:
        print(f"❌ {e}")
        sys.exit(1)


# ========== EXAMPLE 3: Integration with LightShowManager ==========

async def example_with_manager():
    """Using ProcessLock with LightShowManager."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Integration with LightShowManager")
    print("="*60)

    # Create your show
    show = Show("demo", duration=3.0)
    show.add_sync_event(0.0, lambda: print("🎭 Show started"))
    show.add_sync_event(1.0, lambda: print("🎭 1 second"))
    show.add_sync_event(2.0, lambda: print("🎭 2 seconds"))

    # Create manager
    manager = LightShowManager(shows=[show])

    # Use process lock to prevent duplicate instances
    try:
        with ProcessLock("starcourt_show"):  # Use your app name
            print("✅ Process lock acquired")
            print("   Starting light show...")

            await manager.run_show("demo")

            print("   Light show complete!")

    except ProcessLockError as e:
        print(f"❌ {e}")
        print("   Cannot start show - another instance is running")
        sys.exit(1)


# ========== EXAMPLE 4: Graceful Handling ==========

def example_graceful():
    """Gracefully handle duplicate instances."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Graceful Handling")
    print("="*60)

    lock = ProcessLock("my_light_show")

    # Check first without crashing
    if lock.is_locked():
        print("⚠️  Another instance is already running")
        print("   Exiting gracefully...")
        sys.exit(0)

    try:
        lock.acquire()
        print("✅ Lock acquired")

        # Your code here
        import time
        time.sleep(1)

    except ProcessLockError as e:
        # This shouldn't happen since we checked is_locked() first
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    finally:
        lock.release()


# ========== EXAMPLE 5: Custom Lock Directory ==========

def example_custom_directory():
    """Using a custom directory for lock files."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Custom Lock Directory")
    print("="*60)

    from pathlib import Path

    # Store lock files in your app's directory
    lock_dir = Path.home() / ".lightshow" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)

    try:
        with ProcessLock("my_show", lock_dir=lock_dir):
            print(f"✅ Lock acquired in custom directory: {lock_dir}")
            print(f"   Lock file: {lock_dir}/my_show.lock")
            import time
            time.sleep(1)

    except ProcessLockError as e:
        print(f"❌ {e}")
        sys.exit(1)


# ========== EXAMPLE 6: Real Application Template ==========

async def run_application():
    """
    Complete application template with process locking.

    Copy this pattern to your main.py!
    """
    # Create your shows
    show1 = Show("show1", duration=2.0)
    show1.add_sync_event(0.0, lambda: print("🎭 Show 1 running"))

    show2 = Show("show2", duration=2.0)
    show2.add_sync_event(0.0, lambda: print("🎭 Show 2 running"))

    # Create manager
    manager = LightShowManager(shows=[show1, show2])

    # Acquire process lock to prevent duplicate instances
    lock = ProcessLock("starcourt")  # Use your app name

    try:
        # Check if already running (optional, for graceful message)
        if lock.is_locked():
            print("\n⚠️  Starcourt light show is already running!")
            print("   Only one instance can run at a time.")
            print("   If this is incorrect, remove lock file:\n")
            print(f"   rm {lock.lock_file}\n")
            return

        # Acquire lock
        lock.acquire()
        print("✅ Process lock acquired")

        # Run your shows
        await manager.run_show("show1")
        await manager.run_show("show2")

        print("✅ All shows complete")

    except ProcessLockError as e:
        print(f"\n❌ Cannot start: {e}\n")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

    finally:
        # Always release lock on exit
        lock.release()
        print("🔓 Process lock released")


def example_application_template():
    """Show the application template."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Complete Application Template")
    print("="*60)
    print("\n👉 See run_application() function above for complete example")
    print("   This is the recommended pattern for your main.py\n")

    asyncio.run(run_application())


# ========== MAIN ==========

def main():
    """Run all examples."""
    print("\n🔒 Process Lock Examples\n")
    print("These examples show how to prevent duplicate instances")
    print("of your light show from running in multiple terminals.\n")

    # Run examples
    example_basic()
    example_context_manager()
    asyncio.run(example_with_manager())
    example_graceful()
    example_custom_directory()
    example_application_template()

    print("\n" + "="*60)
    print("✅ All examples complete!")
    print("="*60)
    print("\n💡 Tip: Try running this script in two terminals simultaneously")
    print("   to see the lock in action!\n")


if __name__ == "__main__":
    main()
