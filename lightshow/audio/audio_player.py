"""
Audio player with platform detection and backend abstraction.

Supports custom audio implementations via AudioBackend interface.
"""
import asyncio
import logging
import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from lightshow.audio.exceptions import (
    AudioError,
    AudioNotAvailableError,
    AudioFileNotFoundError,
)

logger = logging.getLogger(__name__)


class AudioBackend(ABC):
    """
    Abstract base class for audio backends.

    Users can implement this interface to provide custom audio playback.

    Example:
        class MyAudioBackend(AudioBackend):
            def play(self, filepath, volume, loops):
                # Custom implementation
                pass

            def stop(self):
                # Custom implementation
                pass
    """

    @abstractmethod
    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0) -> None:
        """
        Play audio file.

        Args:
            filepath: Path to audio file
            volume: Volume level (0.0 to 1.0)
            loops: Number of times to loop (0 = play once, -1 = infinite)
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop currently playing audio."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause currently playing audio."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume paused audio."""
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """
        Set volume for current playback.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        pass

    @abstractmethod
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        pass

    @abstractmethod
    def get_position(self) -> float:
        """Get current playback position in seconds."""
        pass


class PygameBackend(AudioBackend):
    """
    Default audio backend using pygame.

    Works on macOS, Linux (including Raspberry Pi), and Windows.
    """

    def __init__(self, output_device: Optional[str] = None):
        """
        Initialize pygame audio backend.

        Args:
            output_device: Audio output device (None = default)
        """
        self.output_device = output_device
        self._pygame = None
        self._mixer = None
        self._current_sound = None
        self._init_pygame()

    def _init_pygame(self):
        """Initialize pygame mixer."""
        try:
            import pygame
            self._pygame = pygame

            # Initialize mixer with appropriate settings
            # Higher buffer on Pi for stability, lower on desktop for responsiveness
            if platform.system() == "Linux":
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            else:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

            logger.info("Pygame audio backend initialized")

        except ImportError:
            raise AudioNotAvailableError(
                "pygame is required for audio support. "
                "Install with: pip install pygame\n"
                "Or use a custom AudioBackend implementation."
            )
        except Exception as e:
            raise AudioNotAvailableError(f"Failed to initialize pygame audio: {e}")

    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0) -> None:
        """Play audio file."""
        try:
            self._current_sound = self._pygame.mixer.Sound(str(filepath))
            self._current_sound.set_volume(max(0.0, min(1.0, volume)))
            self._current_sound.play(loops=loops)
            logger.debug(f"Playing audio: {filepath.name}")
        except Exception as e:
            raise AudioError(f"Failed to play audio file {filepath}: {e}")

    def stop(self) -> None:
        """Stop currently playing audio."""
        if self._current_sound:
            self._current_sound.stop()
            logger.debug("Audio stopped")

    def pause(self) -> None:
        """Pause currently playing audio."""
        if self._pygame:
            self._pygame.mixer.pause()
            logger.debug("Audio paused")

    def resume(self) -> None:
        """Resume paused audio."""
        if self._pygame:
            self._pygame.mixer.unpause()
            logger.debug("Audio resumed")

    def set_volume(self, volume: float) -> None:
        """Set volume for current playback."""
        if self._current_sound:
            self._current_sound.set_volume(max(0.0, min(1.0, volume)))
            logger.debug(f"Volume set to {volume}")

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        if self._pygame:
            return self._pygame.mixer.get_busy()
        return False

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if self._pygame and self._current_sound:
            # pygame returns position in milliseconds
            return self._pygame.mixer.music.get_pos() / 1000.0
        return 0.0


class DummyBackend(AudioBackend):
    """
    Dummy audio backend for testing or when audio is not needed.

    Logs audio operations but doesn't actually play anything.
    """

    def __init__(self):
        """Initialize dummy backend."""
        self._is_playing = False
        logger.info("Dummy audio backend initialized (no actual audio playback)")

    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0) -> None:
        """Simulate playing audio."""
        self._is_playing = True
        logger.info(f"[DUMMY] Playing: {filepath.name} (volume={volume}, loops={loops})")

    def stop(self) -> None:
        """Simulate stopping audio."""
        self._is_playing = False
        logger.info("[DUMMY] Stopped")

    def pause(self) -> None:
        """Simulate pausing audio."""
        logger.info("[DUMMY] Paused")

    def resume(self) -> None:
        """Simulate resuming audio."""
        logger.info("[DUMMY] Resumed")

    def set_volume(self, volume: float) -> None:
        """Simulate setting volume."""
        logger.info(f"[DUMMY] Volume set to {volume}")

    def is_playing(self) -> bool:
        """Check if audio is 'playing'."""
        return self._is_playing

    def get_position(self) -> float:
        """Get simulated playback position."""
        return 0.0


class AudioPlayer:
    """
    High-level audio player for light shows.

    Automatically detects platform and uses appropriate audio backend.
    Supports custom backends via the AudioBackend interface.

    Example:
        # Basic usage with auto-detection
        audio = AudioPlayer(audio_dir="audio")
        audio.play("song.mp3")

        # With custom backend
        audio = AudioPlayer(audio_dir="audio", backend=MyCustomBackend())

        # Dummy backend for testing
        audio = AudioPlayer(audio_dir="audio", backend="dummy")
    """

    def __init__(
        self,
        audio_dir: Union[str, Path] = "audio",
        backend: Optional[Union[AudioBackend, str]] = None,
        output_device: Optional[str] = None,
    ):
        """
        Initialize audio player.

        Args:
            audio_dir: Directory containing audio files
            backend: Audio backend to use:
                - None: Auto-detect and use pygame (default)
                - "dummy": Use dummy backend (no actual audio)
                - AudioBackend instance: Use custom backend
            output_device: Audio output device (backend-dependent)
        """
        self.audio_dir = Path(audio_dir)
        self.output_device = output_device

        # Initialize backend
        if backend is None:
            # Auto-detect platform and use best backend
            if platform.system() == "Darwin":
                # Try afplay first on macOS (better M4A/AAC support)
                try:
                    from lightshow.audio.afplay_backend import AfplayBackend
                    self.backend = AfplayBackend(output_device=output_device)
                    logger.info("Audio player initialized with afplay backend (macOS)")
                except Exception as e:
                    logger.warning(f"Afplay not available, trying pygame: {e}")
                    try:
                        self.backend = PygameBackend(output_device=output_device)
                        logger.info("Audio player initialized with pygame backend")
                    except AudioNotAvailableError as e2:
                        logger.warning(f"Pygame not available, using dummy backend: {e2}")
                        self.backend = DummyBackend()
            else:
                # Try pygame on other platforms
                try:
                    self.backend = PygameBackend(output_device=output_device)
                    logger.info("Audio player initialized with pygame backend")
                except AudioNotAvailableError as e:
                    logger.warning(f"Pygame not available, using dummy backend: {e}")
                    self.backend = DummyBackend()
        elif backend == "dummy":
            self.backend = DummyBackend()
        elif isinstance(backend, AudioBackend):
            self.backend = backend
            logger.info(f"Audio player initialized with custom backend: {type(backend).__name__}")
        else:
            raise ValueError(f"Invalid backend: {backend}")

        # Log platform info
        system = platform.system()
        logger.info(f"Platform: {system}, Audio directory: {self.audio_dir}")

    def play(
        self,
        filename: str,
        volume: float = 1.0,
        loops: int = 0,
    ) -> None:
        """
        Play audio file (synchronous).

        Args:
            filename: Audio file name (relative to audio_dir)
            volume: Volume level (0.0 to 1.0)
            loops: Number of times to loop (0 = play once, -1 = infinite)

        Raises:
            AudioFileNotFoundError: If audio file not found
            AudioError: If playback fails
        """
        filepath = self.audio_dir / filename

        # Skip file check for dummy backend
        if not isinstance(self.backend, DummyBackend) and not filepath.exists():
            raise AudioFileNotFoundError(f"Audio file not found: {filepath}")

        self.backend.play(filepath, volume=volume, loops=loops)

    async def play_async(
        self,
        filename: str,
        volume: float = 1.0,
        loops: int = 0,
    ) -> None:
        """
        Play audio file (asynchronous).

        Runs playback in thread pool to avoid blocking event loop.

        Args:
            filename: Audio file name (relative to audio_dir)
            volume: Volume level (0.0 to 1.0)
            loops: Number of times to loop (0 = play once, -1 = infinite)
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.play, filename, volume, loops)

    def stop(self) -> None:
        """Stop currently playing audio."""
        self.backend.stop()

    def pause(self) -> None:
        """Pause currently playing audio."""
        self.backend.pause()

    def resume(self) -> None:
        """Resume paused audio."""
        self.backend.resume()

    def set_volume(self, volume: float) -> None:
        """
        Set volume for current playback.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.backend.set_volume(volume)

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self.backend.is_playing()

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        return self.backend.get_position()

    def fade_volume(self, target_volume: float, duration: float, steps: int = 20):
        """
        Fade volume to target level (synchronous).

        Args:
            target_volume: Target volume level (0.0 to 1.0)
            duration: Fade duration in seconds
            steps: Number of volume steps
        """
        import time
        current_vol = 1.0  # Assume starting at full volume
        step_duration = duration / steps
        vol_step = (target_volume - current_vol) / steps

        for _ in range(steps):
            current_vol += vol_step
            self.set_volume(current_vol)
            time.sleep(step_duration)

    async def fade_volume_async(
        self, target_volume: float, duration: float, steps: int = 20
    ):
        """
        Fade volume to target level (asynchronous).

        Args:
            target_volume: Target volume level (0.0 to 1.0)
            duration: Fade duration in seconds
            steps: Number of volume steps
        """
        current_vol = 1.0  # Assume starting at full volume
        step_duration = duration / steps
        vol_step = (target_volume - current_vol) / steps

        for _ in range(steps):
            current_vol += vol_step
            self.set_volume(current_vol)
            await asyncio.sleep(step_duration)
