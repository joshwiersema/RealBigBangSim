"""Hydrogen recombination physics via the Saha equation.

Computes the ionization fraction of hydrogen as a function of temperature
during the recombination epoch (z ~ 1100, T ~ 3000 K). Uses the Saha
equation to build a lookup table, then provides fast interpolation.

The Saha equation relates the ionization fraction x = n_e / n_b to
temperature through:

    x^2 / (1 - x) = (1/n_b) * (2 pi m_e k_B T / h^2)^(3/2) * exp(-E_ion / k_B T)

where E_ion = 13.6 eV is the hydrogen ionization energy.

Sources:
  - Saha equation: Weinberg, Cosmology (2008), Section 2.3
  - Recombination: Peebles (1968), ApJ 153:1
  - Constants: CODATA 2018, Planck 2018
"""
import math

import numpy as np

from bigbangsim.simulation.constants import (
    K_B,
    HBAR,
    M_ELECTRON,
    OMEGA_B0,
    T_CMB0,
)
from bigbangsim.simulation.cosmology import RHO_CRIT

# Derived physical constants
_E_ION = 13.6 * 1.602176634e-19          # Hydrogen ionization energy [J]
_H_PLANCK = 2.0 * math.pi * HBAR          # Planck constant h = 2*pi*hbar [J s]
_EV_PER_C2 = 1.602176634e-19 / (2.998e8) ** 2  # 1 eV/c^2 in kg
_M_E_KG = M_ELECTRON * 1e6 * _EV_PER_C2  # Electron mass in kg (from MeV/c^2)
_M_PROTON_KG = 1.67262192e-27             # Proton mass [kg]


def build_ionization_table(n_points: int = 500) -> tuple[np.ndarray, np.ndarray]:
    """Build a lookup table of ionization fraction vs temperature.

    Solves the Saha equation at logarithmically-spaced temperatures from
    1500 K to 10000 K. The returned arrays can be passed to
    get_ionization_fraction() for fast interpolation.

    Args:
        n_points: Number of sample points in the table.

    Returns:
        Tuple of (temperatures, ionization_fractions), both 1D numpy arrays
        of length n_points. Temperatures in Kelvin, fractions in [0, 1].

    Notes:
        The baryon number density n_b is computed from Planck 2018 parameters:
            n_b = OMEGA_B0 * RHO_CRIT * (T / T_CMB0)^3 / M_PROTON_KG

        The quadratic from the Saha equation x^2 + Ax - A = 0 is solved as:
            x = (-A + sqrt(A^2 + 4A)) / 2

    References:
        Weinberg, Cosmology (2008), Section 2.3
        Planck 2018 (arXiv:1807.06209) for OMEGA_B0, T_CMB0
    """
    temps = np.logspace(math.log10(1500.0), math.log10(10000.0), n_points)
    x_values = np.empty(n_points)

    for i, T in enumerate(temps):
        # Baryon number density at this temperature
        # n_b = OMEGA_B0 * rho_crit * (T/T_CMB0)^3 / m_proton
        n_b = OMEGA_B0 * RHO_CRIT * (T / T_CMB0) ** 3 / _M_PROTON_KG

        # Saha equation RHS:
        # A = (1/n_b) * (2 pi m_e k_B T / h^2)^(3/2) * exp(-E_ion / (k_B T))
        thermal_factor = (2.0 * math.pi * _M_E_KG * K_B * T) / (_H_PLANCK ** 2)
        A = (1.0 / n_b) * thermal_factor ** 1.5 * math.exp(-_E_ION / (K_B * T))

        # Solve x^2 + Ax - A = 0 using the quadratic formula
        # For large A (high T), use numerically stable form to avoid
        # catastrophic cancellation in (-A + sqrt(A^2 + 4A)):
        #   x = 2A / (A + sqrt(A^2 + 4A))  [equivalent, stable for large A]
        discriminant = A * A + 4.0 * A
        sqrt_disc = math.sqrt(discriminant)
        if A > 1e6:
            # Numerically stable form for large A
            x = 2.0 * A / (A + sqrt_disc)
        else:
            x = (-A + sqrt_disc) / 2.0

        # Clamp to [0, 1]
        x_values[i] = max(0.0, min(1.0, x))

    # Enforce monotonicity: ionization fraction must not decrease with T.
    # Any tiny non-monotonicity is floating-point noise at the saturated end.
    for i in range(1, n_points):
        if x_values[i] < x_values[i - 1]:
            x_values[i] = x_values[i - 1]

    return (temps, x_values)


def get_ionization_fraction(
    temperature: float,
    table: tuple[np.ndarray, np.ndarray],
) -> float:
    """Interpolate ionization fraction from the precomputed table.

    Args:
        temperature: Temperature in Kelvin.
        table: Tuple of (temperatures, ionization_fractions) from
               build_ionization_table().

    Returns:
        Ionization fraction x in [0, 1].
        Returns 1.0 for T > 10000 K (fully ionized).
        Returns 0.0 for T < 1500 K (fully neutral).

    References:
        Saha equation: Weinberg, Cosmology (2008)
    """
    if temperature > 10000.0:
        return 1.0
    if temperature < 1500.0:
        return 0.0
    return float(np.interp(temperature, table[0], table[1]))
