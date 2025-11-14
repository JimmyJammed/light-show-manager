# Process Lock Guide

## Preventing Duplicate Instances

The ProcessLock prevents multiple instances of your light show from running simultaneously across different terminal windows or processes.

## Quick Start

Add this to your `main.py` or `__main__.py`:

```python
from lightshow import ProcessLock, ProcessLockError

# At the start of your application
lock = ProcessLock("starcourt")  # Use your app name

try:
    # Check if already running (optional, for nicer message)
    if lock.is_locked():
        print("\n⚠️  Light show is already running!")
        print("   Only one instance can run at a time.\n")
        sys.exit(0)

    # Acquire the lock
    lock.acquire()

    # Your application code here
    await manager.run_show("my_show")

except ProcessLockError as e:
    print(f"\n❌ Cannot start: {e}\n")
    sys.exit(1)

finally:
    # Always release on exit
    lock.release()
```

## Recommended Pattern (Context Manager)

This is the cleanest approach - the lock is automatically released:

```python
from lightshow import ProcessLock, ProcessLockError

try:
    with ProcessLock("starcourt"):
        # Your entire application runs here
        await manager.run_show("my_show")

except ProcessLockError as e:
    print(f"\n❌ Another instance is already running!")
    print(f"   {e}\n")
    sys.exit(1)
```

## Integration with argparse

For CLI applications with argparse:

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", required=True)
    args = parser.parse_args()

    # Acquire process lock BEFORE running show
    try:
        with ProcessLock("starcourt"):
            manager = LightShowManager(shows=shows)
            asyncio.run(manager.run_show(args.show))

    except ProcessLockError:
        print("\n⚠️  Light show is already running!")
        print("   Only one instance can run at a time.")
        print("   Wait for the current show to finish.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## What This Prevents

**Without ProcessLock:**
```bash
Terminal 1: python3 starcourt/main.py --show starcourt
Terminal 2: python3 starcourt/main.py --show starcourt
# ❌ Both shows run simultaneously! Audio overlaps, lights conflict
```

**With ProcessLock:**
```bash
Terminal 1: python3 starcourt/main.py --show starcourt
# ✅ Show runs

Terminal 2: python3 starcourt/main.py --show starcourt
# ❌ Immediately exits with error message
#    "Another instance is already running (PID: 12345)"
```

## Lock File Location

By default, lock files are created in:
- Unix/macOS: `/tmp/starcourt.lock`
- Windows: `C:\Users\YourName\AppData\Local\Temp\starcourt.lock`

### Custom Lock Directory

You can specify a custom directory:

```python
from pathlib import Path

lock_dir = Path.home() / ".starcourt" / "locks"
lock_dir.mkdir(parents=True, exist_ok=True)

with ProcessLock("starcourt", lock_dir=lock_dir):
    # Your code
    pass
```

## Handling Stale Locks

If your application crashes, the lock file might remain. ProcessLock automatically detects and cleans up stale locks (where the process no longer exists).

However, if you need to manually remove a stale lock:

```bash
# Find the lock file
ls /tmp/*.lock

# Remove it
rm /tmp/starcourt.lock
```

The error message includes the lock file path for easy removal.

## Advanced: Different Locks for Different Shows

If you want multiple shows to be able to run simultaneously but prevent duplicates of the SAME show:

```python
# Use the show name in the lock
show_name = args.show

try:
    with ProcessLock(f"starcourt_{show_name}"):
        await manager.run_show(show_name)

except ProcessLockError:
    print(f"\n⚠️  Show '{show_name}' is already running!")
    sys.exit(1)
```

This allows:
- ✅ `starcourt` and `demo` to run simultaneously
- ❌ Two instances of `starcourt` to run simultaneously

## Error Messages

The ProcessLock provides clear error messages:

```
❌ Another instance is already running (PID: 12345).
   If this is incorrect, remove lock file: /tmp/starcourt.lock
```

The PID (Process ID) helps you identify which process is holding the lock:

```bash
# Check if process is still running
ps aux | grep 12345
```

## Complete Example

See `examples/process_lock_example.py` for a complete working example with multiple patterns.

## Testing

To test that it works, try running your application in two terminals:

```bash
# Terminal 1
python3 starcourt/main.py --show starcourt
# Show starts running...

# Terminal 2 (while Terminal 1 is still running)
python3 starcourt/main.py --show starcourt
# Should immediately fail with error message
```

## Comparison with In-Process Locking

| Feature | In-Process (interrupt=True) | Process Lock |
|---------|----------------------------|--------------|
| **Scope** | Within single Python process | Across all processes |
| **Use Case** | Prevent concurrent shows in same script | Prevent running same script twice |
| **Example** | `manager.run_show("show2", interrupt=True)` | `with ProcessLock("app"):` |
| **Prevents** | Two shows running at same time in one process | Same script running in multiple terminals |

**Use both together** for complete protection:
- ProcessLock: Prevents duplicate script instances
- interrupt=True: Allows priority shows to take over within the same instance
