"""Tests for milestone event system and educational content data.

Tests cover:
- MILESTONES list structure and scientific accuracy
- ERA_DESCRIPTIONS completeness
- MilestoneManager trigger logic and notification lifecycle
"""
import pytest


class TestMilestoneData:
    """Tests for educational_content.py static data."""

    def test_milestones_list_has_exactly_20_entries(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        assert len(MILESTONES) == 20

    def test_all_milestone_cosmic_times_are_positive_floats(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        for m in MILESTONES:
            assert isinstance(m.cosmic_time, float)
            assert m.cosmic_time > 0.0, f"Milestone '{m.name}' has non-positive cosmic_time: {m.cosmic_time}"

    def test_milestones_sorted_by_cosmic_time_ascending(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        times = [m.cosmic_time for m in MILESTONES]
        for i in range(len(times) - 1):
            assert times[i] <= times[i + 1], (
                f"Milestones not sorted: [{i}] {times[i]} > [{i+1}] {times[i+1]}"
            )

    def test_each_milestone_has_non_empty_name_and_description(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        for m in MILESTONES:
            assert len(m.name.strip()) > 0, f"Milestone at t={m.cosmic_time} has empty name"
            assert len(m.description.strip()) > 0, f"Milestone '{m.name}' has empty description"

    def test_milestone_era_indices_are_valid(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        for m in MILESTONES:
            assert 0 <= m.era_index <= 10, f"Milestone '{m.name}' has invalid era_index: {m.era_index}"

    def test_milestone_is_frozen_dataclass(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        m = MILESTONES[0]
        with pytest.raises(AttributeError):
            m.name = "Modified"

    def test_milestone_temperature_is_float_or_none(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        for m in MILESTONES:
            assert m.temperature is None or isinstance(m.temperature, (int, float)), (
                f"Milestone '{m.name}' has invalid temperature type: {type(m.temperature)}"
            )


class TestEraDescriptions:
    """Tests for ERA_DESCRIPTIONS dict."""

    def test_era_descriptions_has_exactly_11_entries(self):
        from bigbangsim.presentation.educational_content import ERA_DESCRIPTIONS
        assert len(ERA_DESCRIPTIONS) == 11

    def test_era_descriptions_keys_are_0_through_10(self):
        from bigbangsim.presentation.educational_content import ERA_DESCRIPTIONS
        expected_keys = set(range(11))
        assert set(ERA_DESCRIPTIONS.keys()) == expected_keys

    def test_era_descriptions_values_are_non_empty_strings(self):
        from bigbangsim.presentation.educational_content import ERA_DESCRIPTIONS
        for idx, desc in ERA_DESCRIPTIONS.items():
            assert isinstance(desc, str), f"Era {idx} description is not a string"
            assert len(desc.strip()) > 30, f"Era {idx} description is too short: '{desc}'"


class TestMilestoneManager:
    """Tests for MilestoneManager trigger logic and notification lifecycle."""

    def _make_manager(self, display_duration=5.0, fade_duration=1.0):
        from bigbangsim.presentation.educational_content import MILESTONES
        from bigbangsim.presentation.milestones import MilestoneManager
        return MilestoneManager(
            milestones=list(MILESTONES),
            display_duration=display_duration,
            fade_duration=fade_duration,
        )

    def test_update_triggers_milestone_when_cosmic_time_crosses_threshold(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager()
        # Advance to just past the first milestone's cosmic_time
        first_time = MILESTONES[0].cosmic_time
        triggered = manager.update(first_time, dt=0.016)
        assert len(triggered) == 1
        assert triggered[0].name == MILESTONES[0].name

    def test_update_does_not_retrigger_already_fired_milestones(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager()
        first_time = MILESTONES[0].cosmic_time
        # First update triggers
        manager.update(first_time, dt=0.016)
        # Second update at same time should NOT retrigger
        triggered = manager.update(first_time, dt=0.016)
        assert len(triggered) == 0

    def test_update_triggers_multiple_milestones_when_jumping_forward(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager()
        # Jump to time that covers first 5 milestones
        fifth_time = MILESTONES[4].cosmic_time
        triggered = manager.update(fifth_time, dt=0.016)
        assert len(triggered) == 5

    def test_get_active_notifications_returns_notifications_with_remaining_time(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager(display_duration=5.0)
        first_time = MILESTONES[0].cosmic_time
        manager.update(first_time, dt=0.016)
        notifs = manager.get_active_notifications()
        assert len(notifs) == 1
        assert notifs[0].time_remaining > 0.0

    def test_notifications_expire_after_display_duration(self):
        manager = self._make_manager(display_duration=2.0)
        from bigbangsim.presentation.educational_content import MILESTONES
        first_time = MILESTONES[0].cosmic_time
        # Trigger the milestone
        manager.update(first_time, dt=0.0)
        assert len(manager.get_active_notifications()) == 1
        # Advance time to just before expiry
        manager.update(first_time, dt=1.9)
        assert len(manager.get_active_notifications()) == 1
        # Advance past expiry
        manager.update(first_time, dt=0.2)
        assert len(manager.get_active_notifications()) == 0

    def test_reset_clears_all_triggered_flags_and_notifications(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager()
        # Trigger some milestones
        manager.update(MILESTONES[2].cosmic_time, dt=0.016)
        assert manager.triggered_count > 0
        assert len(manager.get_active_notifications()) > 0
        # Reset
        manager.reset()
        assert manager.triggered_count == 0
        assert len(manager.get_active_notifications()) == 0

    def test_reset_allows_retriggering(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager()
        first_time = MILESTONES[0].cosmic_time
        manager.update(first_time, dt=0.016)
        assert manager.triggered_count == 1
        manager.reset()
        triggered = manager.update(first_time, dt=0.016)
        assert len(triggered) == 1
        assert manager.triggered_count == 1

    def test_triggered_count_property(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager()
        assert manager.triggered_count == 0
        manager.update(MILESTONES[0].cosmic_time, dt=0.016)
        assert manager.triggered_count == 1
        manager.update(MILESTONES[4].cosmic_time, dt=0.016)
        assert manager.triggered_count == 5

    def test_notification_alpha_full_opacity_during_display(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager(display_duration=5.0, fade_duration=1.0)
        first_time = MILESTONES[0].cosmic_time
        manager.update(first_time, dt=0.0)
        notif = manager.get_active_notifications()[0]
        # At full display time, alpha should be 1.0
        alpha = manager.get_notification_alpha(notif)
        assert alpha == 1.0

    def test_notification_alpha_fades_during_last_seconds(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager(display_duration=5.0, fade_duration=1.0)
        first_time = MILESTONES[0].cosmic_time
        manager.update(first_time, dt=0.0)
        # Tick forward 4.5 seconds (0.5s remaining, within 1.0s fade window)
        manager.update(first_time, dt=4.5)
        notif = manager.get_active_notifications()[0]
        alpha = manager.get_notification_alpha(notif)
        assert 0.0 < alpha < 1.0
        assert abs(alpha - 0.5) < 0.01  # 0.5s remaining / 1.0s fade = 0.5 alpha

    def test_uses_next_index_pointer_not_linear_scan(self):
        """Verify the MilestoneManager uses _next_index optimization."""
        from bigbangsim.presentation.milestones import MilestoneManager
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = MilestoneManager(list(MILESTONES))
        assert hasattr(manager, '_next_index')
        assert manager._next_index == 0
        manager.update(MILESTONES[2].cosmic_time, dt=0.016)
        assert manager._next_index == 3  # Advanced past first 3

    def test_notification_has_total_duration(self):
        from bigbangsim.presentation.educational_content import MILESTONES
        manager = self._make_manager(display_duration=5.0)
        manager.update(MILESTONES[0].cosmic_time, dt=0.0)
        notif = manager.get_active_notifications()[0]
        assert notif.total_duration == 5.0
