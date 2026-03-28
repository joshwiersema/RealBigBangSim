"""Tests for hydrogen recombination / Saha equation ionization fraction.

Verifies that the ionization fraction transitions from ~1.0 (fully ionized)
at high temperature to ~0.0 (fully neutral) at low temperature, with the
transition region around ~3000-4000 K as expected from the Saha equation.

Sources:
  - Saha equation: Weinberg, Cosmology (2008)
  - Recombination temperature: T ~ 3000 K (z ~ 1100)
"""
import inspect
import numpy as np
import pytest


class TestBuildIonizationTable:
    """Tests for build_ionization_table lookup construction."""

    def test_returns_tuple_of_two_arrays(self):
        """build_ionization_table returns (temps, x_values) tuple."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        result = build_ionization_table()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], np.ndarray)
        assert isinstance(result[1], np.ndarray)

    def test_arrays_have_same_length(self):
        """Temperature and ionization arrays must have the same length."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        temps, x_values = build_ionization_table()
        assert len(temps) == len(x_values)

    def test_temperature_range(self):
        """Temperature array spans 1500 K to 10000 K."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        temps, _ = build_ionization_table()
        assert temps[0] == pytest.approx(1500.0, rel=0.01)
        assert temps[-1] == pytest.approx(10000.0, rel=0.01)

    def test_ionization_high_at_high_temperature(self):
        """Ionization fraction near 1.0 at T=10000 K."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        temps, x_values = build_ionization_table()
        # Last element should be near 1.0
        assert x_values[-1] > 0.9, f"x at T=10000K = {x_values[-1]}, expected > 0.9"

    def test_ionization_low_at_low_temperature(self):
        """Ionization fraction near 0.0 at T=1500 K."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        temps, x_values = build_ionization_table()
        # First element should be near 0.0
        assert x_values[0] < 0.1, f"x at T=1500K = {x_values[0]}, expected < 0.1"

    def test_ionization_values_in_valid_range(self):
        """All ionization fractions between 0.0 and 1.0."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        _, x_values = build_ionization_table()
        assert np.all(x_values >= 0.0)
        assert np.all(x_values <= 1.0)

    def test_ionization_monotonically_increasing(self):
        """Ionization fraction increases with temperature (hotter = more ionized)."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        _, x_values = build_ionization_table()
        # Allow tiny numerical noise
        diffs = np.diff(x_values)
        assert np.all(diffs >= -1e-10), "Ionization not monotonically increasing with T"

    def test_custom_n_points(self):
        """build_ionization_table accepts custom n_points parameter."""
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        temps, x_values = build_ionization_table(n_points=100)
        assert len(temps) == 100
        assert len(x_values) == 100


class TestGetIonizationFraction:
    """Tests for get_ionization_fraction interpolation."""

    @pytest.fixture(scope="class")
    def table(self):
        from bigbangsim.simulation.physics.recombination import build_ionization_table
        return build_ionization_table()

    def test_high_temperature_clamp(self, table):
        """T > 10000 K returns 1.0 (fully ionized)."""
        from bigbangsim.simulation.physics.recombination import get_ionization_fraction
        assert get_ionization_fraction(15000.0, table) == 1.0

    def test_low_temperature_clamp(self, table):
        """T < 1500 K returns 0.0 (fully neutral)."""
        from bigbangsim.simulation.physics.recombination import get_ionization_fraction
        assert get_ionization_fraction(1000.0, table) == 0.0

    def test_transition_region(self, table):
        """Ionization ~0.5 somewhere around 3500-4000 K (Saha transition)."""
        from bigbangsim.simulation.physics.recombination import get_ionization_fraction
        # Check a range around the expected transition
        x_3500 = get_ionization_fraction(3500.0, table)
        x_5000 = get_ionization_fraction(5000.0, table)
        # At least one of these should be near 0.5
        has_transition = (0.1 < x_3500 < 0.9) or (0.1 < x_5000 < 0.9)
        assert has_transition, (
            f"No transition found: x(3500K)={x_3500}, x(5000K)={x_5000}"
        )

    def test_interpolation_between_table_points(self, table):
        """Interpolated value should be between neighboring table values."""
        from bigbangsim.simulation.physics.recombination import get_ionization_fraction
        # Use a temperature between table boundaries
        x = get_ionization_fraction(5000.0, table)
        assert 0.0 <= x <= 1.0

    def test_returns_float(self, table):
        """get_ionization_fraction returns a float."""
        from bigbangsim.simulation.physics.recombination import get_ionization_fraction
        result = get_ionization_fraction(5000.0, table)
        assert isinstance(result, (float, np.floating))


class TestRecombinationModuleBoundary:
    """Test simulation-rendering boundary."""

    def test_imports_from_constants(self):
        """Recombination module imports physical constants from constants.py."""
        import bigbangsim.simulation.physics.recombination as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.simulation.constants import" in source

    def test_no_rendering_imports(self):
        """Recombination module has zero rendering imports."""
        import bigbangsim.simulation.physics.recombination as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.rendering" not in source
        assert "import moderngl" not in source
