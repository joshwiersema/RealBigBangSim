"""Tests for PhysicsState dataclass.

Verifies construction, linear interpolation (lerp), discrete field handling,
and rendering layer isolation.
"""
import inspect
import pytest
from bigbangsim.simulation.state import PhysicsState


def test_construction():
    """PhysicsState can be constructed with all required fields."""
    state = PhysicsState(
        cosmic_time=1e10,
        scale_factor=0.001,
        temperature=3000.0,
        matter_density=1e-18,
        radiation_density=1e-20,
        hubble_param=100.0,
        current_era=6,
        era_progress=0.5,
    )
    assert state.cosmic_time == 1e10
    assert state.current_era == 6
    assert state.scale_factor == 0.001
    assert state.temperature == 3000.0
    assert state.matter_density == 1e-18
    assert state.radiation_density == 1e-20
    assert state.hubble_param == 100.0
    assert state.era_progress == 0.5


def test_lerp_alpha_zero():
    """lerp(other, alpha=0.0) returns self's values."""
    a = PhysicsState(1.0, 0.1, 1000.0, 1e-10, 1e-12, 200.0, 3, 0.2)
    b = PhysicsState(2.0, 0.2, 500.0, 5e-11, 5e-13, 150.0, 4, 0.8)
    result = a.lerp(b, 0.0)
    assert result.cosmic_time == pytest.approx(1.0)
    assert result.scale_factor == pytest.approx(0.1)
    assert result.temperature == pytest.approx(1000.0)
    assert result.matter_density == pytest.approx(1e-10)
    assert result.radiation_density == pytest.approx(1e-12)
    assert result.hubble_param == pytest.approx(200.0)
    assert result.era_progress == pytest.approx(0.2)


def test_lerp_alpha_one():
    """lerp(other, alpha=1.0) returns other's values."""
    a = PhysicsState(1.0, 0.1, 1000.0, 1e-10, 1e-12, 200.0, 3, 0.2)
    b = PhysicsState(2.0, 0.2, 500.0, 5e-11, 5e-13, 150.0, 4, 0.8)
    result = a.lerp(b, 1.0)
    assert result.cosmic_time == pytest.approx(2.0)
    assert result.scale_factor == pytest.approx(0.2)
    assert result.temperature == pytest.approx(500.0)
    assert result.matter_density == pytest.approx(5e-11)
    assert result.radiation_density == pytest.approx(5e-13)
    assert result.hubble_param == pytest.approx(150.0)
    assert result.era_progress == pytest.approx(0.8)


def test_lerp_midpoint():
    """lerp(other, alpha=0.5) returns midpoint for continuous fields."""
    a = PhysicsState(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0)
    b = PhysicsState(10.0, 1.0, 100.0, 50.0, 20.0, 80.0, 5, 1.0)
    result = a.lerp(b, 0.5)
    assert result.cosmic_time == pytest.approx(5.0)
    assert result.scale_factor == pytest.approx(0.5)
    assert result.temperature == pytest.approx(50.0)
    assert result.matter_density == pytest.approx(25.0)
    assert result.radiation_density == pytest.approx(10.0)
    assert result.hubble_param == pytest.approx(40.0)
    assert result.era_progress == pytest.approx(0.5)


def test_lerp_preserves_discrete_era():
    """lerp does NOT interpolate current_era (discrete field)."""
    a = PhysicsState(1.0, 0.1, 1000.0, 1e-10, 1e-12, 200.0, 3, 0.2)
    b = PhysicsState(2.0, 0.2, 500.0, 5e-11, 5e-13, 150.0, 4, 0.8)
    result = a.lerp(b, 0.5)
    assert result.current_era == 3  # Uses self's era, not interpolated


def test_lerp_arbitrary_alpha():
    """lerp works correctly for arbitrary alpha values (0.25, 0.75)."""
    a = PhysicsState(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2, 0.0)
    b = PhysicsState(100.0, 1.0, 1000.0, 4.0, 8.0, 200.0, 7, 1.0)
    result = a.lerp(b, 0.25)
    assert result.cosmic_time == pytest.approx(25.0)
    assert result.scale_factor == pytest.approx(0.25)
    assert result.temperature == pytest.approx(250.0)
    assert result.current_era == 2  # Still self's era


def test_no_rendering_imports():
    """State module has zero imports from rendering layer."""
    import bigbangsim.simulation.state as mod
    source = inspect.getsource(mod)
    assert "import moderngl" not in source
    assert "from bigbangsim.rendering" not in source
