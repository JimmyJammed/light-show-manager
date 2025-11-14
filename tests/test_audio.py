"""Tests for audio module."""

import asyncio
import pytest
from pathlib import Path
from lightshow.audio import AudioPlayer, AudioBackend, AudioError, AudioFileNotFoundError


class MockAudioBackend(AudioBackend):
    """Mock audio backend for testing."""

    def __init__(self):
        self._is_playing = False
        self._volume = 1.0
        self._paused = False
        self._position = 0.0
        self.play_called = False
        self.stop_called = False
        self.last_played_file = None

    def play(self, filepath: Path, volume: float = 1.0, loops: int = 0) -> None:
        self.play_called = True
        self.last_played_file = filepath
        self._is_playing = True
        self._volume = volume

    def stop(self) -> None:
        self.stop_called = True
        self._is_playing = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def set_volume(self, volume: float) -> None:
        self._volume = volume

    def is_playing(self) -> bool:
        return self._is_playing

    def get_position(self) -> float:
        return self._position


class TestAudioPlayer:
    """Test AudioPlayer class."""

    def test_create_with_dummy_backend(self):
        """Test creating audio player with dummy backend."""
        audio = AudioPlayer(audio_dir="audio", backend="dummy")
        assert audio is not None
        assert audio.audio_dir == Path("audio")

    def test_create_with_custom_backend(self):
        """Test creating audio player with custom backend."""
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir="audio", backend=backend)
        assert audio.backend == backend

    def test_play_with_mock_backend(self, tmp_path):
        """Test playing audio with mock backend."""
        # Create test audio file
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        test_file = audio_dir / "test.mp3"
        test_file.write_text("fake audio data")

        # Create audio player with mock backend
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir=str(audio_dir), backend=backend)

        # Play audio
        audio.play("test.mp3", volume=0.8)

        assert backend.play_called
        assert backend.last_played_file == test_file
        assert backend._volume == 0.8
        assert backend.is_playing()

    def test_play_missing_file(self, tmp_path):
        """Test playing non-existent audio file raises error."""
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()

        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir=str(audio_dir), backend=backend)

        with pytest.raises(AudioFileNotFoundError):
            audio.play("nonexistent.mp3")

    @pytest.mark.asyncio
    async def test_play_async(self, tmp_path):
        """Test async audio playback."""
        # Create test audio file
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        test_file = audio_dir / "test.mp3"
        test_file.write_text("fake audio data")

        # Create audio player
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir=str(audio_dir), backend=backend)

        # Play audio async
        await audio.play_async("test.mp3")

        assert backend.play_called
        assert backend.last_played_file == test_file

    def test_stop(self):
        """Test stopping audio."""
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir="audio", backend=backend)

        audio.stop()
        assert backend.stop_called

    def test_pause_resume(self):
        """Test pausing and resuming audio."""
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir="audio", backend=backend)

        audio.pause()
        assert backend._paused

        audio.resume()
        assert not backend._paused

    def test_set_volume(self):
        """Test setting volume."""
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir="audio", backend=backend)

        audio.set_volume(0.5)
        assert backend._volume == 0.5

    def test_is_playing(self):
        """Test checking if audio is playing."""
        backend = MockAudioBackend()
        backend._is_playing = True
        audio = AudioPlayer(audio_dir="audio", backend=backend)

        assert audio.is_playing()

    def test_get_position(self):
        """Test getting playback position."""
        backend = MockAudioBackend()
        backend._position = 5.5
        audio = AudioPlayer(audio_dir="audio", backend=backend)

        assert audio.get_position() == 5.5

    def test_dummy_backend_operations(self):
        """Test dummy backend doesn't crash."""
        audio = AudioPlayer(audio_dir="audio", backend="dummy")

        # These should all work without errors
        audio.play("test.mp3")
        audio.pause()
        audio.resume()
        audio.set_volume(0.5)
        audio.stop()
        assert isinstance(audio.is_playing(), bool)
        assert isinstance(audio.get_position(), float)


class TestAudioIntegration:
    """Test audio integration with light shows."""

    @pytest.mark.asyncio
    async def test_audio_in_show(self, tmp_path):
        """Test using audio in a show."""
        from lightshow import Show, LightShowManager

        # Create test audio file
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        test_file = audio_dir / "test.mp3"
        test_file.write_text("fake audio data")

        # Create audio player
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir=str(audio_dir), backend=backend)

        # Create show with audio events
        show = Show("audio_test", duration=2.0)
        show.add_sync_event(0.0, lambda: audio.play("test.mp3"))
        show.add_sync_event(1.0, lambda: audio.set_volume(0.5))
        show.add_sync_event(1.5, lambda: audio.stop())

        # Cleanup hook
        def post_show(show_obj, context):
            audio.stop()

        # Run show
        manager = LightShowManager(shows=[show], post_show=post_show)
        await manager.run_show("audio_test")

        # Verify audio was used
        assert backend.play_called
        assert backend.stop_called
        assert backend._volume == 0.5

    @pytest.mark.asyncio
    async def test_audio_with_async_events(self, tmp_path):
        """Test using async audio in show."""
        from lightshow import Show, LightShowManager

        # Create test audio file
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir()
        test_file = audio_dir / "test.mp3"
        test_file.write_text("fake audio data")

        # Create audio player
        backend = MockAudioBackend()
        audio = AudioPlayer(audio_dir=str(audio_dir), backend=backend)

        # Create show with async audio events
        show = Show("async_audio", duration=1.0)
        show.add_async_event(0.0, lambda: audio.play_async("test.mp3"))

        # Run show
        manager = LightShowManager(shows=[show])
        await manager.run_show("async_audio")

        # Verify audio was played
        assert backend.play_called


class TestDummyBackend:
    """Test dummy backend functionality."""

    def test_dummy_backend_basic_operations(self):
        """Test all dummy backend operations."""
        audio = AudioPlayer(audio_dir="audio", backend="dummy")

        # Should not crash
        audio.play("test.mp3", volume=0.8, loops=2)
        audio.pause()
        audio.resume()
        audio.set_volume(0.5)
        audio.stop()

        # Should return sensible values
        assert isinstance(audio.is_playing(), bool)
        assert audio.get_position() == 0.0
