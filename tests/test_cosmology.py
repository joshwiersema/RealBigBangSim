"""Tests for Friedmann equation cosmology solver.

Covers PHYS-06: Friedmann equation integration against known cosmological benchmarks.
"""
import math
import pytest

from bigbangsim.simulation.cosmology import CosmologyModel
from bigbangsim.simulation.constants import T_CMB0, AGE_UNIVERSE, H0


@pytest.fixture(scope="module")
def cosmology():
    """Create a single CosmologyModel instance for all tests (expensive init)."""
    return CosmologyModel()


class TestCosmologyModel:
    """Tests for Friedmann equation integration and parameter lookup."""

    def test_scale_factor_today_approximately_one(self, cosmology):
        """scale_factor at t=today should be approximately 1.0."""
        state = cosmology.get_state_at_cosmic_time(AGE_UNIVERSE)
        assert abs(state["scale_factor"] - 1.0) < 0.05, (
            f"Scale factor today = {state['scale_factor']}, expected ~1.0"
        )

    def test_scale_factor_at_recombination(self, cosmology):
        """scale_factor at recombination (z~1100) should be ~1/1100 = ~9.1e-4."""
        # Recombination at ~380,000 years = ~1.2e13 seconds
        state = cosmology.get_state_at_cosmic_time(1.2e13)
        expected_a = 1.0 / 1100.0  # ~9.1e-4
        # Allow factor of 3 tolerance (cosmic time estimate is approximate)
        ratio = state["scale_factor"] / expected_a
        assert 0.3 < ratio < 3.0, (
            f"Scale factor at recombination = {state['scale_factor']}, "
            f"expected ~{expected_a}"
        )

    def test_temperature_today(self, cosmology):
        """Temperature today should be approximately T_CMB0 = 2.7255 K."""
        state = cosmology.get_state_at_cosmic_time(AGE_UNIVERSE)
        assert abs(state["temperature"] - T_CMB0) / T_CMB0 < 0.05, (
            f"Temperature today = {state['temperature']}, expected ~{T_CMB0}"
        )

    def test_temperature_at_recombination(self, cosmology):
        """Temperature at recombination should be approximately 3000 K."""
        state = cosmology.get_state_at_cosmic_time(1.2e13)
        # Allow factor of 3 tolerance
        assert 1000.0 < state["temperature"] < 10000.0, (
            f"Temperature at recombination = {state['temperature']}, expected ~3000 K"
        )

    def test_temperature_scales_inversely_with_scale_factor(self, cosmology):
        """T = T_CMB0 / a(t) in radiation-dominated era."""
        # Test at an early time in radiation-dominated era
        state = cosmology.get_state_at_cosmic_time(1.0)  # ~1 second
        a = state["scale_factor"]
        t = state["temperature"]
        expected_t = T_CMB0 / a
        rel_err = abs(t - expected_t) / expected_t
        assert rel_err < 0.05, (
            f"T = {t}, expected T_CMB0/a = {expected_t}, rel_err = {rel_err}"
        )

    def test_hubble_parameter_early_much_larger(self, cosmology):
        """Hubble parameter at early times should be much larger than today."""
        state_early = cosmology.get_state_at_cosmic_time(1.0)
        state_today = cosmology.get_state_at_cosmic_time(AGE_UNIVERSE)
        assert state_early["hubble_param"] > state_today["hubble_param"] * 10, (
            f"Early H = {state_early['hubble_param']}, "
            f"today H = {state_today['hubble_param']}"
        )

    def test_matter_density_decreases_with_expansion(self, cosmology):
        """Matter density should decrease as the universe expands."""
        state_early = cosmology.get_state_at_cosmic_time(1.0)
        state_late = cosmology.get_state_at_cosmic_time(1e15)
        assert state_early["matter_density"] > state_late["matter_density"]

    def test_radiation_density_decreases_faster_than_matter(self, cosmology):
        """Radiation density should decrease faster than matter density (rho_r ~ a^-4 vs rho_m ~ a^-3)."""
        state_early = cosmology.get_state_at_cosmic_time(1.0)
        state_late = cosmology.get_state_at_cosmic_time(1e15)
        # rho_r ratio should be larger than rho_m ratio
        rad_ratio = state_early["radiation_density"] / max(state_late["radiation_density"], 1e-100)
        mat_ratio = state_early["matter_density"] / max(state_late["matter_density"], 1e-100)
        assert rad_ratio > mat_ratio, (
            f"Radiation density ratio {rad_ratio} not > matter density ratio {mat_ratio}"
        )

    def test_no_rendering_imports(self):
        """Cosmology module must not import from bigbangsim.rendering."""
        import bigbangsim.simulation.cosmology as mod
        import inspect
        source = inspect.getsource(mod)
        assert "bigbangsim.rendering" not in source
        assert "import moderngl" not in source

    def test_get_state_returns_all_keys(self, cosmology):
        """get_state_at_cosmic_time should return all required keys."""
        state = cosmology.get_state_at_cosmic_time(1e10)
        required_keys = [
            "scale_factor", "temperature", "matter_density",
            "radiation_density", "hubble_param",
        ]
        for key in required_keys:
            assert key in state, f"Missing key: {key}"
            assert isinstance(state[key], float), f"Key {key} is not float"
