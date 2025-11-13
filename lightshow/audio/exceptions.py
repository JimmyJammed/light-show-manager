"""Audio-specific exceptions."""


class AudioError(Exception):
    """Base exception for audio errors."""
    pass


class AudioNotAvailableError(AudioError):
    """Raised when audio system is not available."""
    pass


class AudioFileNotFoundError(AudioError):
    """Raised when audio file is not found."""
    pass


class AudioBackendError(AudioError):
    """Raised when audio backend encounters an error."""
    pass
