"""Tests for Big Bang Nucleosynthesis (BBN) yield calculations.

Verifies that BBN yields match PDG 2024 SBBN values and interpolate
correctly across the nucleosynthesis temperature range.

Sources:
  - PDG 2024 SBBN Review: Y_P = 0.2470, D/H = 2.527e-5
"""
import inspect
import math
import pytest


class TestBBNFractions:
    """Tests for get_bbn_fractions temperature-dependent yield lookup."""

    def test_post_bbn_helium_fraction(self):
        """Post-BBN (T < 3e8 K): helium fraction matches PDG Y_P = 0.2470."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(1e8)
        assert result["helium_fraction"] == pytest.approx(0.2470, rel=1e-3)

    def test_post_bbn_hydrogen_fraction(self):
        """Post-BBN: hydrogen_fraction = 1.0 - helium_fraction (mass conservation)."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(1e8)
        assert result["hydrogen_fraction"] == pytest.approx(
            1.0 - result["helium_fraction"], rel=1e-10
        )

    def test_post_bbn_deuterium_ratio(self):
        """Post-BBN: D/H = 2.527e-5 (PDG 2024)."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(1e8)
        assert result["deuterium_ratio"] == pytest.approx(2.527e-5, rel=1e-3)

    def test_post_bbn_he3_ratio(self):
        """Post-BBN: He-3/H = 1.04e-5 (PDG 2024)."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(1e8)
        assert result["he3_ratio"] == pytest.approx(1.04e-5, rel=1e-3)

    def test_post_bbn_li7_ratio(self):
        """Post-BBN: Li-7/H = 1.6e-10 (PDG 2024)."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(1e8)
        assert result["li7_ratio"] == pytest.approx(1.6e-10, rel=1e-3)

    def test_pre_bbn_helium_fraction(self):
        """Pre-BBN (T > 1e9 K): helium fraction approximately matches final yields."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(2e9)
        assert result["helium_fraction"] == pytest.approx(0.2470, rel=1e-3)

    def test_pre_bbn_hydrogen_fraction(self):
        """Pre-BBN: hydrogen_fraction = 1.0 - helium_fraction."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(2e9)
        assert result["hydrogen_fraction"] == pytest.approx(
            1.0 - result["helium_fraction"], rel=1e-10
        )

    def test_intermediate_temperature_interpolation(self):
        """Intermediate T (3e8 <= T <= 1e9): yields interpolate in log-T."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result_low = get_bbn_fractions(3e8)
        result_high = get_bbn_fractions(1e9)
        # Midpoint in log-T space
        t_mid = 10 ** ((math.log10(3e8) + math.log10(1e9)) / 2)
        result_mid = get_bbn_fractions(t_mid)
        # Helium fraction at midpoint should be between the boundary values
        he_low = result_low["helium_fraction"]
        he_high = result_high["helium_fraction"]
        assert min(he_low, he_high) <= result_mid["helium_fraction"] <= max(he_low, he_high) + 1e-10

    def test_mass_conservation_all_temperatures(self):
        """hydrogen_fraction + helium_fraction = 1.0 at various temperatures."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        for temp in [1e7, 1e8, 5e8, 1e9, 1e10]:
            result = get_bbn_fractions(temp)
            total = result["hydrogen_fraction"] + result["helium_fraction"]
            assert total == pytest.approx(1.0, rel=1e-10), (
                f"Mass conservation violated at T={temp}: H={result['hydrogen_fraction']}, "
                f"He={result['helium_fraction']}"
            )

    def test_returns_all_required_keys(self):
        """Result dict has all required keys."""
        from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
        result = get_bbn_fractions(1e8)
        required = ["hydrogen_fraction", "helium_fraction", "deuterium_ratio",
                     "he3_ratio", "li7_ratio"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_imports_from_constants(self):
        """Nucleosynthesis module imports PDG constants from constants.py."""
        import bigbangsim.simulation.physics.nucleosynthesis as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.simulation.constants import" in source
        assert "Y_P" in source

    def test_no_rendering_imports(self):
        """Nucleosynthesis module has zero rendering imports."""
        import bigbangsim.simulation.physics.nucleosynthesis as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.rendering" not in source
        assert "import moderngl" not in source
