"""
Device state management utilities for light shows.

This module provides a decorator for automatically tracking device usage
in light shows and integrating with user-defined state management hooks.

The decorator is completely generic - it doesn't know about any specific
device control library (Govee, Hue, etc.). Users implement the actual
save/restore logic by overriding the show manager's hooks.

Example:
    # In your project, define state management functions:
    def save_device_states(devices, context):
        '''Save state using your device library'''
        device_client = context.get('device_client')
        if device_client:
            device_client.save_state(devices)

    def restore_device_states(devices, context):
        '''Restore state using your device library'''
        device_client = context.get('device_client')
        if device_client:
            device_client.restore_state(devices)

    # Register with show manager:
    show_manager.hooks.save_device_states = save_device_states
    show_manager.hooks.restore_device_states = restore_device_states

    # Use decorator on show builders:
    @with_device_state_management(device_client)
    def build_my_show(show_manager, device_client, config):
        show = show_manager.create_show("my_show", duration=120.0)
        # Any device operations will be tracked automatically
        return show
"""

from functools import wraps
from typing import Set, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


def with_device_state_management(
    device_client,
    methods_to_track: Optional[list] = None,
    spotlight_devices: Optional[list] = None,
    exclude_from_tracking: Optional[list] = None
) -> Callable:
    """
    Decorator that automatically tracks device usage and integrates with show hooks.

    This decorator wraps a show builder function and tracks which devices are
    controlled during show construction by wrapping device client methods.
    The tracked devices are stored in the show's context and passed to
    user-defined hooks for state management.

    The decorator is generic and works with any device control library.
    Users implement actual save/restore logic by overriding:
    - show_manager.hooks.save_device_states(devices, context)
    - show_manager.hooks.restore_device_states(devices, context)

    Args:
        device_client: The device control client to track (e.g., GoveeClient,
            PhilipsHueClient, etc.)
        methods_to_track: List of method names to track. Defaults to common
            control methods like 'power', 'set_color', etc.
        spotlight_devices: Optional list of "spotlight" devices to turn off
            before show starts (for dramatic effect). These will have their
            power() method called with False during pre-show.
        exclude_from_tracking: Optional list of method names to explicitly
            exclude from tracking.

    Returns:
        Decorator function that wraps show builder functions

    Example:
        @with_device_state_management(
            govee_client,
            spotlight_devices=[spotlight1, spotlight2]
        )
        def build_show_starcourt(show_manager, govee_client, config):
            show = show_manager.create_show("starcourt", duration=194.0)

            # All device operations are tracked automatically:
            govee_client.apply_scene(device1, scene1)
            govee_client.set_color(device2, Colors.RED)
            # ... etc ...

            return show

    Notes:
        - The decorator temporarily wraps device client methods during show
          construction, then restores them (thread-safe within the function)
        - Tracked devices are stored in show.context['controlled_devices']
        - The decorator preserves any existing pre/post show hooks
        - If save/restore hooks aren't defined, tracking still happens but
          no state operations occur (allowing progressive adoption)
    """

    # Default methods to track for most device control libraries
    if methods_to_track is None:
        methods_to_track = [
            'apply_scene',
            'set_music_mode',
            'power',
            'set_color',
            'set_brightness',
            'set_color_temp',
            'set_saturation',
            'set_effect',
        ]

    # Remove explicitly excluded methods
    if exclude_from_tracking:
        methods_to_track = [m for m in methods_to_track if m not in exclude_from_tracking]

    def decorator(show_builder_func: Callable) -> Callable:
        @wraps(show_builder_func)
        def wrapper(show_manager, *args, **kwargs):
            # Track devices used during show building
            tracked_devices: Set[Any] = set()

            def track_device(device):
                """Add device(s) to the tracking set."""
                if isinstance(device, list):
                    tracked_devices.update(device)
                elif device is not None:
                    tracked_devices.add(device)

            # Store original methods
            original_methods = {}
            for method_name in methods_to_track:
                if hasattr(device_client, method_name):
                    original_methods[method_name] = getattr(device_client, method_name)

            # Create tracking wrappers
            def make_tracking_wrapper(original_method):
                """Creates a wrapper that tracks the device parameter."""
                def tracking_wrapper(device, *args, **kwargs):
                    track_device(device)
                    return original_method(device, *args, **kwargs)
                return tracking_wrapper

            # Replace methods with tracking versions
            for method_name, original_method in original_methods.items():
                setattr(device_client, method_name, make_tracking_wrapper(original_method))

            try:
                # Build the show (this will track all device usage)
                show = show_builder_func(show_manager, *args, **kwargs)
            finally:
                # Always restore original methods, even if show building fails
                for method_name, original_method in original_methods.items():
                    setattr(device_client, method_name, original_method)

            # Convert to list and store in show context
            controlled_devices = list(tracked_devices)

            # Initialize or update show context
            if not hasattr(show, 'context'):
                show.context = {}
            show.context['controlled_devices'] = controlled_devices
            show.context['spotlight_devices'] = spotlight_devices or []
            show.context['device_client'] = device_client

            logger.info(f"Tracked {len(controlled_devices)} devices for show '{show.name}'")

            # Wire up to show manager's state management hooks
            _add_state_management_hooks(show, show_manager, controlled_devices, spotlight_devices)

            return show

        return wrapper
    return decorator


def _add_state_management_hooks(show, show_manager, controlled_devices, spotlight_devices):
    """
    Add pre/post hooks that call the show manager's state management functions.

    This function integrates with the show manager's hook system:
    - Calls show_manager.hooks.save_device_states() in pre-show hook
    - Calls show_manager.hooks.restore_device_states() in post-show hook

    If these hooks aren't defined, they are treated as no-ops (allowing
    users to adopt state management progressively).

    Args:
        show: The Show object to add hooks to
        show_manager: The LightShowManager instance
        controlled_devices: List of devices that were tracked
        spotlight_devices: Optional list of spotlights to turn off
    """

    # Get the save/restore functions from show manager hooks
    save_fn = getattr(show_manager.hooks, 'save_device_states', None)
    restore_fn = getattr(show_manager.hooks, 'restore_device_states', None)

    def pre_show_hook():
        """Pre-show hook: save device states and turn off spotlights."""
        if save_fn:
            logger.info(f"Saving state of {len(controlled_devices)} devices...")
            try:
                save_fn(controlled_devices, show.context)
                logger.info("Device state saved successfully")
            except Exception as e:
                logger.error(f"Failed to save device states: {e}", exc_info=True)
                # Continue even if save fails - show must go on
        else:
            logger.debug("No save_device_states hook defined - skipping state save")

        # Turn off spotlights for dramatic effect
        if spotlight_devices:
            logger.info(f"Turning off {len(spotlight_devices)} spotlights...")
            device_client = show.context.get('device_client')
            if device_client and hasattr(device_client, 'power'):
                for spotlight in spotlight_devices:
                    try:
                        device_client.power(spotlight, False)
                    except Exception as e:
                        logger.error(f"Failed to turn off spotlight: {e}")

    def post_show_hook():
        """Post-show hook: restore device states."""
        if restore_fn:
            logger.info(f"Restoring state of {len(controlled_devices)} devices...")
            try:
                restore_fn(controlled_devices, show.context)
                logger.info("Device state restored successfully")
            except Exception as e:
                logger.error(f"Failed to restore device states: {e}", exc_info=True)
        else:
            logger.debug("No restore_device_states hook defined - skipping state restore")

    # Preserve any existing hooks
    original_pre_hook = show.hooks.on_pre_show if hasattr(show.hooks, 'on_pre_show') else None
    original_post_hook = show.hooks.on_post_show if hasattr(show.hooks, 'on_post_show') else None

    def combined_pre_hook():
        """Combined pre-show hook that calls original hook first."""
        if original_pre_hook:
            original_pre_hook()
        pre_show_hook()

    def combined_post_hook():
        """Combined post-show hook that calls original hook first."""
        if original_post_hook:
            original_post_hook()
        post_show_hook()

    # Set the combined hooks
    show.hooks.on_pre_show = combined_pre_hook
    show.hooks.on_post_show = combined_post_hook
