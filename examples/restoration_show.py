"""Snapshot and restore a simulated device, including interrupted playback."""
import asyncio
from lightshow import LightShowManager, Show


async def main():
    device = {'brightness': 25}
    def before(show, context):
        context['original'] = device.copy()
    def after(show, context):
        device.update(context.get('original', {}))
    show = Show('restore', .05)
    show.add_sync_event(0, lambda: device.update(brightness=100))
    async with LightShowManager([show], pre_show=before, post_show=after) as manager:
        await manager.run_show('restore')
    assert device['brightness'] == 25
    print('Restored brightness:', device['brightness'])


if __name__ == '__main__':
    asyncio.run(main())
