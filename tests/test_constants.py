"""Tests verifying cosmological constants match published values.

Sources:
  - Planck 2018: arXiv:1807.06209, Table 2 (TT,TE,EE+lowE+lensing)
  - PDG 2024: Particle Data Group Review of Particle Physics
  - CODATA 2018: NIST fundamental physical constants
"""
import inspect
import pytest


def test_h0_planck_2018():
    """H0 = 67.66 km/s/Mpc (Planck 2018 Table 2)."""
    from bigbangsim.simulation.constants import H0
    assert H0 == 67.66


def test_omega_m0_planck_2018():
    """Omega_m0 = 0.3111 (Planck 2018 Table 2)."""
    from bigbangsim.simulation.constants import OMEGA_M0
    assert OMEGA_M0 == 0.3111


def test_omega_b0_planck_2018():
    """Omega_b0 = 0.04897 (Planck 2018 Table 2)."""
    from bigbangsim.simulation.constants import OMEGA_B0
    assert OMEGA_B0 == 0.04897


def test_t_cmb0_planck_2018():
    """T_CMB0 = 2.7255 K (Fixsen 2009 / Planck 2018)."""
    from bigbangsim.simulation.constants import T_CMB0
    assert T_CMB0 == 2.7255


def test_n_eff_standard_model():
    """N_eff = 3.046 (Standard Model prediction)."""
    from bigbangsim.simulation.constants import N_EFF
    assert N_EFF == 3.046


def test_y_p_pdg_sbbn():
    """Y_P = 0.2470 (PDG SBBN review, He-4 mass fraction)."""
    from bigbangsim.simulation.constants import Y_P
    assert Y_P == 0.2470


def test_deuterium_h_pdg_sbbn():
    """D/H = 2.527e-5 (PDG SBBN review)."""
    from bigbangsim.simulation.constants import DEUTERIUM_H
    assert DEUTERIUM_H == 2.527e-5


def test_no_rendering_imports():
    """Constants module must have zero imports from rendering layer."""
    import bigbangsim.simulation.constants as mod
    source = inspect.getsource(mod)
    assert "import moderngl" not in source
    assert "from bigbangsim.rendering" not in source


def test_citations_dict_exists():
    """Every key constant must have a citation in the CITATIONS dict."""
    from bigbangsim.simulation.constants import CITATIONS
    required_keys = ["H0", "OMEGA_M0", "OMEGA_B0", "T_CMB0", "Y_P", "DEUTERIUM_H",
                     "N_EFF", "OMEGA_LAMBDA0", "AGE_UNIVERSE"]
    for key in required_keys:
        assert key in CITATIONS, f"Missing citation for {key}"
        assert len(CITATIONS[key]) > 10, f"Citation for {key} is too short"


def test_citations_contain_references():
    """Citations must reference actual papers/sources."""
    from bigbangsim.simulation.constants import CITATIONS
    # At least some citations should reference arXiv or PDG
    arxiv_count = sum(1 for v in CITATIONS.values() if "arXiv" in v or "1807.06209" in v)
    pdg_count = sum(1 for v in CITATIONS.values() if "PDG" in v)
    assert arxiv_count >= 5, f"Expected at least 5 arXiv citations, got {arxiv_count}"
    assert pdg_count >= 2, f"Expected at least 2 PDG citations, got {pdg_count}"


def test_omega_self_consistency():
    """OMEGA_M0 must equal OMEGA_B0 + OMEGA_CDM0."""
    from bigbangsim.simulation.constants import OMEGA_M0, OMEGA_B0, OMEGA_CDM0
    assert OMEGA_M0 == pytest.approx(OMEGA_B0 + OMEGA_CDM0, rel=1e-10)


def test_flat_universe():
    """OMEGA_M0 + OMEGA_LAMBDA0 + OMEGA_R0 ~ 1.0 (flat universe)."""
    from bigbangsim.simulation.constants import OMEGA_M0, OMEGA_LAMBDA0, OMEGA_R0
    total = OMEGA_M0 + OMEGA_LAMBDA0 + OMEGA_R0
    assert total == pytest.approx(1.0, abs=0.001)
