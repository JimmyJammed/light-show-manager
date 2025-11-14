"""
macOS-specific audio backend using the built-in afplay command.

This backend supports M4A/AAC files that pygame doesn't handle well.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

from lightshow.audio.audio_player import AudioBackend
from lightshow.audio.exceptions import AudioError

logger = logging.getLogger(__name__)


class AfplayBackend(AudioBackend):
    """
    Audio backend using macOS's built-in afplay command.

    This backend is automatically used on macOS (Darwin) when available.
    Supports all audio formats that macOS supports, including M4A/AAC.

    Note: Volume control is not supported by afplay.
    """

    def __init__(self, output_device: Optional[str] = None):
        """
        Initialize afplay backend.

        Args:
            output_device: Not used by afplay (parameter kept for consistency)
        """
        self.output_device = output_device
        self._process = None
        self._current_file = None
        self._volume = 1.0
        logger.info("Afplay audio backend initialized (macOS)")

    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0) -> None:
        """
        Play audio file using afplay.

        Note: Volume control is not supported by afplay. The system volume will be used.
        Note: Loops parameter is not supported by afplay. Audio plays once.
        """
        # Stop any currently playing audio
        self.stop()

        # Store volume (for tracking, but not actually used)
        self._volume = volume
        self._current_file = filepath

        try:
            # Start afplay in background
            self._process = subprocess.Popen(
                ["afplay", str(filepath)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
            logger.debug(f"Playing audio via afplay: {filepath.name}")

            if volume != 1.0:
                logger.warning(
                    f"Volume control not supported by afplay (requested: {volume}). "
                    "Using system volume instead."
                )

            if loops != 0:
                logger.warning(
                    f"Loop parameter not supported by afplay (requested: {loops}). "
                    "Audio will play once."
                )

        except FileNotFoundError:
            raise AudioError("afplay command not found (are you on macOS?)")
        except Exception as e:
            raise AudioError(f"Failed to start afplay: {e}")

    def stop(self) -> None:
        """Stop currently playing audio."""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                logger.warning("afplay did not terminate gracefully, killing process")
                self._process.kill()
            self._process = None
            self._current_file = None
            logger.debug("Audio stopped")

    def pause(self) -> None:
        """Pause not supported by afplay."""
        logger.warning("Pause not supported by afplay backend")

    def resume(self) -> None:
        """Resume not supported by afplay."""
        logger.warning("Resume not supported by afplay backend")

    def set_volume(self, volume: float) -> None:
        """
        Volume control not supported by afplay.

        The volume parameter is stored but not applied. System volume will be used.
        """
        self._volume = volume
        logger.warning(
            f"Volume control not supported by afplay (requested: {volume}). "
            "Use system volume instead."
        )

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._process is not None and self._process.poll() is None

    def get_position(self) -> float:
        """
        Get playback position (not supported by afplay).

        Returns:
            Always returns 0.0 as position tracking is not supported
        """
        return 0.0
