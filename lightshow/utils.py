"""
Utility functions for the light show manager.

Common helpers and convenience functions.
"""
import re


def normalize_show_name(name: str) -> str:
    """
    Normalize a show name to a consistent format.

    Converts to lowercase, replaces spaces/hyphens with underscores,
    and removes special characters.

    Args:
        name: Show name to normalize (e.g., "Running Up That Hill", "starcourt-show")

    Returns:
        Normalized name (e.g., "running_up_that_hill", "starcourt_show")

    Examples:
        >>> normalize_show_name("Running Up That Hill")
        'running_up_that_hill'
        >>> normalize_show_name("starcourt-show")
        'starcourt_show'
        >>> normalize_show_name("  Stranger Things! ")
        'stranger_things'
    """
    if not name or not isinstance(name, str):
        return ""

    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()

    # Replace spaces and hyphens with underscores
    normalized = normalized.replace(" ", "_").replace("-", "_")

    # Remove special characters, keep only alphanumeric and underscores
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)

    # Replace multiple consecutive underscores with single underscore
    normalized = re.sub(r'_+', '_', normalized)

    # Remove leading/trailing underscores
    normalized = normalized.strip('_')

    return normalized
