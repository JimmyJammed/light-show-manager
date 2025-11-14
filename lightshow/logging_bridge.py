"""
Logging bridge to connect Python's standard logging to lightshow Logger.

This allows third-party libraries that use Python's standard logging module
(like the govee-python package) to route their logs through lightshow's Logger,
providing unified, color-coded output.

Usage:
    from lightshow import Logger, configure_stdlib_logging

    # Create your logger
    logger = Logger(log_dir="logs")

    # Bridge Python's logging to lightshow Logger
    configure_stdlib_logging(logger)

    # Now any library using Python's logging will route through lightshow Logger
    from govee import GoveeClient
    client = GoveeClient(api_key="...")  # Its logging goes through lightshow Logger
"""

import logging
from typing import Optional
from lightshow.logger import Logger


class LightShowLogHandler(logging.Handler):
    """
    Custom logging handler that routes Python logging to lightshow Logger.

    Maps Python logging levels to lightshow log methods:
    - DEBUG → logger.debug()
    - INFO → logger.info()
    - WARNING → logger.warn()
    - ERROR/CRITICAL → logger.error()
    """

    def __init__(self, lightshow_logger: Logger):
        """
        Initialize handler with a lightshow Logger instance.

        Args:
            lightshow_logger: The lightshow Logger to route messages to
        """
        super().__init__()
        self.lightshow_logger = lightshow_logger

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record by routing it to lightshow Logger.

        Args:
            record: The Python logging.LogRecord to emit
        """
        try:
            # Format the message
            msg = self.format(record)

            # Map Python logging levels to lightshow methods
            if record.levelno >= logging.ERROR:
                self.lightshow_logger.error(msg)
            elif record.levelno >= logging.WARNING:
                self.lightshow_logger.warn(msg)
            elif record.levelno >= logging.INFO:
                self.lightshow_logger.info(msg)
            else:  # DEBUG
                self.lightshow_logger.debug(msg)
        except Exception:
            self.handleError(record)


def configure_stdlib_logging(
    lightshow_logger: Logger,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    logger_names: Optional[list[str]] = None,
) -> None:
    """
    Configure Python's standard logging to route through lightshow Logger.

    This sets up a bridge so that any library using Python's logging module
    will have its output routed through lightshow's Logger, providing unified
    color-coded console output and file logging.

    Args:
        lightshow_logger: The lightshow Logger instance to route to
        level: Minimum logging level to capture (default: logging.INFO)
        format_string: Optional custom format string for log messages.
                      If None, uses just the message without timestamp
                      (since lightshow Logger adds its own timestamp)
        logger_names: Optional list of logger names to configure.
                     If None, configures the root logger (affects all loggers).
                     Example: ["govee", "my_module"]

    Example:
        from lightshow import Logger, configure_stdlib_logging

        # Create logger with file logging
        logger = Logger(log_dir="logs")

        # Bridge all Python logging to lightshow Logger
        configure_stdlib_logging(logger)

        # Now govee package logs will go through lightshow Logger
        from govee import GoveeClient
        client = GoveeClient(api_key="...")

    Example (specific loggers only):
        # Only bridge govee package logging
        configure_stdlib_logging(logger, logger_names=["govee"])
    """
    # Default format: just the message (lightshow adds timestamp)
    if format_string is None:
        format_string = "[%(name)s] %(message)s"

    # Create handler
    handler = LightShowLogHandler(lightshow_logger)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(format_string))

    if logger_names:
        # Configure specific loggers
        for name in logger_names:
            log = logging.getLogger(name)
            log.setLevel(level)
            log.addHandler(handler)
            # Don't propagate to root logger to avoid duplicate logs
            log.propagate = False
    else:
        # Configure root logger (affects all loggers)
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(handler)


def reset_stdlib_logging() -> None:
    """
    Reset Python's standard logging configuration.

    Removes all handlers from the root logger, effectively resetting
    to default Python logging behavior.

    Useful for testing or when you want to revert the logging bridge.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
