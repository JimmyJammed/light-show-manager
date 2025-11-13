"""
Process-level locking to prevent duplicate script instances.

Uses a lock file (PID file) to ensure only one instance of the manager runs at a time.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ProcessLockError(Exception):
    """Exception raised when process lock cannot be acquired."""
    pass


class ProcessLock:
    """
    Process-level lock using a PID file.

    Ensures only one instance of the application runs at a time across
    multiple processes/terminals.

    Example:
        # Automatic cleanup on exit
        lock = ProcessLock("myapp")

        # Check if locked
        if lock.is_locked():
            print("Another instance is running")

        # Try to acquire lock
        try:
            lock.acquire()
            # Run your code
        finally:
            lock.release()

        # Or use as context manager
        with ProcessLock("myapp"):
            # Run your code
            pass
    """

    def __init__(self, name: str = "lightshow", lock_dir: Optional[Path] = None):
        """
        Initialize process lock.

        Args:
            name: Unique name for this lock (default: "lightshow")
            lock_dir: Directory for lock file (default: /tmp or system temp dir)
        """
        self.name = name

        # Determine lock directory
        if lock_dir:
            self.lock_dir = Path(lock_dir)
        else:
            # Use /tmp on Unix-like systems, or temp dir on Windows
            if sys.platform == "win32":
                import tempfile
                self.lock_dir = Path(tempfile.gettempdir())
            else:
                self.lock_dir = Path("/tmp")

        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.lock_dir / f"{name}.lock"
        self._locked = False

    def is_locked(self) -> bool:
        """
        Check if lock file exists and process is still running.

        Returns:
            True if another process holds the lock, False otherwise
        """
        if not self.lock_file.exists():
            return False

        try:
            # Read PID from lock file
            pid = int(self.lock_file.read_text().strip())

            # Check if process is still running
            return self._is_process_running(pid)

        except (ValueError, IOError) as e:
            logger.warning(f"Invalid lock file {self.lock_file}: {e}")
            # Invalid lock file - remove it
            try:
                self.lock_file.unlink()
            except:
                pass
            return False

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            # Send signal 0 to check if process exists (doesn't actually send signal)
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def acquire(self, timeout: float = 0.0) -> bool:
        """
        Acquire the process lock.

        Args:
            timeout: How long to wait for lock (seconds). 0 = don't wait.

        Returns:
            True if lock acquired, False if timeout

        Raises:
            ProcessLockError: If lock is held by another process and timeout=0
        """
        start_time = time.time()

        while True:
            # Check if lock is held by another process
            if self.is_locked():
                if timeout == 0:
                    # Read the PID for error message
                    try:
                        pid = int(self.lock_file.read_text().strip())
                        raise ProcessLockError(
                            f"Another instance is already running (PID: {pid}). "
                            f"If this is incorrect, remove lock file: {self.lock_file}"
                        )
                    except ValueError:
                        raise ProcessLockError(
                            f"Lock file exists but is invalid: {self.lock_file}"
                        )

                # Wait and retry
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"Lock acquisition timed out after {timeout}s")
                    return False

                time.sleep(0.1)
                continue

            # Try to create lock file
            try:
                # Write our PID to lock file
                self.lock_file.write_text(str(os.getpid()))
                self._locked = True
                logger.debug(f"Acquired process lock: {self.lock_file}")
                return True

            except IOError as e:
                if timeout == 0:
                    raise ProcessLockError(f"Failed to create lock file: {e}")

                # Wait and retry
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"Lock acquisition timed out after {timeout}s")
                    return False

                time.sleep(0.1)

    def release(self):
        """Release the process lock."""
        if not self._locked:
            return

        try:
            if self.lock_file.exists():
                # Verify it's our lock file
                try:
                    pid = int(self.lock_file.read_text().strip())
                    if pid == os.getpid():
                        self.lock_file.unlink()
                        logger.debug(f"Released process lock: {self.lock_file}")
                    else:
                        logger.warning(
                            f"Lock file PID ({pid}) doesn't match our PID ({os.getpid()})"
                        )
                except ValueError:
                    logger.warning(f"Invalid lock file content, removing anyway")
                    self.lock_file.unlink()
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
        finally:
            self._locked = False

    def __enter__(self):
        """Context manager entry - acquire lock."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release lock."""
        self.release()
        return False

    def __del__(self):
        """Cleanup - release lock on deletion."""
        self.release()
