---
phase: 03-era-content
plan: 01
subsystem: simulation
tags: [bbn, nucleosynthesis, saha-equation, recombination, jeans-mass, press-schechter, cosmology, physics]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: constants.py with Planck 2018/PDG values, cosmology.py with Friedmann integration
provides:
  - BBN yield lookup by temperature (get_bbn_fractions)
  - Saha ionization fraction lookup by temperature (build_ionization_table, get_ionization_fraction)
  - Jeans mass and Press-Schechter collapsed fraction (compute_jeans_mass, build_collapsed_fraction_table, get_collapsed_fraction)
  - Data-driven EraVisualConfig for all 11 eras with shader keys, colors, and particle parameters
affects: [03-era-content, 04-audio]

# Tech tracking
tech-stack:
  added: [scipy.special.erfc]
  patterns: [physics-sub-module pattern with lookup tables, frozen dataclass config pattern]

key-files:
  created:
    - bigbangsim/simulation/physics/__init__.py
    - bigbangsim/simulation/physics/nucleosynthesis.py
    - bigbangsim/simulation/physics/recombination.py
    - bigbangsim/simulation/physics/structure.py
    - bigbangsim/simulation/era_visual_config.py
    - tests/test_nucleosynthesis.py
    - tests/test_recombination.py
    - tests/test_structure.py
    - tests/test_era_visual_config.py
  modified: []

key-decisions:
  - "Numerically stable Saha solver: use 2A/(A+sqrt(A^2+4A)) for large A to avoid catastrophic cancellation"
  - "Monotonicity enforcement in ionization table to eliminate floating-point noise at saturation boundary"
  - "Pre-BBN yields approximated as final PDG yields for visualization simplicity (no intermediate nuclear reaction network)"

patterns-established:
  - "Physics sub-module pattern: build_*_table() + get_*() for precomputed lookup with interpolation"
  - "Frozen dataclass config pattern: immutable per-era config data lives in simulation layer"
  - "Simulation-rendering boundary: physics modules have zero imports from bigbangsim.rendering"

requirements-completed: [PHYS-01, PHYS-02]

# Metrics
duration: 8min
completed: 2026-03-28
---

# Phase 3 Plan 1: Era Physics & Visual Config Summary

**BBN yields (PDG 2024), Saha ionization fraction, Jeans mass, Press-Schechter collapsed fraction, and 11-era EraVisualConfig data structure**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-28T20:29:30Z
- **Completed:** 2026-03-28T20:37:31Z
- **Tasks:** 2
- **Files modified:** 9 created

## Accomplishments
- Three physics sub-modules providing era-specific GPU uniform data: BBN yields match PDG 2024 to 3 sig figs, Saha equation transitions correctly around 3000K, Jeans mass scales as T^1.5 and rho^-0.5, Press-Schechter monotonically increasing
- EraVisualConfig frozen dataclass with complete configuration table for all 11 cosmological eras, each with unique shader key, color palettes, particle behavior, and transition timing
- Full test coverage: 69 new tests, all 199 total tests passing, zero rendering imports in any simulation module

## Task Commits

Each task was committed atomically:

1. **Task 1: Physics sub-modules (TDD RED)** - `fa54474` (test)
   **Task 1: Physics sub-modules (TDD GREEN)** - `8a06445` (feat)
2. **Task 2: EraVisualConfig** - `e82b123` (feat)

_Note: Task 1 used TDD with RED (failing tests) then GREEN (implementation) commits._

## Files Created/Modified
- `bigbangsim/simulation/physics/__init__.py` - Package init re-exporting all physics functions
- `bigbangsim/simulation/physics/nucleosynthesis.py` - BBN yield lookup with PDG 2024 values and log-T interpolation
- `bigbangsim/simulation/physics/recombination.py` - Saha equation ionization fraction with numerically stable quadratic solver
- `bigbangsim/simulation/physics/structure.py` - Jeans mass and Press-Schechter collapsed fraction using scipy.special.erfc
- `bigbangsim/simulation/era_visual_config.py` - Frozen dataclass + 11-entry config table for all cosmological eras
- `tests/test_nucleosynthesis.py` - 12 tests: PDG yield verification, mass conservation, interpolation
- `tests/test_recombination.py` - 15 tests: Saha transition, table construction, clamping, boundary
- `tests/test_structure.py` - 21 tests: Jeans scaling laws, Press-Schechter monotonicity, erfc usage
- `tests/test_era_visual_config.py` - 21 tests: data integrity, index consistency, value constraints, immutability

## Decisions Made
- **Numerically stable Saha solver:** For large A (high temperature), used equivalent form `x = 2A/(A+sqrt(A^2+4A))` instead of `(-A+sqrt(A^2+4A))/2` to avoid catastrophic cancellation. Also enforced monotonicity post-hoc to eliminate residual floating-point noise at the saturation boundary.
- **Pre-BBN yield approximation:** Pre-BBN (T>1e9K) yields approximated as final PDG values since the simulation visualizes endpoints, not intermediate nuclear reaction dynamics. This simplifies the interpolation without affecting visual accuracy.
- **Gravity threshold at era 7:** gravity_strength is exactly 0.0 for eras 0-6 (pre-structure formation) and positive for eras 7-10, reflecting the physical transition from radiation-dominated to matter-dominated structure growth.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Saha equation numerical instability at high temperatures**
- **Found during:** Task 1 (Physics sub-modules, GREEN phase)
- **Issue:** Quadratic formula `(-A + sqrt(A^2 + 4A))/2` suffers catastrophic cancellation when A >> 1, causing ionization fraction to fluctuate near 1.0 and violate monotonicity
- **Fix:** Added numerically stable branch `2A/(A+sqrt(A^2+4A))` for A > 1e6, plus monotonicity enforcement pass
- **Files modified:** bigbangsim/simulation/physics/recombination.py
- **Verification:** test_ionization_monotonically_increasing now passes
- **Committed in:** 8a06445 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential fix for numerical correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed Saha instability.

## Known Stubs
None - all modules provide complete implementations with real physics calculations.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Physics data layer complete: BBN, recombination, structure formation modules ready for shader consumption
- EraVisualConfig ready for Plan 02's per-era GLSL shaders (shader_key lookup, color/param uniforms)
- Plan 03 can wire EraVisualConfig into the render loop for era transitions
- All 199 tests green, simulation-rendering boundary preserved

## Self-Check: PASSED

- All 9 created files exist on disk
- All 3 task commits (fa54474, 8a06445, e82b123) found in git log
- 199/199 tests passing
- Zero rendering imports in simulation modules

---
*Phase: 03-era-content*
*Completed: 2026-03-28*
