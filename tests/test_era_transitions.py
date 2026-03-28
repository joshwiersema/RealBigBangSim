"""Unit tests for EraTransitionManager.

Tests validate blend factor computation, smoothstep curve, transition
lifecycle, and state management WITHOUT requiring a real GPU context.
Uses the same mock-based strategy as test_postprocessing.py.
"""
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_transition(width=1280, height=720):
    """Helper to construct EraTransitionManager with a mocked context.

    Returns (transition_manager, mock_ctx) so tests can inspect both.
    """
    from bigbangsim.rendering.era_transition import EraTransitionManager

    mock_ctx = MagicMock()
    mock_ctx.texture.return_value = MagicMock()
    mock_ctx.framebuffer.return_value = MagicMock()
    mock_ctx.program.return_value = MagicMock()

    with patch(
        "bigbangsim.rendering.era_transition.load_shader_source",
        return_value="#version 430\nvoid main() {}",
    ), patch(
        "bigbangsim.rendering.era_transition.geometry"
    ) as mock_geom:
        mock_geom.quad_fs.return_value = MagicMock()
        tm = EraTransitionManager(mock_ctx, width, height)

    return tm, mock_ctx


class TestEraTransitionDefaults:
    """Test initial state of EraTransitionManager."""

    def test_not_in_transition_initially(self):
        """Transition manager starts with in_transition=False."""
        tm, _ = _make_mock_transition()
        assert tm.in_transition is False

    def test_blend_factor_starts_at_zero(self):
        """Blend factor starts at 0.0."""
        tm, _ = _make_mock_transition()
        assert tm.blend_factor == 0.0

    def test_prev_era_starts_at_negative_one(self):
        """Internal _prev_era starts at -1 (uninitialized)."""
        tm, _ = _make_mock_transition()
        assert tm._prev_era == -1

    def test_default_transition_duration(self):
        """Default transition duration is 2.0 seconds."""
        tm, _ = _make_mock_transition()
        assert tm.transition_duration == 2.0


class TestEraTransitionCheckTransition:
    """Test the check_transition lifecycle."""

    def test_first_frame_no_transition(self):
        """First call initializes _prev_era without starting transition."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        assert tm.in_transition is False
        assert tm._prev_era == 0

    def test_same_era_no_transition(self):
        """Repeated calls with same era do not trigger transition."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(0, 0.016, 2.0)
        assert tm.in_transition is False

    def test_era_change_starts_transition(self):
        """Changing era triggers transition start."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)  # init
        tm.check_transition(1, 0.016, 2.0)  # era changes: 0 -> 1
        assert tm.in_transition is True
        assert tm.outgoing_era == 0
        assert tm.incoming_era == 1

    def test_blend_factor_starts_near_zero(self):
        """Blend factor is near 0.0 at the start of transition."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(1, 0.016, 2.0)
        # After 0.016s with 2.0s duration: very small
        assert tm.blend_factor < 0.05

    def test_blend_factor_reaches_one(self):
        """Blend factor reaches 1.0 after transition_duration seconds."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(1, 0.016, 2.0)  # start transition
        # Advance past full duration
        tm.check_transition(1, 3.0, 2.0)
        assert tm.blend_factor >= 1.0

    def test_transition_ends_after_duration(self):
        """in_transition becomes False after blend reaches 1.0."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(1, 0.016, 2.0)  # start transition
        tm.check_transition(1, 3.0, 2.0)   # complete transition
        assert tm.in_transition is False

    def test_prev_era_updated_after_transition(self):
        """_prev_era is updated to the new era after transition completes."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(1, 0.016, 2.0)
        tm.check_transition(1, 3.0, 2.0)
        assert tm._prev_era == 1


class TestEraTransitionSmoothstep:
    """Test smoothstep blend factor curve."""

    def test_smoothstep_at_midpoint(self):
        """At t=0.5 duration, blend is approximately 0.5 (smoothstep)."""
        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(1, 0.0, 2.0)  # start, elapsed=0
        tm.check_transition(1, 1.0, 2.0)  # half of 2.0s
        # smoothstep(0.5) = 0.5*0.5*(3-2*0.5) = 0.25*2 = 0.5
        assert abs(tm.blend_factor - 0.5) < 0.05

    def test_smoothstep_at_quarter(self):
        """At t=0.25 duration, blend follows smoothstep curve."""
        from bigbangsim.rendering.era_transition import _smoothstep

        tm, _ = _make_mock_transition()
        tm.check_transition(0, 0.016, 2.0)
        tm.check_transition(1, 0.0, 2.0)
        tm.check_transition(1, 0.5, 2.0)  # 0.25 of 2.0s duration
        expected = _smoothstep(0.5 / 2.0)
        assert abs(tm.blend_factor - expected) < 0.05

    def test_smoothstep_function_bounds(self):
        """smoothstep returns 0.0 at t=0 and 1.0 at t=1."""
        from bigbangsim.rendering.era_transition import _smoothstep

        assert _smoothstep(0.0) == 0.0
        assert _smoothstep(1.0) == 1.0

    def test_smoothstep_clamps_negative(self):
        """smoothstep clamps negative input to 0.0."""
        from bigbangsim.rendering.era_transition import _smoothstep

        assert _smoothstep(-0.5) == 0.0

    def test_smoothstep_clamps_above_one(self):
        """smoothstep clamps input > 1.0 to 1.0."""
        from bigbangsim.rendering.era_transition import _smoothstep

        assert _smoothstep(1.5) == 1.0


class TestEraTransitionMethods:
    """Test that required methods exist and are callable."""

    def test_has_begin_outgoing(self):
        """Transition manager has begin_outgoing method."""
        tm, _ = _make_mock_transition()
        assert callable(tm.begin_outgoing)

    def test_has_composite(self):
        """Transition manager has composite method."""
        tm, _ = _make_mock_transition()
        assert callable(tm.composite)

    def test_has_resize(self):
        """Transition manager has resize method."""
        tm, _ = _make_mock_transition()
        assert callable(tm.resize)

    def test_has_release(self):
        """Transition manager has release method."""
        tm, _ = _make_mock_transition()
        assert callable(tm.release)

    def test_begin_outgoing_uses_fbo(self):
        """begin_outgoing should use() and clear() the transition FBO."""
        tm, _ = _make_mock_transition()
        tm.begin_outgoing()
        tm.transition_fbo.use.assert_called_once()
        tm.transition_fbo.clear.assert_called_once()


class TestEraTransitionConstruction:
    """Test GPU resource creation."""

    def test_creates_texture_with_rgba16f(self):
        """Transition texture uses RGBA16F (dtype='f2')."""
        width, height = 1280, 720
        tm, mock_ctx = _make_mock_transition(width, height)
        first_texture_call = mock_ctx.texture.call_args_list[0]
        assert first_texture_call[0][0] == (width, height)
        assert first_texture_call[0][1] == 4  # RGBA
        assert first_texture_call[1].get("dtype") == "f2"

    def test_creates_one_framebuffer(self):
        """One FBO created for transition rendering."""
        tm, mock_ctx = _make_mock_transition()
        assert mock_ctx.framebuffer.call_count == 1

    def test_creates_one_program(self):
        """One shader program created (crossfade composite)."""
        tm, mock_ctx = _make_mock_transition()
        assert mock_ctx.program.call_count == 1
