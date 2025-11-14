#!/usr/bin/env python3
"""
Create GitHub release

Usage:
    export GITHUB_TOKEN=your_token_here
    python3 create_release.py [version]

Examples:
    python3 create_release.py 1.0.0
    python3 create_release.py 1.0.1
"""

import json
import os
import sys
import urllib.request
import urllib.error

REPO = "JimmyJammed/light-show-manager"

# Get version from command line or default
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
TAG = f"v{VERSION}"

RELEASE_BODIES = {
    "1.0.0": """# Version 1.0.0 - Initial Release

A timeline-based show orchestration framework for coordinating time-synchronized commands across multiple devices and systems.

## Features

- **Timeline-Based Execution** - Precise event scheduling with synchronous and asynchronous command support
- **Audio Synchronization** - Built-in audio playback with multiple backend support (afplay, custom backends)
- **Lifecycle Hooks** - Pre-show, post-show, on-event, and error handling hooks
- **State Management** - Automatic device state save/restore decorators
- **Process Locking** - Prevent multiple instances from running simultaneously
- **Show Rotation** - Automatic show selection with cooldown management
- **Volume Scheduling** - Time-based volume adjustments for different periods
- **Unified Logging** - Color-coded console output and timestamped log files
- **Async Support** - Full async/await support for modern Python applications
- **Type Safety** - Comprehensive type hints throughout the codebase

## Installation

```bash
pip install light-show-manager
```

## Quick Start

```python
from lightshow import LightShowManager, Show

# Create show manager
manager = LightShowManager()

# Create a show
show = manager.create_show("my_show", duration=120.0)

# Add events
show.add_sync_event(10.0, lambda: print("Event at 10 seconds"))
show.add_async_event(20.0, async_func)

# Run the show
manager.run_show(show)
```

## Documentation

See [README.md](README.md) for full documentation and examples."""
}

def get_release_body(version):
    """Get release body for a specific version"""
    return RELEASE_BODIES.get(version, RELEASE_BODIES.get("1.0.0", ""))

def main():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("\nTo create a release, you need a GitHub Personal Access Token:")
        print("1. Create a token at: https://github.com/settings/tokens")
        print("2. Give it 'repo' scope")
        print("3. Run: export GITHUB_TOKEN=your_token_here")
        print(f"4. Run this script again: python3 create_release.py {VERSION}")
        print("\nOr create the release manually at:")
        print(f"   https://github.com/{REPO}/releases/new")
        print(f"   - Select tag: {TAG}")
        print(f"   - Title: {TAG}")
        sys.exit(1)
    
    release_body = get_release_body(VERSION)
    if not release_body:
        print(f"❌ No release body defined for version {VERSION}")
        print(f"   Available versions: {', '.join(RELEASE_BODIES.keys())}")
        sys.exit(1)
    
    print(f"📦 Creating release {TAG} for {REPO}")
    print(f"   Version: {VERSION}")
    
    release_data = {
        "tag_name": TAG,
        "name": TAG,
        "body": release_body,
        "draft": False,
        "prerelease": False
    }
    
    url = f"https://api.github.com/repos/{REPO}/releases"
    data = json.dumps(release_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'token {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json'
    })
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("✅ Release created successfully!")
            print(f"   URL: {result.get('html_url', 'N/A')}")
            return 0
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get('message', error_body)
        except:
            error_msg = error_body
        print(f"❌ Failed to create release: {e.code}")
        print(f"   Error: {error_msg}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

