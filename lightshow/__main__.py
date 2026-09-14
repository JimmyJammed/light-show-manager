"""Run a configurable device-free timeline: python -m lightshow --duration 2."""

import argparse
import asyncio

from . import LightShowManager, Show


async def demo(duration):
    show = Show("Lanterns", duration)
    for fraction, cue in [(0, "Warm glow"), (0.4, "Blue shimmer"), (0.8, "Fade out")]:
        show.add_sync_event(duration * fraction, lambda cue=cue: print(cue), cue)
    async with LightShowManager([show], post_show=lambda *_: print("Restored")) as manager:
        result = await manager.run_show(show.name)
        print(result.status)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=2)
    args = parser.parse_args()
    asyncio.run(demo(args.duration))


if __name__ == "__main__":
    main()
