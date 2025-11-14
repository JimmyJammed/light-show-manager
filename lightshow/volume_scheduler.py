"""
Time-based volume scheduling for neighborhood-friendly light shows.

Automatically adjusts volume based on time of day to respect neighbors'
quiet hours while maintaining good audio during peak evening hours.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class VolumeScheduler:
    """
    Schedule volume levels based on time of day.

    Perfect for outdoor/neighborhood light shows where you want to be
    respectful of neighbors while still having good audio during peak hours.

    Features:
    - Configurable time windows (HIGH, MEDIUM, LOW, QUIET)
    - Per-show volume overrides
    - Graceful fallback to default volumes

    Example:
        scheduler = VolumeScheduler(
            high_hours=(18, 21),      # 6pm-9pm: 80%
            medium_hours=(21, 22),    # 9pm-10pm: 70%
            low_hours=(22, 22, 30),   # 10pm-10:30pm: 60%
            default_volume=70
        )

        # Get volume for current time
        volume = scheduler.get_volume()

        # Get volume for specific show and time
        volume = scheduler.get_volume(show_name="starcourt")

        # Add per-show overrides
        scheduler.set_show_volumes(
            "starcourt",
            high=85, medium=75, low=65, quiet=55
        )
    """

    def __init__(
        self,
        high_hours: Tuple[int, int] = (18, 21),
        medium_hours: Tuple[int, int] = (21, 22),
        low_hours: Tuple[int, int, int] = (22, 22, 30),
        default_volume: int = 70,
        high_volume: int = 80,
        medium_volume: int = 70,
        low_volume: int = 60,
        quiet_volume: int = 50,
    ):
        """
        Initialize volume scheduler.

        Args:
            high_hours: (start_hour, end_hour) for HIGH volume period
            medium_hours: (start_hour, end_hour) for MEDIUM volume period
            low_hours: (start_hour, end_hour, end_minute) for LOW volume period
            default_volume: Volume to use outside scheduled hours
            high_volume: Volume level for HIGH period
            medium_volume: Volume level for MEDIUM period
            low_volume: Volume level for LOW period
            quiet_volume: Volume level for QUIET period (late night)
        """
        # Time windows
        self.high_start = high_hours[0]
        self.high_end = high_hours[1]
        self.medium_start = medium_hours[0]
        self.medium_end = medium_hours[1]
        self.low_start = low_hours[0]
        self.low_end = low_hours[1]
        self.low_end_minute = low_hours[2] if len(low_hours) > 2 else 59

        # Default volumes
        self.default_volume = self._clamp_volume(default_volume)
        self.high_volume = self._clamp_volume(high_volume)
        self.medium_volume = self._clamp_volume(medium_volume)
        self.low_volume = self._clamp_volume(low_volume)
        self.quiet_volume = self._clamp_volume(quiet_volume)

        # Per-show overrides: show_name -> {high, medium, low, quiet}
        self._show_volumes: Dict[str, Dict[str, int]] = {}

        logger.info(
            f"Volume scheduler initialized: "
            f"HIGH {self.high_start}:00-{self.high_end}:00 ({self.high_volume}%), "
            f"MEDIUM {self.medium_start}:00-{self.medium_end}:00 ({self.medium_volume}%), "
            f"LOW {self.low_start}:00-{self.low_end}:{self.low_end_minute:02d} ({self.low_volume}%), "
            f"QUIET after ({self.quiet_volume}%), "
            f"default {self.default_volume}%"
        )

    @staticmethod
    def _clamp_volume(volume: int) -> int:
        """Clamp volume to 0-100 range."""
        return max(0, min(100, volume))

    def set_show_volumes(
        self,
        show_name: str,
        high: Optional[int] = None,
        medium: Optional[int] = None,
        low: Optional[int] = None,
        quiet: Optional[int] = None,
    ) -> None:
        """
        Set per-show volume overrides.

        Args:
            show_name: Show name to configure
            high: Volume for HIGH period (6-9pm typically)
            medium: Volume for MEDIUM period (9-10pm typically)
            low: Volume for LOW period (10-10:30pm typically)
            quiet: Volume for QUIET period (late night)

        Example:
            scheduler.set_show_volumes(
                "starcourt",
                high=85,      # Louder during peak hours
                medium=75,
                low=65,
                quiet=55
            )
        """
        if show_name not in self._show_volumes:
            self._show_volumes[show_name] = {}

        if high is not None:
            self._show_volumes[show_name]["high"] = self._clamp_volume(high)
        if medium is not None:
            self._show_volumes[show_name]["medium"] = self._clamp_volume(medium)
        if low is not None:
            self._show_volumes[show_name]["low"] = self._clamp_volume(low)
        if quiet is not None:
            self._show_volumes[show_name]["quiet"] = self._clamp_volume(quiet)

        logger.info(f"Set volume overrides for '{show_name}': {self._show_volumes[show_name]}")

    def get_volume(
        self, show_name: Optional[str] = None, now: Optional[datetime] = None
    ) -> Tuple[int, str]:
        """
        Get appropriate volume for current time and show.

        Args:
            show_name: Optional show name for per-show overrides
            now: Optional datetime (defaults to current time)

        Returns:
            Tuple of (volume_percent, period_name)
            period_name is one of: "HIGH", "MEDIUM", "LOW", "QUIET", "OFF_HOURS"

        Example:
            volume, period = scheduler.get_volume("starcourt")
            print(f"Volume: {volume}% ({period})")
        """
        now = now or datetime.now()
        hour = now.hour
        minute = now.minute

        # Determine time period
        period = self._get_period(hour, minute)

        # Get base volume for period
        if period == "HIGH":
            base_volume = self.high_volume
        elif period == "MEDIUM":
            base_volume = self.medium_volume
        elif period == "LOW":
            base_volume = self.low_volume
        elif period == "QUIET":
            base_volume = self.quiet_volume
        else:  # OFF_HOURS
            base_volume = self.default_volume

        # Check for per-show override
        if show_name and show_name in self._show_volumes:
            period_key = period.lower()
            if period_key in self._show_volumes[show_name]:
                volume = self._show_volumes[show_name][period_key]
                logger.debug(
                    f"Volume for '{show_name}' at {now.strftime('%I:%M %p')}: "
                    f"{volume}% (period: {period}, show override)"
                )
                return volume, period

        logger.debug(
            f"Volume for '{show_name or 'default'}' at {now.strftime('%I:%M %p')}: "
            f"{base_volume}% (period: {period})"
        )
        return base_volume, period

    def _get_period(self, hour: int, minute: int) -> str:
        """
        Determine which time period current time falls into.

        Returns:
            One of: "HIGH", "MEDIUM", "LOW", "QUIET", "OFF_HOURS"
        """
        # HIGH period (e.g., 6-9pm)
        if self.high_start <= hour < self.high_end:
            return "HIGH"

        # MEDIUM period (e.g., 9-10pm)
        if self.medium_start <= hour < self.medium_end:
            return "MEDIUM"

        # LOW period (e.g., 10pm-10:30pm)
        if hour == self.low_start and minute < self.low_end_minute:
            return "LOW"
        if self.low_start < hour < self.low_end:
            return "LOW"

        # QUIET period (late night, e.g., after 10:30pm)
        if hour >= 22:
            if hour > self.low_end or (hour == self.low_end and minute >= self.low_end_minute):
                return "QUIET"

        # OFF_HOURS (before scheduled period starts)
        return "OFF_HOURS"

    def format_schedule(self) -> str:
        """
        Format the volume schedule as a human-readable string.

        Returns:
            Formatted schedule description
        """
        lines = [
            "Volume Schedule:",
            f"  HIGH:   {self.high_start}:00-{self.high_end}:00 → {self.high_volume}%",
            f"  MEDIUM: {self.medium_start}:00-{self.medium_end}:00 → {self.medium_volume}%",
            f"  LOW:    {self.low_start}:00-{self.low_end}:{self.low_end_minute:02d} → {self.low_volume}%",
            f"  QUIET:  After {self.low_end}:{self.low_end_minute:02d} → {self.quiet_volume}%",
            f"  OFF_HOURS: Before {self.high_start}:00 → {self.default_volume}%",
        ]

        if self._show_volumes:
            lines.append("\nShow Overrides:")
            for show_name, volumes in self._show_volumes.items():
                vol_str = ", ".join(f"{k}={v}%" for k, v in volumes.items())
                lines.append(f"  {show_name}: {vol_str}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"VolumeScheduler("
            f"high={self.high_start}-{self.high_end}h, "
            f"medium={self.medium_start}-{self.medium_end}h, "
            f"low={self.low_start}-{self.low_end}h, "
            f"shows={len(self._show_volumes)})"
        )
