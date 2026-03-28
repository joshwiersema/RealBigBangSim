"""Milestone event system for BigBangSim presentation layer.

Provides MilestoneManager which tracks cosmic time, triggers milestone events
exactly once at their threshold times, and manages a notification queue with
timed fade-out for HUD display.

Uses an advancing index pointer (O(1) per frame) rather than linear scan
for efficient milestone triggering.
"""
from __future__ import annotations

from dataclasses import dataclass

from bigbangsim.presentation.educational_content import Milestone


@dataclass
class MilestoneNotification:
    """An active milestone notification being displayed on the HUD.

    Attributes:
        milestone: The milestone that triggered this notification.
        time_remaining: Seconds until the notification disappears.
        total_duration: Total display time in seconds, for alpha calculation.
    """
    milestone: Milestone
    time_remaining: float
    total_duration: float


class MilestoneManager:
    """Manages milestone triggering and notification lifecycle.

    Uses a sorted milestone list with a monotonically advancing index pointer
    (_next_index) for O(1) trigger checks per frame. Milestones fire exactly
    once when cosmic_time crosses their threshold.

    Args:
        milestones: List of Milestone objects (will be sorted by cosmic_time).
        display_duration: Seconds a notification stays fully visible.
        fade_duration: Seconds for the notification to fade out at the end.
    """

    def __init__(
        self,
        milestones: list[Milestone],
        display_duration: float = 5.0,
        fade_duration: float = 1.0,
    ) -> None:
        self._milestones = sorted(milestones, key=lambda m: m.cosmic_time)
        self._display_duration = display_duration
        self._fade_duration = fade_duration
        self._triggered: list[bool] = [False] * len(self._milestones)
        self._active: list[MilestoneNotification] = []
        self._next_index: int = 0

    def update(self, cosmic_time: float, dt: float) -> list[Milestone]:
        """Advance milestone state for the current frame.

        Checks if any milestones should fire at the given cosmic_time,
        and ticks down active notification timers.

        Args:
            cosmic_time: Current cosmic time in seconds after the Big Bang.
            dt: Frame delta time in seconds (wall clock) for notification decay.

        Returns:
            List of newly triggered Milestone objects this frame.
        """
        newly_triggered: list[Milestone] = []

        # Advance pointer: fire all milestones whose threshold has been reached
        while (
            self._next_index < len(self._milestones)
            and cosmic_time >= self._milestones[self._next_index].cosmic_time
        ):
            milestone = self._milestones[self._next_index]
            self._triggered[self._next_index] = True
            self._active.append(
                MilestoneNotification(
                    milestone=milestone,
                    time_remaining=self._display_duration,
                    total_duration=self._display_duration,
                )
            )
            newly_triggered.append(milestone)
            self._next_index += 1

        # Tick down active notification timers and remove expired ones
        for notif in self._active:
            notif.time_remaining -= dt
        self._active = [n for n in self._active if n.time_remaining > 0.0]

        return newly_triggered

    def get_active_notifications(self) -> list[MilestoneNotification]:
        """Return currently active (non-expired) notifications.

        Returns:
            List of MilestoneNotification objects with positive time_remaining.
        """
        return list(self._active)

    def get_notification_alpha(self, notif: MilestoneNotification) -> float:
        """Calculate display alpha for a notification.

        Full opacity during display period, linear fade from 1.0 to 0.0
        during the last fade_duration seconds.

        Args:
            notif: The notification to calculate alpha for.

        Returns:
            Alpha value between 0.0 and 1.0.
        """
        if notif.time_remaining <= self._fade_duration:
            return max(0.0, notif.time_remaining / self._fade_duration)
        return 1.0

    def reset(self) -> None:
        """Clear all triggered flags, reset pointer, and remove notifications.

        Call this when restarting the simulation timeline.
        """
        self._triggered = [False] * len(self._milestones)
        self._next_index = 0
        self._active.clear()

    @property
    def triggered_count(self) -> int:
        """Return the number of milestones triggered so far."""
        return sum(self._triggered)
