"""Structure formation physics: Jeans instability and Press-Schechter formalism.

Provides two key models for the late-universe era content:

1. Jeans mass: The minimum mass for gravitational collapse of a gas cloud.
   M_J = (pi/6) * c_s^3 / (G^1.5 * rho^0.5)
   where c_s = sqrt(gamma * k_B * T / (mu * m_p)) is the sound speed.

2. Press-Schechter collapsed fraction: The fraction of matter in collapsed
   halos as a function of cosmic time, using the complementary error function.
   F(>M) = erfc(delta_c / (sqrt(2) * sigma(M, z)))

Sources:
  - Jeans instability: Binney & Tremaine, Galactic Dynamics (2008), Ch. 5
  - Press-Schechter: Press & Schechter (1974), ApJ 187:425
  - delta_c = 1.686: Spherical collapse threshold
  - Planck 2018 (arXiv:1807.06209): sigma_8 = 0.8102, n_s = 0.9665
"""
import math

import numpy as np
from scipy.special import erfc

from bigbangsim.simulation.constants import (
    G,
    K_B,
    SIGMA_8,
    N_S,
    AGE_UNIVERSE,
    T_CMB0,
    OMEGA_M0,
)
from bigbangsim.simulation.cosmology import RHO_CRIT

# Proton mass [kg]
_M_PROTON_KG = 1.67262192e-27

# Spherical collapse threshold (linear theory)
_DELTA_C = 1.686


def compute_jeans_mass(
    temperature: float,
    matter_density: float,
    ionized: bool = True,
) -> float:
    """Compute the Jeans mass for gravitational collapse.

    The Jeans mass is the minimum mass for a gas cloud to collapse under
    its own gravity against thermal pressure:

        M_J = (pi/6) * c_s^3 / (G^1.5 * rho^0.5)

    where the sound speed c_s = sqrt(gamma * k_B * T / (mu * m_p)).

    Args:
        temperature: Gas temperature in Kelvin.
        matter_density: Matter density in kg/m^3.
        ionized: If True, use mean molecular weight mu=0.6 (ionized primordial gas).
                 If False, use mu=1.22 (neutral primordial gas).

    Returns:
        Jeans mass in kg.

    Notes:
        - gamma = 5/3 (monatomic ideal gas)
        - mu = 0.6 for ionized primordial gas (H + He with free electrons)
        - mu = 1.22 for neutral primordial gas

    References:
        Binney & Tremaine, Galactic Dynamics (2008), Section 5.2
        Jeans (1902), Phil. Trans. R. Soc. London A, 199:1
    """
    gamma = 5.0 / 3.0
    mu = 0.6 if ionized else 1.22

    # Sound speed [m/s]
    c_s = math.sqrt(gamma * K_B * temperature / (mu * _M_PROTON_KG))

    # Jeans mass [kg]
    m_j = (math.pi / 6.0) * c_s ** 3 / (G ** 1.5 * matter_density ** 0.5)

    return m_j


def build_collapsed_fraction_table(
    n_points: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a lookup table of Press-Schechter collapsed fraction vs cosmic time.

    Uses a simplified Press-Schechter formalism at the sigma_8 mass scale:

        F_collapsed = erfc(delta_c / (sqrt(2) * sigma_M(z)))

    where sigma_M(z) = sigma_8 * D(z) and D(z) ~ 1/(1+z) in the
    matter-dominated era.

    The cosmic time range covers from First Stars (~6.3e15 s) to
    Large-Scale Structure (~4.35e17 s).

    Args:
        n_points: Number of sample points in the table.

    Returns:
        Tuple of (cosmic_times, collapsed_fractions), both 1D numpy arrays.
        Times in seconds, fractions in [0, 1].

    References:
        Press & Schechter (1974), ApJ 187:425
        Planck 2018 (arXiv:1807.06209): sigma_8 = 0.8102
    """
    # Time range: First Stars to LSS
    cosmic_times = np.logspace(
        math.log10(6.3e15), math.log10(4.35e17), n_points
    )

    fractions = np.empty(n_points)

    for i, t in enumerate(cosmic_times):
        # Scale factor from matter-dominated approximation: a = (t/t_0)^(2/3)
        a = (t / AGE_UNIVERSE) ** (2.0 / 3.0)

        # Redshift
        z = 1.0 / a - 1.0

        # Growth factor D(z) ~ a = 1/(1+z) in matter-dominated era
        d_z = 1.0 / (1.0 + z)

        # RMS fluctuation at sigma_8 scale
        sigma_m = SIGMA_8 * d_z

        # Press-Schechter collapsed fraction
        fractions[i] = erfc(_DELTA_C / (math.sqrt(2.0) * sigma_m))

    return (cosmic_times, fractions)


def get_collapsed_fraction(
    cosmic_time: float,
    table: tuple[np.ndarray, np.ndarray],
) -> float:
    """Interpolate collapsed fraction from the precomputed table.

    Values outside the table range are clamped to the nearest boundary.

    Args:
        cosmic_time: Cosmic time in seconds after the Big Bang.
        table: Tuple of (cosmic_times, collapsed_fractions) from
               build_collapsed_fraction_table().

    Returns:
        Collapsed fraction in [0, 1].

    References:
        Press & Schechter (1974), ApJ 187:425
    """
    return float(np.interp(cosmic_time, table[0], table[1]))
