"""Tests for process lock module."""

import os
import time
import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from lightshow import ProcessLock, ProcessLockError


class TestProcessLock:
    """Test ProcessLock class."""

    def test_create_lock(self, tmp_path):
        """Test creating a process lock."""
        lock = ProcessLock("test", lock_dir=tmp_path)
        assert lock.name == "test"
        assert lock.lock_file == tmp_path / "test.lock"
        assert not lock.is_locked()

    def test_acquire_lock(self, tmp_path):
        """Test acquiring a lock."""
        lock = ProcessLock("test", lock_dir=tmp_path)

        # Should not be locked initially
        assert not lock.is_locked()

        # Acquire lock
        lock.acquire()

        # Should be locked now
        assert lock.is_locked()
        assert lock.lock_file.exists()

        # Lock file should contain our PID
        pid = int(lock.lock_file.read_text().strip())
        assert pid == os.getpid()

        # Cleanup
        lock.release()

    def test_release_lock(self, tmp_path):
        """Test releasing a lock."""
        lock = ProcessLock("test", lock_dir=tmp_path)

        lock.acquire()
        assert lock.is_locked()

        lock.release()
        assert not lock.is_locked()
        assert not lock.lock_file.exists()

    def test_double_acquire_same_process(self, tmp_path):
        """Test acquiring lock twice in same process raises error."""
        lock1 = ProcessLock("test", lock_dir=tmp_path)
        lock2 = ProcessLock("test", lock_dir=tmp_path)

        lock1.acquire()

        # Second acquire should fail
        with pytest.raises(ProcessLockError) as exc_info:
            lock2.acquire()

        assert "Another instance is already running" in str(exc_info.value)
        assert str(os.getpid()) in str(exc_info.value)

        lock1.release()

    def test_context_manager(self, tmp_path):
        """Test using lock as context manager."""
        lock = ProcessLock("test", lock_dir=tmp_path)

        assert not lock.is_locked()

        with lock:
            assert lock.is_locked()
            assert lock.lock_file.exists()

        # Should be released after context
        assert not lock.is_locked()
        assert not lock.lock_file.exists()

    def test_context_manager_with_exception(self, tmp_path):
        """Test context manager releases lock even on exception."""
        lock = ProcessLock("test", lock_dir=tmp_path)

        try:
            with lock:
                assert lock.is_locked()
                raise ValueError("Test error")
        except ValueError:
            pass

        # Lock should still be released
        assert not lock.is_locked()
        assert not lock.lock_file.exists()

    def test_stale_lock_cleanup(self, tmp_path):
        """Test that stale locks (dead process) are cleaned up."""
        lock = ProcessLock("test", lock_dir=tmp_path)

        # Create a fake lock file with non-existent PID
        fake_pid = 999999  # Very unlikely to exist
        lock.lock_file.write_text(str(fake_pid))

        # Should not be considered locked (process doesn't exist)
        assert not lock.is_locked()

        # Should be able to acquire
        lock.acquire()
        assert lock.is_locked()

        # Should have our PID now
        pid = int(lock.lock_file.read_text().strip())
        assert pid == os.getpid()

        lock.release()

    def test_invalid_lock_file_cleanup(self, tmp_path):
        """Test that invalid lock files are cleaned up."""
        lock = ProcessLock("test", lock_dir=tmp_path)

        # Create invalid lock file (non-numeric)
        lock.lock_file.write_text("invalid")

        # Should not be considered locked
        assert not lock.is_locked()

        # Lock file should be removed
        # (is_locked() removes invalid files)
        assert not lock.lock_file.exists()

        # Should be able to acquire
        lock.acquire()
        assert lock.is_locked()

        lock.release()

    def test_acquire_timeout(self, tmp_path):
        """Test acquire with timeout."""
        lock1 = ProcessLock("test", lock_dir=tmp_path)
        lock2 = ProcessLock("test", lock_dir=tmp_path)

        lock1.acquire()

        # Try to acquire with timeout - should fail
        start = time.time()
        result = lock2.acquire(timeout=0.5)
        elapsed = time.time() - start

        assert not result
        assert elapsed >= 0.5
        assert elapsed < 1.0  # Should timeout, not wait forever

        lock1.release()

    def test_acquire_timeout_success(self, tmp_path):
        """Test acquire with timeout succeeds when lock released."""
        lock1 = ProcessLock("test", lock_dir=tmp_path)
        lock2 = ProcessLock("test", lock_dir=tmp_path)

        lock1.acquire()

        # Release lock after short delay
        def release_after_delay():
            time.sleep(0.2)
            lock1.release()

        import threading

        thread = threading.Thread(target=release_after_delay)
        thread.start()

        # Should succeed within timeout
        result = lock2.acquire(timeout=1.0)
        assert result
        assert lock2.is_locked()

        thread.join()
        lock2.release()

    def test_destructor_cleanup(self, tmp_path):
        """Test that destructor releases lock."""
        lock = ProcessLock("test", lock_dir=tmp_path)
        lock.acquire()

        assert lock.is_locked()
        lock_file = lock.lock_file

        # Delete lock object
        del lock

        # Lock should be released
        assert not lock_file.exists()

    def test_different_lock_names(self, tmp_path):
        """Test that different lock names don't conflict."""
        lock1 = ProcessLock("test1", lock_dir=tmp_path)
        lock2 = ProcessLock("test2", lock_dir=tmp_path)

        lock1.acquire()

        # Should be able to acquire different lock
        lock2.acquire()

        assert lock1.is_locked()
        assert lock2.is_locked()

        lock1.release()
        lock2.release()

    def test_multiple_processes(self, tmp_path):
        """Test that lock actually prevents multiple processes."""
        # Create a test script that tries to acquire lock
        test_script = tmp_path / "test_lock_script.py"
        test_script.write_text(
            f"""
import sys
sys.path.insert(0, '{Path.cwd()}')
from lightshow import ProcessLock

lock = ProcessLock("multiproc_test", lock_dir="{tmp_path}")
try:
    lock.acquire()
    print("ACQUIRED")
    import time
    time.sleep(1.0)
    lock.release()
    sys.exit(0)
except Exception as e:
    print(f"FAILED: {{e}}")
    sys.exit(1)
"""
        )

        # Start first process
        proc1 = subprocess.Popen(
            [sys.executable, str(test_script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Give it time to acquire lock
        time.sleep(0.2)

        # Start second process - should fail
        proc2 = subprocess.Popen(
            [sys.executable, str(test_script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait for both to complete
        out1, err1 = proc1.communicate(timeout=5)
        out2, err2 = proc2.communicate(timeout=5)

        # First should succeed
        assert b"ACQUIRED" in out1
        assert proc1.returncode == 0

        # Second should fail
        assert b"FAILED" in out2
        assert proc2.returncode == 1


class TestProcessLockIntegration:
    """Integration tests for ProcessLock."""

    def test_real_world_usage(self, tmp_path):
        """Test typical usage pattern."""
        # Simulate application startup
        lock = ProcessLock("myapp", lock_dir=tmp_path)

        # Check if already running
        if lock.is_locked():
            pytest.fail("Should not be locked initially")

        # Acquire lock for application lifetime
        try:
            lock.acquire()

            # Simulate application running
            assert lock.is_locked()

            # Try to start another instance
            lock2 = ProcessLock("myapp", lock_dir=tmp_path)
            with pytest.raises(ProcessLockError):
                lock2.acquire()

        finally:
            # Cleanup on exit
            lock.release()

        # Verify cleanup
        assert not lock.is_locked()

    def test_crash_recovery(self, tmp_path):
        """Test that crashed process locks are recoverable."""
        lock = ProcessLock("crashtest", lock_dir=tmp_path)

        # Simulate a crashed process by creating stale lock
        lock.lock_file.write_text("999999")  # Non-existent PID

        # Should be able to recover and acquire
        lock.acquire()
        assert lock.is_locked()

        lock.release()
