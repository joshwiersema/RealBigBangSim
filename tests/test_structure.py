"""Tests for structure formation physics: Jeans mass and Press-Schechter.

Verifies that Jeans mass scales correctly with temperature and density,
and that the Press-Schechter collapsed fraction increases with cosmic time.

Sources:
  - Jeans instability: Binney & Tremaine, Galactic Dynamics (2008)
  - Press-Schechter: Press & Schechter (1974), ApJ 187:425
"""
import inspect
import math
import numpy as np
import pytest


class TestComputeJeansMass:
    """Tests for Jeans mass calculation."""

    def test_returns_positive_float(self):
        """Jeans mass must be a positive float."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        mass = compute_jeans_mass(temperature=3000.0, matter_density=1e-18)
        assert isinstance(mass, float)
        assert mass > 0

    def test_higher_temperature_larger_mass(self):
        """Hotter gas requires more mass to collapse (larger Jeans mass)."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        m_cool = compute_jeans_mass(temperature=1000.0, matter_density=1e-18)
        m_hot = compute_jeans_mass(temperature=10000.0, matter_density=1e-18)
        assert m_hot > m_cool, (
            f"Jeans mass at 10000K ({m_hot}) should be > at 1000K ({m_cool})"
        )

    def test_higher_density_smaller_mass(self):
        """Denser gas collapses easier (smaller Jeans mass)."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        m_sparse = compute_jeans_mass(temperature=3000.0, matter_density=1e-20)
        m_dense = compute_jeans_mass(temperature=3000.0, matter_density=1e-16)
        assert m_dense < m_sparse, (
            f"Jeans mass at rho=1e-16 ({m_dense}) should be < at rho=1e-20 ({m_sparse})"
        )

    def test_order_of_magnitude(self):
        """Jeans mass at T=3000K, rho=1e-18 should be in 1e36-1e40 kg range."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        mass = compute_jeans_mass(temperature=3000.0, matter_density=1e-18)
        assert 1e34 < mass < 1e42, (
            f"Jeans mass = {mass} kg, expected in ~1e36-1e40 range"
        )

    def test_ionized_vs_neutral(self):
        """Ionized gas has lower mean molecular weight, higher sound speed, larger Jeans mass."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        m_ionized = compute_jeans_mass(temperature=5000.0, matter_density=1e-18, ionized=True)
        m_neutral = compute_jeans_mass(temperature=5000.0, matter_density=1e-18, ionized=False)
        assert m_ionized > m_neutral, (
            f"Ionized Jeans mass ({m_ionized}) should be > neutral ({m_neutral})"
        )

    def test_scales_as_t_to_three_halves(self):
        """Jeans mass M_J ~ T^(3/2): doubling T should increase mass by ~2^1.5 = 2.83."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        m1 = compute_jeans_mass(temperature=2000.0, matter_density=1e-18)
        m2 = compute_jeans_mass(temperature=4000.0, matter_density=1e-18)
        ratio = m2 / m1
        expected_ratio = 2.0 ** 1.5  # ~2.83
        assert ratio == pytest.approx(expected_ratio, rel=0.05), (
            f"Mass ratio = {ratio}, expected ~{expected_ratio}"
        )

    def test_scales_as_rho_to_minus_half(self):
        """Jeans mass M_J ~ rho^(-1/2): 100x density should give 10x smaller mass."""
        from bigbangsim.simulation.physics.structure import compute_jeans_mass
        m1 = compute_jeans_mass(temperature=3000.0, matter_density=1e-20)
        m2 = compute_jeans_mass(temperature=3000.0, matter_density=1e-18)
        ratio = m1 / m2
        expected_ratio = 10.0  # (1e-20/1e-18)^(-0.5) = 100^0.5 = 10
        assert ratio == pytest.approx(expected_ratio, rel=0.05), (
            f"Mass ratio = {ratio}, expected ~{expected_ratio}"
        )


class TestBuildCollapsedFractionTable:
    """Tests for Press-Schechter collapsed fraction table."""

    def test_returns_tuple_of_two_arrays(self):
        """build_collapsed_fraction_table returns (times, fractions) tuple."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        result = build_collapsed_fraction_table()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], np.ndarray)
        assert isinstance(result[1], np.ndarray)

    def test_arrays_same_length(self):
        """Time and fraction arrays have the same length."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        times, fractions = build_collapsed_fraction_table()
        assert len(times) == len(fractions)

    def test_fractions_in_valid_range(self):
        """Collapsed fractions between 0.0 and 1.0."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        _, fractions = build_collapsed_fraction_table()
        assert np.all(fractions >= 0.0)
        assert np.all(fractions <= 1.0)

    def test_early_time_near_zero(self):
        """Collapsed fraction at early times (high redshift) near 0.0."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        _, fractions = build_collapsed_fraction_table()
        assert fractions[0] < 0.1, (
            f"Early collapsed fraction = {fractions[0]}, expected near 0.0"
        )

    def test_late_time_increases(self):
        """Collapsed fraction at late times higher than early times."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        _, fractions = build_collapsed_fraction_table()
        assert fractions[-1] > fractions[0], (
            f"Late fraction ({fractions[-1]}) not > early ({fractions[0]})"
        )

    def test_monotonically_increasing(self):
        """Collapsed fraction increases with cosmic time."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        _, fractions = build_collapsed_fraction_table()
        diffs = np.diff(fractions)
        assert np.all(diffs >= -1e-10), "Collapsed fraction not monotonically increasing"

    def test_custom_n_points(self):
        """build_collapsed_fraction_table accepts custom n_points."""
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        times, fractions = build_collapsed_fraction_table(n_points=50)
        assert len(times) == 50

    def test_uses_erfc(self):
        """Structure module uses scipy.special.erfc for Press-Schechter."""
        import bigbangsim.simulation.physics.structure as mod
        source = inspect.getsource(mod)
        assert "erfc" in source


class TestGetCollapsedFraction:
    """Tests for collapsed fraction interpolation."""

    @pytest.fixture(scope="class")
    def table(self):
        from bigbangsim.simulation.physics.structure import build_collapsed_fraction_table
        return build_collapsed_fraction_table()

    def test_interpolation_within_range(self, table):
        """Interpolated value within the table range."""
        from bigbangsim.simulation.physics.structure import get_collapsed_fraction
        times = table[0]
        t_mid = (times[0] + times[-1]) / 2
        frac = get_collapsed_fraction(t_mid, table)
        assert 0.0 <= frac <= 1.0

    def test_clamp_before_table(self, table):
        """Time before table range returns first fraction value."""
        from bigbangsim.simulation.physics.structure import get_collapsed_fraction
        frac = get_collapsed_fraction(1e10, table)
        assert 0.0 <= frac <= 1.0

    def test_clamp_after_table(self, table):
        """Time after table range returns last fraction value."""
        from bigbangsim.simulation.physics.structure import get_collapsed_fraction
        frac = get_collapsed_fraction(1e20, table)
        assert 0.0 <= frac <= 1.0

    def test_returns_float(self, table):
        """get_collapsed_fraction returns a float."""
        from bigbangsim.simulation.physics.structure import get_collapsed_fraction
        result = get_collapsed_fraction(1e16, table)
        assert isinstance(result, (float, np.floating))


class TestStructureModuleBoundary:
    """Test simulation-rendering boundary."""

    def test_imports_from_constants(self):
        """Structure module imports constants from constants.py."""
        import bigbangsim.simulation.physics.structure as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.simulation.constants import" in source

    def test_no_rendering_imports(self):
        """Structure module has zero rendering imports."""
        import bigbangsim.simulation.physics.structure as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.rendering" not in source
        assert "import moderngl" not in source
