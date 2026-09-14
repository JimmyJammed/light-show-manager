import asyncio
import signal
import subprocess
import sys
import threading

import pytest

from lightshow import LightShowManager, ProcessLock, Show


@pytest.mark.asyncio
async def test_replacement_waits_for_cleanup():
    entered, release = asyncio.Event(), asyncio.Event()
    order = []

    async def cleanup(show, context):
        if show.name == "a":
            entered.set()
            await release.wait()
        order.append("clean:" + show.name)

    a, b = Show("a", 10), Show("b", 0)
    a.add_async_event(0, lambda: asyncio.sleep(10))
    b.add_sync_event(0, lambda: order.append("b"))
    async with LightShowManager([a, b], post_show=cleanup) as manager:
        first = asyncio.create_task(manager.run_show("a"))
        await asyncio.sleep(0.01)
        second = asyncio.create_task(manager.run_show("b", interrupt=True))
        await entered.wait()
        assert "b" not in order
        release.set()
        assert (await first).status == "interrupted"
        assert (await second).status == "completed"
        assert order.index("clean:a") < order.index("b")


@pytest.mark.asyncio
async def test_canceled_worker_finishes_before_restoration():
    started, release = threading.Event(), threading.Event()
    order = []

    def work():
        started.set()
        release.wait(2)
        order.append("work")

    show = Show("worker", 0)
    show.add_sync_event(0, work)
    async with LightShowManager([show], post_show=lambda *_: order.append("restore")) as m:
        task = asyncio.create_task(m.run_show("worker"))
        await asyncio.to_thread(started.wait, 2)
        task.cancel()
        await asyncio.sleep(0.01)
        assert order == []
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert order == ["work", "restore"]


@pytest.mark.asyncio
async def test_injected_clock_and_repeated_runs():
    now = [0.0]
    seen = []

    async def sleep(seconds):
        now[0] += seconds

    show = Show("timed", 5)
    show.add_sync_event(2, lambda: seen.append(now[0]))
    async with LightShowManager([show], clock=lambda: now[0], sleep=sleep) as m:
        await m.run_show("timed")
        await m.run_show("timed")
    assert seen == [2, 7]
    assert now[0] == 10


def test_signals_unchanged_and_restored():
    old = signal.getsignal(signal.SIGINT)
    with LightShowManager() as m:
        assert signal.getsignal(signal.SIGINT) == old
        with m.signal_handlers():
            assert signal.getsignal(signal.SIGINT) != old
        assert signal.getsignal(signal.SIGINT) == old


def test_kernel_lock_contention(tmp_path):
    code = 'from lightshow import ProcessLock; import sys; l=ProcessLock("show",sys.argv[1]); print(l.acquire(timeout=.05))'
    with ProcessLock("show", tmp_path):
        result = subprocess.run(
            [sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "False"
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, check=False
    )
    assert result.stdout.strip() == "True"


@pytest.mark.asyncio
async def test_failed_cleanup_is_visible():
    def fail(*_):
        raise ValueError("cleanup failed")

    async with LightShowManager([Show("x", 0)], post_show=fail) as m:
        with pytest.raises(ValueError, match="cleanup failed"):
            await m.run_show("x")
        assert m.last_result.status == "failed"
        assert not m.is_running
