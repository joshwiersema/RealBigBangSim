"""Piecewise logarithmic timeline controller.

Maps wall-clock screen time to cosmic time spanning 60+ orders of magnitude.
Each cosmological era gets a configurable screen time budget. Within each era,
time is mapped logarithmically between the era's cosmic start and end times.

This is the single most important architectural component (Pitfall 1 from
research): getting the piecewise logarithmic mapping right prevents having to
rewrite every downstream system.
"""
import math
from typing import List, Tuple

from bigbangsim.simulation.eras import EraDefinition


class TimelineController:
    """Piecewise logarithmic mapping between screen time and cosmic time.

    Pre-computes cumulative screen time boundaries at construction for
    efficient lookups during the simulation loop.

    Args:
        eras: List of EraDefinition objects defining the cosmic timeline.
    """

    def __init__(self, eras: List[EraDefinition]) -> None:
        self._eras = eras
        # Pre-compute cumulative screen time boundaries
        self._screen_starts: List[float] = []
        cumulative = 0.0
        for era in eras:
            self._screen_starts.append(cumulative)
            cumulative += era.screen_seconds
        self._total_duration = cumulative

        # Pre-compute log boundaries for each era
        self._log_starts: List[float] = []
        self._log_ends: List[float] = []
        for era in eras:
            self._log_starts.append(math.log10(max(era.cosmic_start, 1e-45)))
            self._log_ends.append(math.log10(era.cosmic_end))

    def screen_to_cosmic(self, screen_time: float) -> float:
        """Convert screen (wall-clock) time to cosmic time.

        Uses piecewise logarithmic interpolation within each era.

        Args:
            screen_time: Wall-clock playback position in seconds.

        Returns:
            Cosmic time in seconds after the Big Bang.
        """
        # Clamp to valid range
        screen_time = max(0.0, min(screen_time, self._total_duration))

        # Find which era this screen_time falls in
        era_idx = self._find_era_by_screen_time(screen_time)
        era = self._eras[era_idx]

        # Fraction within this era's screen time allocation
        era_offset = screen_time - self._screen_starts[era_idx]
        frac = era_offset / era.screen_seconds if era.screen_seconds > 0 else 0.0
        frac = max(0.0, min(1.0, frac))

        # Logarithmic interpolation between era's cosmic boundaries
        log_start = self._log_starts[era_idx]
        log_end = self._log_ends[era_idx]
        cosmic_time = 10.0 ** (log_start + frac * (log_end - log_start))

        return cosmic_time

    def cosmic_to_screen(self, cosmic_time: float) -> float:
        """Convert cosmic time to screen (wall-clock) time.

        Inverse of screen_to_cosmic for timeline bar display.

        Args:
            cosmic_time: Time in seconds after the Big Bang.

        Returns:
            Screen time in seconds.
        """
        # Clamp to valid range
        cosmic_time = max(self._eras[0].cosmic_start, cosmic_time)

        # Find which era this cosmic time falls in
        era_idx = self._find_era_by_cosmic_time(cosmic_time)
        era = self._eras[era_idx]

        # Logarithmic fraction within this era
        log_start = self._log_starts[era_idx]
        log_end = self._log_ends[era_idx]
        log_span = log_end - log_start

        if log_span > 0:
            frac = (math.log10(max(cosmic_time, 1e-45)) - log_start) / log_span
        else:
            frac = 0.0

        frac = max(0.0, min(1.0, frac))
        screen_time = self._screen_starts[era_idx] + frac * era.screen_seconds

        return screen_time

    def get_current_era(self, cosmic_time: float) -> Tuple[int, float]:
        """Get the current era index and progress within that era.

        Args:
            cosmic_time: Time in seconds after the Big Bang.

        Returns:
            Tuple of (era_index, era_progress) where era_progress is 0.0-1.0.
        """
        era_idx = self._find_era_by_cosmic_time(cosmic_time)
        era = self._eras[era_idx]

        log_start = self._log_starts[era_idx]
        log_end = self._log_ends[era_idx]
        log_span = log_end - log_start

        if log_span > 0:
            progress = (math.log10(max(cosmic_time, 1e-45)) - log_start) / log_span
        else:
            progress = 0.0

        progress = max(0.0, min(1.0, progress))
        return era_idx, progress

    def total_duration(self) -> float:
        """Return the total screen time duration in seconds."""
        return self._total_duration

    def _find_era_by_screen_time(self, screen_time: float) -> int:
        """Find the era index for a given screen time.

        Uses the pre-computed cumulative screen time boundaries.

        Args:
            screen_time: Wall-clock playback position in seconds.

        Returns:
            Era index (0-10).
        """
        for i in range(len(self._eras) - 1, -1, -1):
            if screen_time >= self._screen_starts[i]:
                return i
        return 0

    def _find_era_by_cosmic_time(self, cosmic_time: float) -> int:
        """Find the era index for a given cosmic time.

        When multiple eras overlap in cosmic time (e.g., Grand Unification
        and Inflation both start at 1e-36), returns the era that actually
        contains the cosmic time within its [cosmic_start, cosmic_end] range.
        If multiple eras fully contain the time, returns the highest-index era
        among them. Falls back to the last era whose start is <= cosmic_time.

        Args:
            cosmic_time: Time in seconds after the Big Bang.

        Returns:
            Era index (0-10).
        """
        # First try: find eras that fully contain the cosmic time
        best = -1
        for i in range(len(self._eras)):
            era = self._eras[i]
            if era.cosmic_start <= cosmic_time <= era.cosmic_end:
                best = i
        if best >= 0:
            return best

        # Fallback: last era whose start is <= cosmic_time
        for i in range(len(self._eras) - 1, -1, -1):
            if cosmic_time >= self._eras[i].cosmic_start:
                return i
        return 0
