"""
Show rotation with persistent state tracking.

Maintains show rotation order with state that persists across restarts
and resets daily.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class ShowRotation:
    """
    Manages show rotation with persistent state tracking.

    Maintains the current position in a show rotation list, with state
    that persists across application restarts and resets daily.

    Features:
    - Automatic wraparound when reaching end of rotation
    - Daily reset (starts from beginning each day)
    - Thread-safe file-based persistence
    - Handles rotation changes gracefully (add/remove shows)

    Example:
        rotation = ShowRotation(
            shows=["show1", "show2", "show3"],
            state_file=".rotation_state"
        )

        # Get next show and advance
        show_name = rotation.next_show()

        # Peek without advancing
        show_name, index = rotation.peek_next()

        # Reset to beginning
        rotation.reset()
    """

    def __init__(
        self, shows: List[str], state_file: Optional[str] = None, state_dir: Optional[Path] = None
    ):
        """
        Initialize show rotation.

        Args:
            shows: List of show names in rotation order
            state_file: Name of state file (default: ".show_rotation_state")
            state_dir: Directory for state file (default: current directory)
        """
        if not shows:
            raise ValueError("Show rotation cannot be empty")

        self.shows = list(shows)  # Make a copy
        self._state_file = self._get_state_file_path(state_file, state_dir)

        logger.info(f"Initialized rotation with {len(self.shows)} shows: {', '.join(self.shows)}")
        logger.debug(f"State file: {self._state_file}")

    def _get_state_file_path(self, state_file: Optional[str], state_dir: Optional[Path]) -> Path:
        """Build path to state file."""
        filename = state_file or ".show_rotation_state"
        directory = state_dir or Path.cwd()
        return Path(directory) / filename

    def _read_state(self) -> tuple[Optional[str], Optional[int]]:
        """
        Read rotation state from file.

        Returns:
            Tuple of (date_string, index) or (None, None) if invalid/missing
        """
        try:
            if not self._state_file.exists():
                return None, None

            content = self._state_file.read_text().strip()
            if "," not in content:
                return None, None

            date_str, index_str = content.split(",", 1)
            index = int(index_str)

            # Validate index is reasonable
            if index < 0 or index >= 10000:
                logger.warning(f"Invalid index {index} in state file, resetting")
                return None, None

            return date_str, index

        except (ValueError, OSError) as e:
            logger.warning(f"Failed to read rotation state: {e}")
            return None, None

    def _write_state(self, index: int) -> None:
        """
        Write rotation state to file.

        Args:
            index: Current rotation index
        """
        try:
            # Validate index before writing
            if index < 0 or index >= len(self.shows):
                logger.warning(
                    f"Invalid index {index} for rotation size {len(self.shows)}, not saving"
                )
                return

            today = datetime.now().strftime("%Y-%m-%d")
            content = f"{today},{index}"

            # Ensure directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)

            self._state_file.write_text(content)
            logger.debug(f"Saved rotation state: index={index}, date={today}")

        except OSError as e:
            logger.warning(f"Failed to write rotation state: {e}")

    def _get_current_index(self) -> int:
        """
        Get current rotation index.

        Returns:
            Current index, or -1 if no state or different day
        """
        date_str, index = self._read_state()

        if date_str is None or index is None:
            return -1

        # Check if it's the same day
        today = datetime.now().strftime("%Y-%m-%d")
        if date_str != today:
            logger.debug(f"State is from {date_str}, today is {today}, resetting to start")
            return -1

        # Validate index is within current rotation bounds
        if index >= len(self.shows):
            logger.warning(
                f"Saved index {index} is out of bounds for rotation size {len(self.shows)}, "
                f"resetting to start"
            )
            return -1

        return index

    def peek_next(self) -> tuple[str, int]:
        """
        Peek at next show without advancing.

        Returns:
            Tuple of (show_name, next_index)
        """
        current = self._get_current_index()
        next_index = (current + 1) % len(self.shows)
        show_name = self.shows[next_index]

        logger.debug(f"Next show: '{show_name}' (index {next_index}/{len(self.shows)-1})")
        return show_name, next_index

    def next_show(self) -> str:
        """
        Get next show in rotation and advance.

        Returns:
            Show name

        Example:
            rotation = ShowRotation(["show1", "show2", "show3"])
            show1 = rotation.next_show()  # Returns "show1"
            show2 = rotation.next_show()  # Returns "show2"
            show3 = rotation.next_show()  # Returns "show3"
            show1 = rotation.next_show()  # Wraps around, returns "show1"
        """
        show_name, next_index = self.peek_next()
        self._write_state(next_index)
        logger.info(f"Advanced rotation to '{show_name}' (index {next_index})")
        return show_name

    def reset(self) -> None:
        """
        Reset rotation to beginning.

        Next call to next_show() will return the first show.
        """
        try:
            self._state_file.unlink(missing_ok=True)
            logger.info("Reset rotation to beginning")
        except OSError as e:
            logger.warning(f"Failed to reset rotation state: {e}")

    def get_current_position(self) -> tuple[Optional[str], int, int]:
        """
        Get current position in rotation.

        Returns:
            Tuple of (current_show_name, current_index, total_shows)
            Returns (None, -1, total) if at start or reset
        """
        current_index = self._get_current_index()
        total = len(self.shows)

        if current_index == -1:
            return None, -1, total

        show_name = self.shows[current_index]
        return show_name, current_index, total

    def __len__(self) -> int:
        """Get number of shows in rotation."""
        return len(self.shows)

    def __repr__(self) -> str:
        """String representation."""
        current_show, index, total = self.get_current_position()
        if current_show:
            return f"ShowRotation({total} shows, current: '{current_show}' at index {index})"
        return f"ShowRotation({total} shows, at start)"
