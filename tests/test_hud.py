"""Tests for HUD overlay manager (HUD-01..HUD-05).

Tests cover:
- HUDManager visibility toggle
- format_physics_value scientific / fixed-point formatting
- format_cosmic_time unit selection
- render() skips when invisible (mocked imgui)
"""
from unittest.mock import patch, MagicMock

import pytest


class TestHUDManagerState:
    """Tests for HUDManager toggle and visibility state."""

    def test_hud_visible_default(self):
        from bigbangsim.presentation.hud import HUDManager
        hud = HUDManager()
        assert hud.visible is True

    def test_hud_toggle(self):
        from bigbangsim.presentation.hud import HUDManager
        hud = HUDManager()
        assert hud.visible is True
        hud.toggle()
        assert hud.visible is False
        hud.toggle()
        assert hud.visible is True


class TestFormatPhysicsValue:
    """Tests for the format_physics_value helper."""

    def test_format_physics_value_large(self):
        from bigbangsim.presentation.hud import format_physics_value
        result = format_physics_value(1e32, "K")
        assert result == "1.00e+32 K"

    def test_format_physics_value_small(self):
        from bigbangsim.presentation.hud import format_physics_value
        result = format_physics_value(9.47e-27, "kg/m^3")
        assert result == "9.47e-27 kg/m^3"

    def test_format_physics_value_medium(self):
        from bigbangsim.presentation.hud import format_physics_value
        result = format_physics_value(2725.0, "K")
        assert result == "2725.0000 K"

    def test_format_physics_value_zero(self):
        from bigbangsim.presentation.hud import format_physics_value
        result = format_physics_value(0.0, "K")
        # 0.0 < 1e-3 is False (abs(0) = 0 which is < 1e-3), so scientific
        assert "0.00" in result
        assert "K" in result

    def test_format_physics_value_negative_large(self):
        from bigbangsim.presentation.hud import format_physics_value
        result = format_physics_value(-1e10, "K")
        assert "-1.00e+10 K" == result


class TestFormatCosmicTime:
    """Tests for the format_cosmic_time helper."""

    def test_format_cosmic_time_seconds(self):
        from bigbangsim.presentation.hud import format_cosmic_time
        result = format_cosmic_time(1e-43)
        assert "s" in result
        assert "e-43" in result

    def test_format_cosmic_time_minutes(self):
        from bigbangsim.presentation.hud import format_cosmic_time
        result = format_cosmic_time(180.0)
        assert "min" in result
        assert "3.0" in result

    def test_format_cosmic_time_hours(self):
        from bigbangsim.presentation.hud import format_cosmic_time
        result = format_cosmic_time(7200.0)
        assert "hr" in result
        assert "2.0" in result

    def test_format_cosmic_time_years(self):
        from bigbangsim.presentation.hud import format_cosmic_time
        result = format_cosmic_time(1.2e13)
        assert "yr" in result

    def test_format_cosmic_time_myr(self):
        from bigbangsim.presentation.hud import format_cosmic_time
        # 500 Myr in seconds = 500e6 * 365.25 * 86400
        secs = 500e6 * 365.25 * 86400
        result = format_cosmic_time(secs)
        assert "Myr" in result

    def test_format_cosmic_time_gyr(self):
        from bigbangsim.presentation.hud import format_cosmic_time
        result = format_cosmic_time(4.35e17)
        assert "Gyr" in result


class TestHUDConstants:
    """Tests for module-level constants."""

    def test_era_colors_has_11_entries(self):
        from bigbangsim.presentation.hud import ERA_COLORS
        assert len(ERA_COLORS) == 11

    def test_era_colors_are_rgba_tuples(self):
        from bigbangsim.presentation.hud import ERA_COLORS
        for i, color in enumerate(ERA_COLORS):
            assert len(color) == 4, f"ERA_COLORS[{i}] is not RGBA: {color}"
            for c in color:
                assert 0.0 <= c <= 1.0, f"ERA_COLORS[{i}] value out of range: {c}"

    def test_hud_flags_is_nonzero_int(self):
        from bigbangsim.presentation.hud import HUD_FLAGS
        assert isinstance(HUD_FLAGS, int)
        assert HUD_FLAGS != 0


class TestHUDRender:
    """Tests that render() respects visibility state (mocked imgui)."""

    def test_render_skipped_when_invisible(self):
        from bigbangsim.presentation.hud import HUDManager
        hud = HUDManager()
        hud.visible = False

        # Mock all the dependencies that render() would call
        state = MagicMock()
        sim = MagicMock()
        milestones = MagicMock()

        with patch("bigbangsim.presentation.hud.imgui") as mock_imgui:
            hud.render(state, sim, milestones, True, [])
            # imgui.begin should NOT be called when invisible
            mock_imgui.begin.assert_not_called()
            mock_imgui.get_io.assert_not_called()
