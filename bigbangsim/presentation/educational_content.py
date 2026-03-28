"""Educational content data for BigBangSim presentation layer.

Contains scientifically sourced milestone events (~20 cosmic timestamps with
educational descriptions) and rich era descriptions for all 11 cosmological eras.

Sources:
  - Planck 2018: arXiv:1807.06209
  - PDG 2024: Review of Particle Physics
  - CODATA 2018: Fundamental physical constants
  - Chronology of the Universe (standard cosmology references)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Milestone:
    """A significant cosmic event with trigger and display data.

    Attributes:
        cosmic_time: Seconds after Big Bang (trigger threshold).
        era_index: Which era this belongs to (0-10).
        name: Short event name for notification display.
        description: Educational explanation (2-3 sentences, accessible to non-physicists).
        temperature: Temperature at this event in Kelvin, if applicable.
    """
    cosmic_time: float
    era_index: int
    name: str
    description: str
    temperature: float | None


MILESTONES: list[Milestone] = [
    # Era 0: Planck Epoch
    Milestone(
        cosmic_time=1e-43,
        era_index=0,
        name="Planck Time",
        description=(
            "The universe is one Planck time old -- the smallest meaningful unit of time "
            "in physics. Quantum gravity effects dominate and all four fundamental forces "
            "are believed to be unified into a single superforce."
        ),
        temperature=1.4e32,
    ),

    # Era 1: Grand Unification
    Milestone(
        cosmic_time=1e-36,
        era_index=1,
        name="Gravity Separates",
        description=(
            "Gravity becomes a distinct force as the universe cools below the grand "
            "unification energy scale (~10^16 GeV). The strong, weak, and electromagnetic "
            "forces remain unified as a single grand unified force."
        ),
        temperature=1e28,
    ),

    # Era 2: Inflation
    Milestone(
        cosmic_time=1e-36,
        era_index=2,
        name="Inflation Begins",
        description=(
            "A phase transition triggers exponential expansion of space itself. In a "
            "tiny fraction of a second, the universe will expand by a factor of roughly "
            "10^26, smoothing out any initial irregularities."
        ),
        temperature=1e28,
    ),
    Milestone(
        cosmic_time=1e-32,
        era_index=2,
        name="Inflation Ends / Reheating",
        description=(
            "Inflation ends after roughly 60 e-folds of expansion. The inflaton field's "
            "energy converts into a flood of hot particles, reheating the universe to "
            "extreme temperatures and seeding the matter we see today."
        ),
        temperature=1e27,
    ),

    # Era 3: Quark-Gluon Plasma
    Milestone(
        cosmic_time=2e-11,
        era_index=3,
        name="Electroweak Symmetry Breaking",
        description=(
            "The Higgs field acquires its vacuum expectation value, breaking the "
            "electroweak symmetry. The W and Z bosons gain mass, splitting the "
            "electromagnetic and weak forces into separate interactions."
        ),
        temperature=1e15,
    ),
    Milestone(
        cosmic_time=2e-5,
        era_index=3,
        name="QCD Phase Transition",
        description=(
            "The quark-gluon plasma cools enough for quarks to become confined inside "
            "hadrons. Free quarks and gluons can no longer roam the universe -- they are "
            "permanently locked into protons, neutrons, and other composite particles."
        ),
        temperature=1.5e12,
    ),

    # Era 4: Hadron Epoch
    Milestone(
        cosmic_time=1e-4,
        era_index=4,
        name="First Protons and Neutrons",
        description=(
            "Stable protons and neutrons emerge as the dominant baryonic matter. "
            "Heavier hadrons decay away, leaving behind the building blocks that will "
            "eventually form atomic nuclei, stars, and planets."
        ),
        temperature=1e12,
    ),
    Milestone(
        cosmic_time=1.0,
        era_index=4,
        name="Neutrino Decoupling",
        description=(
            "Neutrinos stop interacting with other particles and stream freely through "
            "the universe. This cosmic neutrino background still fills space today at "
            "a temperature of about 1.95 Kelvin, though it has never been directly detected."
        ),
        temperature=1e10,
    ),
    Milestone(
        cosmic_time=6.0,
        era_index=4,
        name="Electron-Positron Annihilation",
        description=(
            "As the universe cools below the electron rest mass energy, electrons and "
            "positrons annihilate each other in pairs. A tiny excess of electrons survives "
            "due to matter-antimatter asymmetry, providing the electrons in atoms today."
        ),
        temperature=5e9,
    ),

    # Era 5: Nucleosynthesis
    Milestone(
        cosmic_time=10.0,
        era_index=5,
        name="Nucleosynthesis Begins",
        description=(
            "The universe has cooled enough for protons and neutrons to start fusing into "
            "light atomic nuclei. Over the next few minutes, roughly 25% of all baryonic "
            "matter will be converted into helium-4."
        ),
        temperature=1e9,
    ),
    Milestone(
        cosmic_time=180.0,
        era_index=5,
        name="Deuterium Bottleneck Breaks",
        description=(
            "Temperatures drop below the deuterium photo-dissociation threshold. "
            "Deuterium nuclei can finally survive long enough to fuse into heavier "
            "elements, unleashing a rapid chain of nuclear reactions."
        ),
        temperature=8e8,
    ),
    Milestone(
        cosmic_time=1200.0,
        era_index=5,
        name="Nucleosynthesis Ends",
        description=(
            "The universe has expanded and cooled too much for further nuclear fusion. "
            "The final tally: about 75% hydrogen, 25% helium-4, and trace amounts of "
            "deuterium, helium-3, and lithium-7. All heavier elements must wait for stars."
        ),
        temperature=3e7,
    ),

    # Era 6: Recombination / CMB
    Milestone(
        cosmic_time=1.5e12,
        era_index=6,
        name="Matter-Radiation Equality",
        description=(
            "The energy density of matter overtakes that of radiation for the first time. "
            "This shift allows gravity to begin pulling matter into the first large-scale "
            "structures -- the seeds of galaxies and galaxy clusters."
        ),
        temperature=9000.0,
    ),
    Milestone(
        cosmic_time=1.2e13,
        era_index=6,
        name="Recombination / CMB Release",
        description=(
            "Electrons bind with nuclei to form neutral atoms at about 380,000 years. "
            "Photons are released from the plasma and stream freely across space, creating "
            "the Cosmic Microwave Background -- the oldest light in the universe."
        ),
        temperature=3000.0,
    ),

    # Era 7: Dark Ages
    Milestone(
        cosmic_time=1.2e13,
        era_index=7,
        name="Dark Ages Begin",
        description=(
            "With no luminous sources yet formed, the universe enters a period of "
            "darkness. Neutral hydrogen gas fills the expanding cosmos, slowly cooling "
            "and clumping under gravity into the first dark matter halos."
        ),
        temperature=3000.0,
    ),

    # Era 8: First Stars / Reionization
    Milestone(
        cosmic_time=6.3e15,
        era_index=8,
        name="First Stars Ignite",
        description=(
            "After roughly 200 million years of darkness, the first Population III stars "
            "ignite. These massive, metal-free stars are hundreds of times the mass of "
            "our Sun and burn fiercely, flooding the universe with ultraviolet light."
        ),
        temperature=50.0,
    ),
    Milestone(
        cosmic_time=7.9e15,
        era_index=8,
        name="Reionization Begins",
        description=(
            "Ultraviolet photons from the first stars begin ionizing the neutral hydrogen "
            "gas between galaxies. Bubbles of ionized gas expand outward from each star "
            "and galaxy, gradually transforming the intergalactic medium."
        ),
        temperature=40.0,
    ),

    # Era 9: Galaxy Formation
    Milestone(
        cosmic_time=1.3e16,
        era_index=9,
        name="First Galaxies Form",
        description=(
            "Gravity assembles dark matter halos and gas clouds into the first proto-galaxies "
            "at around 400 million years. Mergers and gas accretion fuel intense bursts of "
            "star formation, building the diverse galaxy population we observe today."
        ),
        temperature=30.0,
    ),
    Milestone(
        cosmic_time=3.2e16,
        era_index=9,
        name="Reionization Complete",
        description=(
            "By about 1 billion years after the Big Bang, the intergalactic medium is "
            "fully ionized. The overlapping bubbles from countless galaxies have rendered "
            "the universe transparent to ultraviolet light once again."
        ),
        temperature=10.0,
    ),

    # Era 10: Large-Scale Structure
    Milestone(
        cosmic_time=3.1e17,
        era_index=10,
        name="Dark Energy Dominance",
        description=(
            "At roughly 9.8 billion years, the mysterious dark energy overtakes matter "
            "as the dominant component of the universe. The expansion of space begins to "
            "accelerate, driving galaxies apart ever faster."
        ),
        temperature=4.0,
    ),
]


ERA_DESCRIPTIONS: dict[int, str] = {
    0: (
        "The Planck Epoch is the earliest moment in cosmic history, lasting from the Big Bang "
        "to about 10^-43 seconds. All four fundamental forces -- gravity, electromagnetism, "
        "the strong force, and the weak force -- are thought to be unified into a single "
        "superforce. Our current physics cannot describe this era; a theory of quantum "
        "gravity is needed."
    ),
    1: (
        "During Grand Unification, gravity has separated as a distinct force, but the "
        "strong, weak, and electromagnetic forces remain unified. The universe is unimaginably "
        "hot -- over 10^28 Kelvin -- and filled with exotic particles and radiation. "
        "This era sets the stage for inflation."
    ),
    2: (
        "Inflation is a brief but dramatic period of exponential expansion. In less than "
        "10^-32 seconds, the observable universe expands from smaller than a proton to "
        "roughly the size of a grapefruit. This expansion smooths out irregularities, "
        "explains the universe's flatness, and generates the tiny density fluctuations "
        "that will seed all cosmic structure."
    ),
    3: (
        "The Quark-Gluon Plasma era is a seething soup of free quarks, gluons, and other "
        "elementary particles at temperatures exceeding a trillion degrees. The electroweak "
        "force splits into the electromagnetic and weak forces during this period. As the "
        "universe cools, quarks become confined into protons, neutrons, and other hadrons."
    ),
    4: (
        "In the Hadron Epoch, protons and neutrons are the dominant form of baryonic matter. "
        "Neutrinos decouple and stream freely, and most electron-positron pairs annihilate. "
        "The ratio of neutrons to protons freezes out, setting the stage for nucleosynthesis. "
        "This era lasts about one second of cosmic time."
    ),
    5: (
        "Big Bang Nucleosynthesis forges the lightest elements in the first few minutes. "
        "Protons and neutrons fuse into deuterium, helium-3, helium-4, and traces of lithium-7. "
        "The primordial abundances -- about 75% hydrogen and 25% helium by mass -- match "
        "observations precisely, providing one of the strongest confirmations of Big Bang theory."
    ),
    6: (
        "During Recombination, the universe cools enough for electrons to bind with nuclei, "
        "forming the first neutral atoms at about 380,000 years. Photons decouple from matter "
        "and stream freely as the Cosmic Microwave Background (CMB) -- the oldest light we can "
        "observe. Matter begins clumping under gravity into the seeds of cosmic structure."
    ),
    7: (
        "The Dark Ages are a period of cosmic quiet lasting hundreds of millions of years. "
        "No stars or galaxies have formed yet. The universe is filled with neutral hydrogen "
        "gas that slowly cools and collapses into dark matter halos. Tiny density fluctuations "
        "from inflation gradually grow under gravity, preparing for the first starlight."
    ),
    8: (
        "The era of First Stars and Reionization begins when massive, metal-free Population III "
        "stars ignite after about 200 million years. Their intense ultraviolet radiation "
        "carves expanding bubbles of ionized gas through the neutral intergalactic medium. "
        "This process, called reionization, gradually transforms the universe from opaque to "
        "transparent once more."
    ),
    9: (
        "Galaxy Formation is driven by gravity assembling dark matter halos, gas, and stars "
        "into the first proto-galaxies. Mergers, gas accretion, and feedback from supernovae "
        "and supermassive black holes shape galaxy morphology. By about 1 billion years, "
        "reionization is complete and the diverse galaxy population we observe today is taking shape."
    ),
    10: (
        "In the era of Large-Scale Structure, the cosmic web of galaxy filaments, clusters, "
        "and voids has fully matured. Dark energy -- discovered in 1998 -- dominates the "
        "energy budget and accelerates the expansion of the universe. Galaxies continue to "
        "evolve, merge, and form the grand structures of the observable cosmos."
    ),
}
