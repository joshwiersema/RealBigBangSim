"""Cosmological era definitions with screen time budgets.

Defines the 11 major eras of cosmic history, each with physical time boundaries
and configurable screen time allocations for the cinematic simulation.

The eras span from the Planck epoch (~1e-43 s) to large-scale structure
formation (~4.35e17 s), covering 60+ orders of magnitude in cosmic time.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EraDefinition:
    """A cosmological era with physical boundaries and display parameters.

    Attributes:
        name: Display name of the era.
        index: Sequential index (0-10).
        cosmic_start: Start time in seconds after the Big Bang.
        cosmic_end: End time in seconds after the Big Bang.
        screen_seconds: Wall-clock seconds of display time allocated.
        description: One-line educational summary of the era.
    """
    name: str
    index: int
    cosmic_start: float
    cosmic_end: float
    screen_seconds: float
    description: str


ERAS: list[EraDefinition] = [
    EraDefinition(
        name="Planck Epoch",
        index=0,
        cosmic_start=1e-43,
        cosmic_end=1e-36,
        screen_seconds=12.0,
        description="All four fundamental forces are unified; quantum gravity dominates.",
    ),
    EraDefinition(
        name="Grand Unification",
        index=1,
        cosmic_start=1e-36,
        cosmic_end=1e-12,
        screen_seconds=12.0,
        description="Gravity separates; strong, weak, and electromagnetic forces remain unified.",
    ),
    EraDefinition(
        name="Inflation",
        index=2,
        cosmic_start=1e-36,
        cosmic_end=1e-32,
        screen_seconds=15.0,
        description="Exponential expansion stretches the universe by a factor of ~10^26.",
    ),
    EraDefinition(
        name="Quark-Gluon Plasma",
        index=3,
        cosmic_start=1e-12,
        cosmic_end=1e-6,
        screen_seconds=15.0,
        description="A superhot soup of free quarks and gluons fills the universe.",
    ),
    EraDefinition(
        name="Hadron Epoch",
        index=4,
        cosmic_start=1e-6,
        cosmic_end=1.0,
        screen_seconds=12.0,
        description="Quarks combine into protons and neutrons as the universe cools.",
    ),
    EraDefinition(
        name="Nucleosynthesis",
        index=5,
        cosmic_start=1.0,
        cosmic_end=1200.0,
        screen_seconds=20.0,
        description="Protons and neutrons fuse into light elements: hydrogen, helium, lithium.",
    ),
    EraDefinition(
        name="Recombination/CMB",
        index=6,
        cosmic_start=1.2e3,
        cosmic_end=1.2e13,
        screen_seconds=20.0,
        description="Electrons bind to nuclei; the universe becomes transparent, releasing the CMB.",
    ),
    EraDefinition(
        name="Dark Ages",
        index=7,
        cosmic_start=1.2e13,
        cosmic_end=6.3e15,
        screen_seconds=12.0,
        description="No stars yet; neutral gas fills the expanding cosmos in darkness.",
    ),
    EraDefinition(
        name="First Stars / Reionization",
        index=8,
        cosmic_start=6.3e15,
        cosmic_end=1.3e16,
        screen_seconds=15.0,
        description="The first massive stars ignite, ionizing surrounding hydrogen gas.",
    ),
    EraDefinition(
        name="Galaxy Formation",
        index=9,
        cosmic_start=1.3e16,
        cosmic_end=6.3e16,
        screen_seconds=18.0,
        description="Gravity assembles matter into galaxies, galaxy clusters, and cosmic web.",
    ),
    EraDefinition(
        name="Large-Scale Structure",
        index=10,
        cosmic_start=6.3e16,
        cosmic_end=4.35e17,
        screen_seconds=15.0,
        description="The cosmic web matures into today's observable universe.",
    ),
]


def get_era_by_cosmic_time(cosmic_time: float) -> EraDefinition:
    """Return the era active at the given cosmic time.

    Uses sequential era boundaries (by index) for unambiguous lookup.
    For overlapping physical eras (e.g., Inflation overlaps Grand Unification),
    the sequential index ordering determines which era is returned.

    Args:
        cosmic_time: Time in seconds after the Big Bang.

    Returns:
        The EraDefinition active at the given cosmic time.
    """
    # Walk eras by index; the last era whose cosmic_start <= cosmic_time wins,
    # but we must also check that cosmic_time < cosmic_end for non-final eras.
    # For sequential screen time allocation, we use index order.
    for i in range(len(ERAS) - 1, -1, -1):
        if cosmic_time >= ERAS[i].cosmic_start:
            return ERAS[i]
    # Before Planck time: return Planck Epoch
    return ERAS[0]


def total_screen_time() -> float:
    """Return the total screen time across all eras in seconds."""
    return sum(era.screen_seconds for era in ERAS)


def era_screen_start(era_index: int) -> float:
    """Return the cumulative screen time before the given era starts.

    Args:
        era_index: Index of the era (0-10).

    Returns:
        Screen time offset in seconds where this era begins.
    """
    return sum(ERAS[i].screen_seconds for i in range(era_index))
