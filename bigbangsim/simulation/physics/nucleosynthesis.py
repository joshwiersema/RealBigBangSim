"""Big Bang Nucleosynthesis (BBN) yield calculations.

Returns primordial element abundances as a function of temperature,
using PDG 2024 Standard BBN (SBBN) values as the final yields.

The BBN epoch occurs at temperatures between ~1 GK (10^9 K, BBN onset)
and ~0.3 GK (3x10^8 K, BBN freeze-out). At higher temperatures, free
nucleons dominate; at lower temperatures, final yields are frozen in.

For the intermediate temperature range, yields are interpolated linearly
in log10(T) space between the pre-BBN and post-BBN values.

Sources:
  - PDG 2024 SBBN Review: Y_P = 0.2470 +/- 0.0002
  - PDG 2024 SBBN Review: D/H = (2.527 +/- 0.030) x 10^-5
  - PDG 2024 SBBN Review: He-3/H = (1.04 +/- 0.04) x 10^-5
  - PDG 2024 SBBN Review: Li-7/H = 1.6 x 10^-10 (theory; observed ~3x lower)
"""
import math

from bigbangsim.simulation.constants import (
    Y_P,
    DEUTERIUM_H,
    HE3_H,
    LI7_H,
)

# Temperature boundaries for BBN [Kelvin]
_T_BBN_ONSET = 1.0e9    # ~1 GK: BBN begins (proton-neutron freeze-out)
_T_BBN_FREEZE = 3.0e8   # ~0.3 GK: BBN effectively complete

# Pre-computed log10 boundaries for interpolation
_LOG_T_ONSET = math.log10(_T_BBN_ONSET)    # 9.0
_LOG_T_FREEZE = math.log10(_T_BBN_FREEZE)  # ~8.477

# Final PDG yields (post-BBN)
_FINAL_YIELDS = {
    "helium_fraction": Y_P,              # 0.2470
    "deuterium_ratio": DEUTERIUM_H,      # 2.527e-5
    "he3_ratio": HE3_H,                  # 1.04e-5
    "li7_ratio": LI7_H,                  # 1.6e-10
}

# Pre-BBN yields (approximate as final yields for visualization purposes,
# since the simulation shows endpoints rather than intermediate nuclear
# reaction networks)
_INITIAL_YIELDS = {
    "helium_fraction": Y_P,
    "deuterium_ratio": DEUTERIUM_H,
    "he3_ratio": HE3_H,
    "li7_ratio": LI7_H,
}


def get_bbn_fractions(temperature: float) -> dict[str, float]:
    """Return BBN element fractions at the given temperature.

    Args:
        temperature: Temperature in Kelvin.

    Returns:
        Dictionary with keys:
          - hydrogen_fraction: H mass fraction (= 1.0 - helium_fraction)
          - helium_fraction: He-4 mass fraction (Y_P)
          - deuterium_ratio: D/H number ratio
          - he3_ratio: He-3/H number ratio
          - li7_ratio: Li-7/H number ratio

    Notes:
        For T > 1e9 K (pre-BBN): returns initial yields (approximated
        as final yields for visualization).
        For T < 3e8 K (post-BBN): returns final PDG 2024 SBBN values.
        For 3e8 <= T <= 1e9 K: linearly interpolates in log10(T) space.

    References:
        PDG 2024 Standard BBN Review
        Planck 2018 (arXiv:1807.06209)
    """
    if temperature >= _T_BBN_ONSET:
        # Pre-BBN: return initial yields
        yields = dict(_INITIAL_YIELDS)
    elif temperature <= _T_BBN_FREEZE:
        # Post-BBN: return final PDG values
        yields = dict(_FINAL_YIELDS)
    else:
        # Intermediate: interpolate linearly in log10(T) space
        log_t = math.log10(temperature)
        # Fraction from freeze-out (0.0) to onset (1.0)
        frac = (log_t - _LOG_T_FREEZE) / (_LOG_T_ONSET - _LOG_T_FREEZE)
        frac = max(0.0, min(1.0, frac))

        yields = {}
        for key in _FINAL_YIELDS:
            v_final = _FINAL_YIELDS[key]
            v_initial = _INITIAL_YIELDS[key]
            yields[key] = v_final + (v_initial - v_final) * frac

    # Mass conservation: hydrogen_fraction = 1.0 - helium_fraction
    yields["hydrogen_fraction"] = 1.0 - yields["helium_fraction"]
    return yields
