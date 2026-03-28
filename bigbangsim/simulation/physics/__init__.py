"""Physics sub-modules for era-specific cosmological calculations.

Provides data-driven physics models that produce per-era uniforms for
GPU shaders. All modules live in the simulation layer with zero
rendering imports.

Sub-modules:
  nucleosynthesis -- Big Bang Nucleosynthesis (BBN) yield calculations
  recombination   -- Saha equation ionization fraction
  structure       -- Jeans instability and Press-Schechter collapsed fraction
"""

from bigbangsim.simulation.physics.nucleosynthesis import get_bbn_fractions
from bigbangsim.simulation.physics.recombination import (
    build_ionization_table,
    get_ionization_fraction,
)
from bigbangsim.simulation.physics.structure import (
    compute_jeans_mass,
    build_collapsed_fraction_table,
    get_collapsed_fraction,
)

__all__ = [
    "get_bbn_fractions",
    "build_ionization_table",
    "get_ionization_fraction",
    "compute_jeans_mass",
    "build_collapsed_fraction_table",
    "get_collapsed_fraction",
]
