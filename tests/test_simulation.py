"""Tests for fixed-timestep simulation engine.

Covers PHYS-06: accumulator pattern, pause/speed controls, deterministic timestep.
"""
import pytest
from copy import copy

from bigbangsim.simulation.engine import SimulationEngine
from bigbangsim.simulation.state import PhysicsState
from bigbangsim.config import PHYSICS_DT


@pytest.fixture
def engine():
    """Create a fresh SimulationEngine for each test."""
    return SimulationEngine()


class TestSimulationEngine:
    """Tests for the fixed-timestep simulation engine."""

    def test_update_produces_valid_physics_state(self, engine):
        """SimulationEngine.update() must return a valid PhysicsState."""
        state, alpha = engine.update(1.0 / 60.0)
        assert isinstance(state, PhysicsState)
        assert state.cosmic_time > 0
        assert state.scale_factor > 0
        assert state.temperature > 0
        assert 0 <= alpha <= 1.0

    def test_paused_returns_same_state(self, engine):
        """When paused, update() returns the same state regardless of frametime."""
        initial_state = copy(engine.state)
        engine.paused = True

        state1, alpha1 = engine.update(0.1)
        state2, alpha2 = engine.update(1.0)
        state3, alpha3 = engine.update(10.0)

        assert state1.cosmic_time == initial_state.cosmic_time
        assert state2.cosmic_time == initial_state.cosmic_time
        assert state3.cosmic_time == initial_state.cosmic_time
        assert alpha1 == 0.0
        assert alpha2 == 0.0

    def test_speed_multiplier_doubles_advance_rate(self, engine):
        """Speed multiplier of 2.0 should advance cosmic time approximately 2x faster."""
        # Run engine at speed 1.0
        engine1 = SimulationEngine()
        engine1.set_speed(1.0)
        for _ in range(60):
            engine1.update(PHYSICS_DT)

        # Run engine at speed 2.0
        engine2 = SimulationEngine()
        engine2.set_speed(2.0)
        for _ in range(60):
            engine2.update(PHYSICS_DT)

        # Engine2 should have advanced further in screen time
        assert engine2.screen_time > engine1.screen_time * 1.5, (
            f"2x speed screen_time={engine2.screen_time} not >> "
            f"1x speed screen_time={engine1.screen_time}"
        )

    def test_fixed_timestep_accumulator_deterministic(self, engine):
        """Multiple small frametimes should produce same result as fewer larger frametimes.

        This verifies the fixed-timestep accumulator pattern: physics steps
        happen at fixed intervals regardless of how frametime is delivered.
        """
        # Method 1: many small frames
        engine1 = SimulationEngine()
        for _ in range(120):
            engine1.update(PHYSICS_DT / 2.0)

        # Method 2: fewer large frames
        engine2 = SimulationEngine()
        for _ in range(60):
            engine2.update(PHYSICS_DT)

        # Both should have advanced the same amount of screen time
        # (within floating point tolerance)
        rel_diff = abs(engine1.screen_time - engine2.screen_time) / max(engine1.screen_time, 1e-10)
        assert rel_diff < 0.01, (
            f"Accumulator not deterministic: "
            f"screen_time1={engine1.screen_time}, screen_time2={engine2.screen_time}"
        )

    def test_toggle_pause(self, engine):
        """toggle_pause should flip the paused state."""
        assert engine.paused is False
        engine.toggle_pause()
        assert engine.paused is True
        engine.toggle_pause()
        assert engine.paused is False

    def test_set_speed_clamps(self, engine):
        """set_speed should clamp to [MIN_SPEED, MAX_SPEED]."""
        from bigbangsim.config import MIN_SPEED, MAX_SPEED

        engine.set_speed(0.0)  # Below minimum
        assert engine.speed_multiplier == MIN_SPEED

        engine.set_speed(100.0)  # Above maximum
        assert engine.speed_multiplier == MAX_SPEED

        engine.set_speed(2.0)  # Within range
        assert engine.speed_multiplier == 2.0

    def test_increase_decrease_speed(self, engine):
        """increase_speed doubles, decrease_speed halves."""
        engine.set_speed(1.0)
        engine.increase_speed()
        assert engine.speed_multiplier == 2.0
        engine.decrease_speed()
        assert engine.speed_multiplier == 1.0

    def test_screen_time_advances_with_updates(self, engine):
        """screen_time should advance when engine is not paused."""
        initial = engine.screen_time
        for _ in range(10):
            engine.update(PHYSICS_DT)
        assert engine.screen_time > initial

    def test_era_index_in_valid_range(self, engine):
        """Current era index should be in range [0, 10]."""
        state, _ = engine.update(PHYSICS_DT)
        assert 0 <= state.current_era <= 10

    def test_era_progress_in_valid_range(self, engine):
        """Era progress should be in range [0.0, 1.0]."""
        state, _ = engine.update(PHYSICS_DT)
        assert 0.0 <= state.era_progress <= 1.0
