"""Run after pip install -e .; all commands are simulated."""
import asyncio
from lightshow import LightShowManager, Show


async def main():
    show = Show('mixed', .1)
    async def shimmer():
        print('Async shimmer')
    show.add_sync_event(0, lambda: print('Sync glow'))
    show.add_async_event(.05, shimmer)
    async with LightShowManager([show]) as manager:
        print(await manager.run_show('mixed'))


if __name__ == '__main__':
    asyncio.run(main())
