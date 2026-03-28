"""Cosmological constants from Planck 2018 and PDG.

Sources:
  - Planck 2018: arXiv:1807.06209, Table 2 (TT,TE,EE+lowE+lensing)
  - PDG: Particle Data Group, 2024 Review of Particle Physics
  - CODATA 2018: NIST fundamental physical constants
  - Fixsen 2009: ApJ 707:916 (CMB temperature)
"""

# --- Fundamental Physical Constants (CODATA 2018) ---
C = 2.99792458e8          # Speed of light [m/s] (exact)
G = 6.67430e-11           # Gravitational constant [m^3 kg^-1 s^-2]
HBAR = 1.054571817e-34    # Reduced Planck constant [J s]
K_B = 1.380649e-23        # Boltzmann constant [J/K] (exact)
SIGMA_SB = 5.670374419e-8  # Stefan-Boltzmann constant [W m^-2 K^-4]

# --- Planck 2018 Cosmological Parameters (arXiv:1807.06209, Table 2) ---
H0 = 67.66               # Hubble constant [km/s/Mpc]
H0_SI = H0 * 1e3 / 3.0857e22  # H0 in [s^-1]
OMEGA_M0 = 0.3111        # Total matter density parameter
OMEGA_B0 = 0.04897       # Baryon density parameter
OMEGA_CDM0 = OMEGA_M0 - OMEGA_B0  # Cold dark matter density parameter
OMEGA_R0 = 9.182e-5      # Radiation density parameter (derived from T_CMB0)
OMEGA_LAMBDA0 = 0.6889   # Dark energy density parameter
T_CMB0 = 2.7255          # CMB temperature today [K] (Fixsen 2009)
N_EFF = 3.046            # Effective number of neutrino species
SIGMA_8 = 0.8102         # RMS matter fluctuations at 8 Mpc/h
N_S = 0.9665             # Scalar spectral index
AGE_UNIVERSE = 13.787e9 * 365.25 * 24 * 3600  # Age of universe [seconds]

# --- Planck Units (derived) ---
T_PLANCK = 1.416784e32   # Planck temperature [K]
L_PLANCK = 1.616255e-35  # Planck length [m]
T_PLANCK_TIME = 5.391247e-44  # Planck time [s]
M_PLANCK = 2.176434e-8   # Planck mass [kg]

# --- BBN Yields (PDG 2024 SBBN Review) ---
Y_P = 0.2470             # Primordial He-4 mass fraction
DEUTERIUM_H = 2.527e-5   # Primordial D/H ratio
HE3_H = 1.04e-5          # Primordial He-3/H ratio
LI7_H = 1.6e-10          # Primordial Li-7/H (theory; observed ~3x lower - "cosmological lithium problem")

# --- Particle Masses (PDG 2024) [MeV/c^2] ---
M_PROTON = 938.272        # Proton mass [MeV/c^2]
M_NEUTRON = 939.565       # Neutron mass [MeV/c^2]
M_ELECTRON = 0.51100      # Electron mass [MeV/c^2]

# --- Key Cosmic Temperatures [K] ---
T_ELECTROWEAK = 1e15      # Electroweak symmetry breaking
T_QCD = 1.5e12            # QCD phase transition (quark-hadron)
T_NUCLEOSYNTHESIS = 1e9   # BBN onset (~1 MeV)
T_RECOMBINATION = 3000.0  # Hydrogen recombination
T_REIONIZATION = 50.0     # Approximate reionization temperature

# --- Citations Registry ---
CITATIONS = {
    "H0": "Planck 2018 (arXiv:1807.06209) Table 2, TT,TE,EE+lowE+lensing: 67.66 +/- 0.42 km/s/Mpc",
    "OMEGA_M0": "Planck 2018 (arXiv:1807.06209) Table 2: 0.3111 +/- 0.0056",
    "OMEGA_B0": "Planck 2018 (arXiv:1807.06209) Table 2: 0.04897 +/- 0.00031 (Omega_b h^2 = 0.02242)",
    "OMEGA_LAMBDA0": "Planck 2018 (arXiv:1807.06209) Table 2: 0.6889 +/- 0.0056",
    "T_CMB0": "Fixsen 2009, ApJ 707:916: 2.7255 +/- 0.0006 K",
    "N_EFF": "Standard Model prediction: 3.046 (Mangano et al. 2005, arXiv:hep-ph/0506164)",
    "Y_P": "PDG 2024 SBBN Review: 0.2470 +/- 0.0002",
    "DEUTERIUM_H": "PDG 2024 SBBN Review: (2.527 +/- 0.030) x 10^-5",
    "AGE_UNIVERSE": "Planck 2018 (arXiv:1807.06209) Table 2: 13.787 +/- 0.020 Gyr",
    "SIGMA_8": "Planck 2018 (arXiv:1807.06209) Table 2: 0.8102 +/- 0.0060",
    "N_S": "Planck 2018 (arXiv:1807.06209) Table 2: 0.9665 +/- 0.0038",
    "OMEGA_R0": "Derived from T_CMB0 and Planck 2018 (arXiv:1807.06209) parameters",
}
