# Light Show Manager

Python 3.12+ · MIT · version 2.0.0

Coordinate timed lighting, audio, and other device commands with explicit sync/async events and cleanup that finishes before the next show starts.

## Run locally

```sh
git clone https://github.com/JimmyJammed/light-show-manager.git
cd light-show-manager
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m lightshow --duration 2
```

The built-in Lanterns demo needs no devices, credentials, or audio hardware:

```text
Warm glow
Blue shimmer
Fade out
Restored
completed
```

## Integrate

```python
import asyncio
from lightshow import LightShowManager, Show

async def main():
    show = Show("hello", duration=1)
    show.add_sync_event(0, lambda: print("Lights on"))
    async with LightShowManager([show], post_show=lambda *_: print("Restore")) as manager:
        result = await manager.run_show("hello")
        print(result.status)

asyncio.run(main())
```

Use `add_async_event` with an async function, not an already-created coroutine. Batch methods accept lists of functions. The core has no runtime dependencies. Audio and notification backends are optional.

## Documentation

[Getting started](docs/GETTING_STARTED.md) · [API](docs/API.md) · [Customization](docs/CUSTOMIZATION.md) · [Architecture](docs/ARCHITECTURE.md) · [Migration](docs/MIGRATION.md) · [Testing](docs/TESTING.md) · [Validation](docs/VALIDATION.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

Timing is best-effort, not hard real-time. See validation for actually tested environments. Existing historical examples under `examples/` may require explicitly documented hardware/audio setup.

## License

[MIT](LICENSE). Existing author and copyright attribution is retained.
