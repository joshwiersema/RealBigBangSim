"""Friedmann equation integration and cosmological parameter computation.

Pre-computes a dense lookup table of cosmological parameters (scale factor,
temperature, densities, Hubble parameter) by integrating the Friedmann equation
from a very early scale factor to a=1.0 (today).

Uses scipy.integrate.solve_ivp with Radau method for the stiff ODE at the
radiation-matter transition. All parameters come from Planck 2018 results.

Sources:
  - Planck 2018: arXiv:1807.06209
  - Friedmann equations: Weinberg, Cosmology (2008)
"""
import math
import numpy as np
from scipy.integrate import solve_ivp

from bigbangsim.simulation.constants import (
    H0,
    H0_SI,
    OMEGA_M0,
    OMEGA_R0,
    OMEGA_LAMBDA0,
    T_CMB0,
    G,
    AGE_UNIVERSE,
)


# Critical density today: rho_crit = 3 H0^2 / (8 pi G)
RHO_CRIT = 3.0 * H0_SI**2 / (8.0 * math.pi * G)


class CosmologyModel:
    """Pre-computed cosmological parameter lookup table.

    At construction, integrates the Friedmann equation dt/da from a_start
    to a=1.0 to build dense arrays of cosmological parameters as a function
    of cosmic time. Provides O(1) interpolation lookups at any cosmic time.
    """

    def __init__(self, n_points: int = 10000) -> None:
        """Initialize by integrating the Friedmann equation.

        Args:
            n_points: Number of sample points in the lookup table.
        """
        self._n_points = n_points

        # Integration bounds
        self._a_start = 1e-12  # Very early scale factor
        self._a_end = 1.0      # Today

        # Integrate dt/da from a_start to a_end
        self._integrate_friedmann()

        # Compute derived quantities at each sample point
        self._compute_derived_quantities()

    def _hubble_at_a(self, a: float) -> float:
        """Compute Hubble parameter H(a) from Friedmann equation.

        H(a) = H0 * sqrt(Omega_r0/a^4 + Omega_m0/a^3 + Omega_Lambda0)

        Args:
            a: Scale factor.

        Returns:
            Hubble parameter in s^-1.
        """
        return H0_SI * math.sqrt(
            OMEGA_R0 / a**4 + OMEGA_M0 / a**3 + OMEGA_LAMBDA0
        )

    def _integrate_friedmann(self) -> None:
        """Integrate dt/da to get cosmic time as a function of scale factor."""

        def dtda(a, t):
            """ODE: dt/da = 1 / (a * H(a))

            Returns array-shaped output for solver compatibility.
            """
            H = H0_SI * np.sqrt(
                OMEGA_R0 / a**4 + OMEGA_M0 / a**3 + OMEGA_LAMBDA0
            )
            return np.atleast_1d(1.0 / (a * H))

        def jac(a, t):
            """Jacobian d(dtda)/dt = 0 (dtda does not depend on t)."""
            return np.array([[0.0]])

        # Initial time estimate at a_start using radiation-dominated approximation:
        # t ~ 1 / (2 * H0 * sqrt(Omega_r0)) * a^2
        t_start = self._a_start**2 / (2.0 * H0_SI * math.sqrt(OMEGA_R0))

        # Create evaluation points in log-space for better coverage of early universe
        a_eval = np.logspace(
            math.log10(self._a_start),
            math.log10(self._a_end),
            self._n_points,
        )

        # Integrate with Radau (implicit) solver -- good for stiff equations
        # at the radiation-matter transition. Analytical Jacobian provided
        # since dtda doesn't depend on t.
        sol = solve_ivp(
            dtda,
            [self._a_start, self._a_end],
            [t_start],
            method="Radau",
            jac=jac,
            dense_output=True,
            rtol=1e-10,
            atol=1e-20,
        )

        if not sol.success:
            raise RuntimeError(f"Friedmann integration failed: {sol.message}")

        # Evaluate dense output at our sample points
        self._scale_factors = a_eval
        self._cosmic_times = sol.sol(a_eval)[0]

        # Normalize so that t(a=1) = AGE_UNIVERSE
        # The integration gives t relative to t_start; adjust to match known age
        t_at_today = self._cosmic_times[-1]
        self._time_normalization = AGE_UNIVERSE / t_at_today
        self._cosmic_times = self._cosmic_times * self._time_normalization

    def _compute_derived_quantities(self) -> None:
        """Compute temperature, densities, and Hubble parameter at each sample point."""
        a = self._scale_factors

        # Temperature: T(a) = T_CMB0 / a
        self._temperatures = T_CMB0 / a

        # Matter density: rho_m(a) = rho_crit * Omega_m0 / a^3
        self._matter_densities = RHO_CRIT * OMEGA_M0 / a**3

        # Radiation density: rho_r(a) = rho_crit * Omega_r0 / a^4
        self._radiation_densities = RHO_CRIT * OMEGA_R0 / a**4

        # Hubble parameter: H(a) in km/s/Mpc
        # H(a) = H0 * sqrt(Omega_r0/a^4 + Omega_m0/a^3 + Omega_Lambda0)
        self._hubble_params = H0 * np.sqrt(
            OMEGA_R0 / a**4 + OMEGA_M0 / a**3 + OMEGA_LAMBDA0
        )

    def get_state_at_cosmic_time(self, cosmic_time: float) -> dict:
        """Interpolate the lookup table at the given cosmic time.

        For very early times (before a_start), extrapolates using
        the radiation-dominated approximation.

        Args:
            cosmic_time: Time in seconds after the Big Bang.

        Returns:
            Dictionary with keys: scale_factor, temperature, matter_density,
            radiation_density, hubble_param.
        """
        cosmic_time = max(cosmic_time, 1e-45)  # Clamp to positive

        # For times before our integration range, use radiation-dominated extrapolation
        t_min = self._cosmic_times[0]
        if cosmic_time < t_min:
            return self._extrapolate_early(cosmic_time)

        # For times after our integration range, use the last computed values
        t_max = self._cosmic_times[-1]
        if cosmic_time > t_max:
            cosmic_time = t_max

        # Interpolate each quantity
        scale_factor = float(np.interp(cosmic_time, self._cosmic_times, self._scale_factors))
        temperature = float(np.interp(cosmic_time, self._cosmic_times, self._temperatures))
        matter_density = float(np.interp(cosmic_time, self._cosmic_times, self._matter_densities))
        radiation_density = float(np.interp(cosmic_time, self._cosmic_times, self._radiation_densities))
        hubble_param = float(np.interp(cosmic_time, self._cosmic_times, self._hubble_params))

        return {
            "scale_factor": scale_factor,
            "temperature": temperature,
            "matter_density": matter_density,
            "radiation_density": radiation_density,
            "hubble_param": hubble_param,
        }

    def get_state_at_scale_factor(self, a: float) -> dict:
        """Interpolate the lookup table at the given scale factor.

        Args:
            a: Scale factor (dimensionless, 1.0 = today).

        Returns:
            Dictionary with the same keys as get_state_at_cosmic_time.
        """
        a = max(a, 1e-15)  # Clamp to positive
        a = min(a, self._a_end)

        # Find cosmic time for this scale factor
        cosmic_time = float(np.interp(a, self._scale_factors, self._cosmic_times))
        return self.get_state_at_cosmic_time(cosmic_time)

    def _extrapolate_early(self, cosmic_time: float) -> dict:
        """Extrapolate for very early times using radiation-dominated approximation.

        In the radiation-dominated era:
            a(t) ~ sqrt(2 * H0_SI * sqrt(Omega_r0) * t)
            T = T_CMB0 / a(t)
            rho_m = rho_crit * Omega_m0 / a^3
            rho_r = rho_crit * Omega_r0 / a^4

        Args:
            cosmic_time: Time in seconds (before the integration start time).

        Returns:
            Dictionary with cosmological parameters.
        """
        # Apply time normalization to be consistent with integrated range
        # In radiation-dominated: a ~ sqrt(2 H0 sqrt(Omega_r) t)
        # But we need to match our normalized time scale
        a = math.sqrt(2.0 * H0_SI * math.sqrt(OMEGA_R0) * cosmic_time / self._time_normalization)
        a = max(a, 1e-30)

        temperature = T_CMB0 / a
        matter_density = RHO_CRIT * OMEGA_M0 / a**3
        radiation_density = RHO_CRIT * OMEGA_R0 / a**4
        hubble_param = H0 * math.sqrt(
            OMEGA_R0 / a**4 + OMEGA_M0 / a**3 + OMEGA_LAMBDA0
        )

        return {
            "scale_factor": float(a),
            "temperature": float(temperature),
            "matter_density": float(matter_density),
            "radiation_density": float(radiation_density),
            "hubble_param": float(hubble_param),
        }
