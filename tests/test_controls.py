"""Tests for simulation control interface (CAMR-04).

Tests the SimulationEngine's pause/resume and speed control methods.
No GPU required -- tests the engine's control API directly.
"""
import pytest

from bigbangsim.config import MIN_SPEED, MAX_SPEED, DEFAULT_SPEED
from bigbangsim.simulation.engine import SimulationEngine


class TestPauseControl:
    """Play/pause toggle behavior."""

    def test_engine_starts_unpaused(self):
        engine = SimulationEngine()
        assert engine.paused is False

    def test_toggle_pause_flips_state(self):
        engine = SimulationEngine()
        engine.toggle_pause()
        assert engine.paused is True

    def test_toggle_pause_twice_returns_to_original(self):
        engine = SimulationEngine()
        engine.toggle_pause()
        engine.toggle_pause()
        assert engine.paused is False


class TestSpeedControl:
    """Speed multiplier adjustment and clamping."""

    def test_default_speed(self):
        engine = SimulationEngine()
        assert engine.speed_multiplier == DEFAULT_SPEED

    def test_increase_speed_doubles(self):
        engine = SimulationEngine()
        engine.increase_speed()
        assert engine.speed_multiplier == DEFAULT_SPEED * 2.0

    def test_decrease_speed_halves(self):
        engine = SimulationEngine()
        engine.decrease_speed()
        assert engine.speed_multiplier == DEFAULT_SPEED / 2.0

    def test_speed_clamped_to_min(self):
        engine = SimulationEngine()
        engine.set_speed(0.1)
        assert engine.speed_multiplier == MIN_SPEED

    def test_speed_clamped_to_max(self):
        engine = SimulationEngine()
        engine.set_speed(100.0)
        assert engine.speed_multiplier == MAX_SPEED


class TestPausedUpdate:
    """Update behavior when paused."""

    def test_update_paused_returns_unchanged_state(self):
        engine = SimulationEngine()
        engine.toggle_pause()
        initial_time = engine.state.cosmic_time
        state, alpha = engine.update(1.0)
        assert state.cosmic_time == initial_time
