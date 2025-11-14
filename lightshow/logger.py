"""
Lightweight console logger for Light Show Manager.

Features:
- Color-coded console output (INFO=white, WARN=yellow, ERROR=red, DEBUG=cyan)
- Timestamp support (optional)
- File logging to timestamped log files (log_YYYY_MM_DD_HH_MM_SS.log)
- Component-based filtering (optional, for user extension)
- Auto-detection of TTY for color support
- Respects NO_COLOR environment variable

Usage:
    from lightshow import Logger

    # Basic logging
    logger = Logger()
    logger.info("Show started")
    logger.warn("Device not responding")
    logger.error("Failed to initialize")
    logger.debug("Event details...")

    # Enable file logging
    logger = Logger(log_dir="logs")
    logger.info("This goes to console AND file")

    # Disable timestamps
    logger = Logger(timestamps=False)

    # Force color on/off
    logger = Logger(color=True)   # Force colors
    logger = Logger(color=False)  # Disable colors
    logger = Logger(color="auto") # Auto-detect (default)

API:
    log(level, msg, end="\\n")     - Generic logging method
    info(msg, end="\\n")           - Info level (white)
    warn(msg, end="\\n")           - Warning level (yellow)
    error(msg, end="\\n")          - Error level (red)
    debug(msg, end="\\n")          - Debug level (cyan)
    close()                        - Close file logging
"""

from __future__ import annotations

import os
import sys
import datetime as dt
from typing import TextIO, Optional, Literal


# ANSI color codes
class _Colors:
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"


# Log level definitions
LogLevel = Literal["info", "warn", "warning", "error", "debug"]

_LEVEL_MAP = {
    "info": (_Colors.WHITE, "INFO"),
    "warn": (_Colors.YELLOW, "WARN"),
    "warning": (_Colors.YELLOW, "WARN"),
    "error": (_Colors.RED, "ERROR"),
    "debug": (_Colors.CYAN, "DEBUG"),
}


class Logger:
    """
    Logger with color-coded console output and optional file logging.

    Args:
        timestamps: Include timestamps in log output (default: True)
        color: Color mode - True, False, or "auto" (default: "auto")
        stream: Output stream for console logging (default: sys.stdout)
        log_dir: Directory for log files. If None, file logging is disabled (default: None)
    """

    def __init__(
        self,
        *,
        timestamps: bool = True,
        color: bool | str = "auto",
        stream: TextIO = sys.stdout,
        log_dir: Optional[str] = None,
    ):
        self._timestamps = timestamps
        self._color_mode = color
        self._stream = stream
        self._log_file: Optional[TextIO] = None
        self._log_file_path: Optional[str] = None

        # Initialize file logging if log_dir provided
        if log_dir:
            self._init_file_logging(log_dir)

    def _should_color(self) -> bool:
        """Determine if colors should be used based on settings and environment."""
        if self._color_mode is True:
            return True
        if self._color_mode is False:
            return False
        # Auto mode
        try:
            # Respect NO_COLOR environment variable
            if "NO_COLOR" in os.environ:
                return False
            return hasattr(self._stream, "isatty") and self._stream.isatty()
        except Exception:
            return False

    def _colorize(self, text: str, color_code: str) -> str:
        """Apply ANSI color codes to text if colors are enabled."""
        if not self._should_color():
            return text
        try:
            return f"{color_code}{text}{_Colors.RESET}"
        except Exception:
            return text

    def _timestamp(self) -> str:
        """Generate current timestamp string."""
        return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _init_file_logging(self, log_dir: str) -> None:
        """
        Initialize file logging to capture logs to a timestamped file.

        Creates: logs/log_YYYY_MM_DD_HH_MM_SS.log

        Args:
            log_dir: Directory path for log files
        """
        # Close existing log file if any
        self.close()

        # Create logs directory if it doesn't exist
        try:
            abs_log_dir = os.path.abspath(log_dir)
            os.makedirs(abs_log_dir, exist_ok=True)
        except Exception as e:
            print(
                f"[WARN] Failed to create log directory '{log_dir}': {e}",
                file=sys.stderr,
            )
            return

        # Generate timestamped filename
        timestamp = dt.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        log_filename = f"log_{timestamp}.log"
        log_path = os.path.join(abs_log_dir, log_filename)

        # Open log file
        try:
            self._log_file = open(log_path, "w", encoding="utf-8", buffering=1)
            self._log_file_path = log_path

            # Write header
            self._log_file.write("=" * 80 + "\n")
            self._log_file.write("Light Show Manager Log\n")
            self._log_file.write(f"Started: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self._log_file.write("=" * 80 + "\n\n")
            self._log_file.flush()

            # Log success to console
            self.info(f"File logging initialized: {log_path}")
        except Exception as e:
            print(f"[ERROR] Failed to open log file '{log_path}': {e}", file=sys.stderr)
            self._log_file = None
            self._log_file_path = None

    def log(self, level: LogLevel, msg: object, *, end: str = "\n") -> None:
        """
        Log a message at the specified level.

        Args:
            level: Log level ("info", "warn", "warning", "error", "debug")
            msg: Message to log (will be converted to string)
            end: Line ending (default: "\\n")
        """
        # Normalize level and get color + label
        k = (level or "info").lower().strip()
        color, label = _LEVEL_MAP.get(k, (_Colors.WHITE, k.upper() or "INFO"))

        # Build plain text line
        parts = []
        if self._timestamps:
            parts.append(self._timestamp())
        parts.append(f"[{label}]")
        parts.append(str(msg))

        plain_line = " ".join(parts)

        # Colorize for console output
        colored_line = self._colorize(plain_line, color)

        # Print to console
        try:
            print(colored_line, file=self._stream, end=end, flush=True)
        except Exception:
            # Fallback to plain stdout
            try:
                print(plain_line, end=end)
            except Exception:
                pass  # Swallow if even printing fails

        # Write to file (INFO, WARN, ERROR only - skip DEBUG unless you want all)
        if self._log_file is not None and label in ("INFO", "WARN", "ERROR"):
            try:
                # Get caller info for better debugging
                import inspect

                caller_frame = None
                context_info = ""
                try:
                    frame = inspect.currentframe()
                    if frame and frame.f_back and frame.f_back.f_back:
                        # Skip one more frame to get actual caller (not log/info/warn/error wrapper)
                        caller_frame = frame.f_back.f_back
                        filename = caller_frame.f_code.co_filename
                        lineno = caller_frame.f_lineno
                        function = caller_frame.f_code.co_name
                        # Make path relative if possible
                        try:
                            filename = os.path.relpath(filename)
                        except Exception:
                            pass
                        context_info = f" [{os.path.basename(filename)}:{lineno} in {function}()]"
                except Exception:
                    pass
                finally:
                    del frame, caller_frame

                # Write to file (plain text, no colors)
                self._log_file.write(f"{plain_line}{context_info}{end}")
                self._log_file.flush()
            except Exception:
                # Don't let file logging errors break the program
                pass

    def info(self, msg: object, *, end: str = "\n") -> None:
        """Log an info message (white)."""
        self.log("info", msg, end=end)

    def warn(self, msg: object, *, end: str = "\n") -> None:
        """Log a warning message (yellow)."""
        self.log("warn", msg, end=end)

    def error(self, msg: object, *, end: str = "\n") -> None:
        """Log an error message (red)."""
        self.log("error", msg, end=end)

    def debug(self, msg: object, *, end: str = "\n") -> None:
        """Log a debug message (cyan)."""
        self.log("debug", msg, end=end)

    def close(self) -> None:
        """Close file logging if active."""
        if self._log_file is not None:
            try:
                self._log_file.write(f"\n{'=' * 80}\n")
                self._log_file.write(
                    f"Log ended: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                self._log_file.write(f"{'=' * 80}\n")
                self._log_file.close()
            except Exception:
                pass
            finally:
                self._log_file = None
                self._log_file_path = None

    @property
    def log_file_path(self) -> Optional[str]:
        """Get the path to the current log file, if any."""
        return self._log_file_path

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close log file on context exit."""
        self.close()
        return False

    def __del__(self):
        """Ensure file is closed on deletion."""
        try:
            self.close()
        except Exception:
            pass


# Convenience: Create a default logger instance for quick usage
_default_logger = Logger()


def log(level: LogLevel, msg: object, *, end: str = "\n") -> None:
    """Log using the default logger instance."""
    _default_logger.log(level, msg, end=end)


def info(msg: object, *, end: str = "\n") -> None:
    """Info log using the default logger instance."""
    _default_logger.info(msg, end=end)


def warn(msg: object, *, end: str = "\n") -> None:
    """Warning log using the default logger instance."""
    _default_logger.warn(msg, end=end)


def error(msg: object, *, end: str = "\n") -> None:
    """Error log using the default logger instance."""
    _default_logger.error(msg, end=end)


def debug(msg: object, *, end: str = "\n") -> None:
    """Debug log using the default logger instance."""
    _default_logger.debug(msg, end=end)
