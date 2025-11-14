# Testing light-show-manager Locally in Another Project

This guide shows how to test the `light-show-manager` package in another project before publishing to PyPI.

## Method 1: Install in Editable Mode (Recommended)

This creates a live link to your development code, so changes are immediately reflected.

### Steps:

1. **Navigate to your other project**:
   ```bash
   cd /path/to/your/other-project
   ```

2. **Install light-show-manager in editable mode**:
   ```bash
   pip install -e /Users/jhickman/GitHub/light-show-manager
   ```

3. **Test the import**:
   ```python
   # In your project code
   from lightshow import LightShowManager, Show
   import asyncio

   # Create a test show
   show = Show("test", duration=5.0)
   show.add_sync_event(0.0, lambda: print("Hello from light-show-manager!"))

   manager = LightShowManager(shows=[show])
   asyncio.run(manager.run_show("test"))
   ```

4. **Make changes if needed**:
   - Edit code in `/Users/jhickman/GitHub/light-show-manager/lightshow/`
   - Changes are immediately available (no reinstall needed)

5. **When done testing, uninstall**:
   ```bash
   pip uninstall light-show-manager
   ```

## Method 2: Install from Built Distribution

Test the actual package that will be uploaded to PyPI.

### Steps:

1. **Build the package** (already done, but if you need to rebuild):
   ```bash
   cd /Users/jhickman/GitHub/light-show-manager
   python3 -m build
   ```

2. **Install from the wheel file**:
   ```bash
   cd /path/to/your/other-project
   pip install /Users/jhickman/GitHub/light-show-manager/dist/light_show_manager-0.1.0-py3-none-any.whl
   ```

3. **Test the import** (same as Method 1)

4. **Uninstall when done**:
   ```bash
   pip uninstall light-show-manager
   ```

## Method 3: Add to requirements.txt (For Testing)

If your other project uses a requirements.txt file:

1. **Add to requirements.txt**:
   ```
   # requirements.txt
   light-show-manager @ file:///Users/jhickman/GitHub/light-show-manager
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Remove the line when done testing**

## Testing Checklist

When testing in your other project, verify:

- [ ] Package imports successfully
- [ ] Basic Show creation works
- [ ] Sync events execute properly
- [ ] Async events execute properly
- [ ] Batch events work
- [ ] Lifecycle hooks function correctly
- [ ] Error handling works as expected
- [ ] Integration with your hardware/devices works
- [ ] No import errors or missing dependencies
- [ ] Performance is acceptable

## Common Test Scenarios

### Test 1: Basic Integration
```python
from lightshow import LightShowManager, Show

def test_basic():
    show = Show("basic_test", duration=2.0)
    show.add_sync_event(0.0, lambda: print("Start"))
    show.add_sync_event(1.0, lambda: print("Middle"))
    show.add_sync_event(2.0, lambda: print("End"))

    manager = LightShowManager(shows=[show])
    import asyncio
    asyncio.run(manager.run_show("basic_test"))

test_basic()
```

### Test 2: With Your Devices (Example with govee-python)
```python
from lightshow import LightShowManager, Show
from govee import GoveeClient  # Your other package
import asyncio

# Initialize hardware
govee = GoveeClient(api_key="...", prefer_lan=True)
govee.load_devices("govee_devices.json")

# Create show
show = Show("device_test", duration=5.0)
show.add_sync_event(0.0, lambda: govee.set_brightness_all(govee.get_all_devices(), 100))
show.add_sync_event(2.0, lambda: govee.set_color_all(govee.get_all_devices(), (255, 0, 0)))
show.add_sync_event(4.0, lambda: govee.power_all(govee.get_all_devices(), False))

# Run
manager = LightShowManager(
    shows=[show],
    post_show=lambda show, ctx: govee.power_all(govee.get_all_devices(), False)
)
asyncio.run(manager.run_show("device_test"))
```

### Test 3: Async Events
```python
from lightshow import LightShowManager, Show
import asyncio

async def async_task():
    print("Async task started")
    await asyncio.sleep(0.5)
    print("Async task completed")

def test_async():
    show = Show("async_test", duration=2.0)
    show.add_async_event(0.0, async_task)
    show.add_async_event(1.0, async_task)

    manager = LightShowManager(shows=[show])
    asyncio.run(manager.run_show("async_test"))

test_async()
```

## Troubleshooting

### Import Error
```
ModuleNotFoundError: No module named 'lightshow'
```
**Solution**: Make sure you installed the package (Method 1 or 2)

### Already Installed
```
ERROR: Cannot install because different version already installed
```
**Solution**: Uninstall first: `pip uninstall light-show-manager`

### Changes Not Reflected
**Problem**: Made code changes but they don't appear
**Solution**:
- If using Method 2 (wheel), reinstall: `pip install --force-reinstall /path/to/wheel`
- If using Method 1 (editable), changes should be automatic

### Python Version Mismatch
**Problem**: Package requires Python 3.8+
**Solution**: Check your Python version: `python3 --version`

## After Testing

Once you're satisfied with testing:

1. **Uninstall the local version**:
   ```bash
   pip uninstall light-show-manager
   ```

2. **Publish to PyPI** (follow RELEASE_CHECKLIST.md)

3. **Install from PyPI** in your other project:
   ```bash
   pip install light-show-manager
   ```

4. **Update your project's requirements.txt**:
   ```
   light-show-manager>=0.1.0
   ```

## Quick Start Commands

For govee-python project or another project:

```bash
# Navigate to your other project
cd /Users/jhickman/GitHub/govee-python  # or your project path

# Install light-show-manager in editable mode
pip install -e /Users/jhickman/GitHub/light-show-manager

# Test import
python3 -c "from lightshow import LightShowManager, Show; print('✓ Import successful!')"

# Run your test script
python3 your_test_script.py

# When done
pip uninstall light-show-manager
```
