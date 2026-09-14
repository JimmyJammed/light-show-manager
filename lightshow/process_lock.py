"""Process exclusion backed by kernel locks, not PID liveness checks."""

import os
import tempfile
import time
from pathlib import Path


class ProcessLockError(Exception):
    """Another process owns the lock."""


class ProcessLock:
    """Lock files persist intentionally: unlinking a locked inode permits races."""

    def __init__(self, name="lightshow", lock_dir=None):
        if not name or Path(name).name != name:
            raise ValueError("Lock name must be a filename")
        self.name = name
        self.lock_dir = Path(lock_dir or tempfile.gettempdir())
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.lock_dir / f"{name}.lock"
        self._handle = None
        self._locked = False

    @staticmethod
    def _lock(handle):
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _unlock(handle):
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _open(self):
        # Windows byte-range locks need a byte present; never truncate the file.
        handle = self.lock_file.open("a+b")
        if self.lock_file.stat().st_size == 0:
            handle.write(b"\0")
            handle.flush()
        return handle

    def is_locked(self):
        if self._locked:
            return True
        with self._open() as handle:
            try:
                self._lock(handle)
            except (BlockingIOError, PermissionError):
                return True
            self._unlock(handle)
            return False

    def acquire(self, timeout=0.0):
        if timeout < 0:
            raise ValueError("timeout must be nonnegative")
        if self._locked:
            raise ProcessLockError("This instance already owns the lock")
        deadline = time.monotonic() + timeout
        handle = self._open()
        try:
            while True:
                try:
                    self._lock(handle)
                    self._handle, self._locked = handle, True
                    return True
                except (BlockingIOError, PermissionError) as error:
                    if timeout == 0:
                        raise ProcessLockError(f"Lock is held: {self.lock_file}") from error
                    if time.monotonic() >= deadline:
                        handle.close()
                        return False
                    time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        except BaseException:
            handle.close()
            raise

    def release(self):
        if self._handle is not None:
            try:
                self._unlock(self._handle)
            finally:
                self._handle.close()
                self._handle, self._locked = None, False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()
