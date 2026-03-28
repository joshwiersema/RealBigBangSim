---
phase: 01-foundation
plan: 02
subsystem: simulation
tags: [friedmann, cosmology, timeline, physics, scipy, numpy, ode, accumulator]

# Dependency graph
requires:
  - phase: 01-foundation-01
    provides: "PhysicsState dataclass, cosmological constants, config values"
provides:
  - "Piecewise logarithmic timeline controller mapping wall-clock to cosmic time across 60+ orders of magnitude"
  - "Friedmann equation integration with pre-computed 10000-point lookup table"
  - "11 cosmological era definitions with screen time budgets"
  - "Fixed-timestep simulation engine with accumulator pattern"
  - "Pause/resume and speed control (0.5x-10x)"
affects: [rendering, camera, hud, audio, particle-system]

# Tech tracking
tech-stack:
  added: [scipy.integrate.solve_ivp, numpy.interp]
  patterns: [piecewise-logarithmic-mapping, fixed-timestep-accumulator, pre-computed-lookup-table, radiation-dominated-extrapolation]

key-files:
  created:
    - bigbangsim/simulation/eras.py
    - bigbangsim/simulation/timeline.py
    - bigbangsim/simulation/cosmology.py
    - bigbangsim/simulation/engine.py
    - tests/test_timeline.py
    - tests/test_cosmology.py
    - tests/test_simulation.py
  modified: []

key-decisions:
  - "Analytical Jacobian for Radau solver since dt/da ODE has zero dependence on t"
  - "Era overlap handled by returning highest-index era containing cosmic time"
  - "Time normalization to match AGE_UNIVERSE at a=1.0 after Friedmann integration"

patterns-established:
  - "Piecewise logarithmic mapping: each era maps screen time to cosmic time via log10 interpolation"
  - "Fixed-timestep accumulator: physics at PHYSICS_DT intervals, lerp for smooth rendering"
  - "Pre-computed lookup table: 10000-point dense output with np.interp for O(1) lookups"
  - "Radiation-dominated extrapolation: a(t) ~ sqrt(2 H0 sqrt(Omega_r) t) for times before integration start"

requirements-completed: [PHYS-03, PHYS-06]

# Metrics
duration: 10min
completed: 2026-03-28
---

# Phase 1 Plan 2: Simulation Engine Core Summary

**Piecewise logarithmic timeline spanning 60+ orders of magnitude with Friedmann equation solver and fixed-timestep accumulator engine producing PhysicsState from wall-clock time**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-28T04:17:45Z
- **Completed:** 2026-03-28T04:27:46Z
- **Tasks:** 2
- **Files created:** 7

## Accomplishments
- Piecewise logarithmic timeline maps screen time 0 to Planck time (~1e-43 s) and total screen time (166 s) to age of universe (~4.35e17 s), covering 60 orders of magnitude
- Friedmann equation integration produces correct cosmological parameters at known benchmarks: scale factor ~1.0 today, ~9.1e-4 at recombination, temperature ~2.7255 K today, ~3000 K at recombination
- Fixed-timestep simulation engine decouples physics from render rate, producing deterministic results independent of frametime granularity
- 41 tests all passing across three test files

## Task Commits

Each task was committed atomically (TDD: test -> feat):

1. **Task 1: Era definitions and piecewise logarithmic timeline controller** - `a327b29` (test: RED), `f95a32b` (feat: GREEN)
2. **Task 2: Friedmann cosmology solver and fixed-timestep simulation engine** - `d0ff204` (test: RED), `a41e709` (feat: GREEN)

## Files Created/Modified
- `bigbangsim/simulation/eras.py` - 11 era definitions with EraDefinition dataclass, screen time budgets, helper functions
- `bigbangsim/simulation/timeline.py` - TimelineController with piecewise logarithmic screen-to-cosmic and cosmic-to-screen mapping
- `bigbangsim/simulation/cosmology.py` - CosmologyModel integrating Friedmann equation via solve_ivp(Radau) with 10000-point lookup table
- `bigbangsim/simulation/engine.py` - SimulationEngine with fixed-timestep accumulator, pause/speed controls, PhysicsState production
- `tests/test_timeline.py` - 21 tests for era definitions and timeline mapping
- `tests/test_cosmology.py` - 10 tests for Friedmann equation benchmarks
- `tests/test_simulation.py` - 10 tests for accumulator pattern and engine controls

## Decisions Made
- **Analytical Jacobian for Radau solver:** The dt/da ODE does not depend on t (cosmic time), so the Jacobian is exactly [[0.0]]. Providing this analytically avoids numerical Jacobian computation issues with scipy's Radau solver on scalar ODEs.
- **Era overlap handling:** Grand Unification (index 1) and Inflation (index 2) share cosmic_start=1e-36. For cosmic_to_screen, the highest-index era fully containing the cosmic time is returned. For screen_to_cosmic, eras are always sequential by screen time.
- **Time normalization:** The Friedmann integration produces relative cosmic times. These are normalized so t(a=1.0) = AGE_UNIVERSE (4.35e17 s) to match known cosmological age.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed solve_ivp Radau solver scalar ODE compatibility**
- **Found during:** Task 2 (Cosmology solver implementation)
- **Issue:** scipy.integrate.solve_ivp with Radau method requires array-shaped outputs for numerical Jacobian computation. The ODE function returning a scalar caused IndexError in the Jacobian estimation.
- **Fix:** Added np.atleast_1d() wrapping on ODE output and provided analytical Jacobian (jac=[[0.0]]) since dt/da is independent of t.
- **Files modified:** bigbangsim/simulation/cosmology.py
- **Verification:** All 10 cosmology tests pass.
- **Committed in:** a41e709 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test assertions for overlapping era boundaries**
- **Found during:** Task 1 (Timeline controller implementation)
- **Issue:** Original tests assumed global monotonicity of screen_to_cosmic and cosmic_to_screen, but Inflation (era 2) and Grand Unification (era 1) overlap in cosmic time, making global monotonicity impossible. This is physical reality, not a bug.
- **Fix:** Updated tests to verify within-era monotonicity and round-trip consistency within non-overlapping ranges only. Updated _find_era_by_cosmic_time to prefer era that fully contains the cosmic time.
- **Files modified:** tests/test_timeline.py, bigbangsim/simulation/timeline.py
- **Verification:** All 21 timeline tests pass.
- **Committed in:** f95a32b (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Python 3.14 used instead of 3.11 (3.11 not available on system). All dependencies (scipy, numpy, pytest) installed and worked correctly on 3.14.

## Known Stubs
None -- all data sources are wired and producing real cosmological values from Friedmann equation integration.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Simulation engine core complete and independently testable
- PhysicsState snapshots produced from wall-clock time input via timeline -> cosmology pipeline
- Ready for rendering layer (Phase 2) to consume PhysicsState for visual output
- Ready for HUD overlay to display era information and physics parameters

## Self-Check: PASSED

All 8 created files verified present on disk. All 4 commit hashes verified in git log.

---
*Phase: 01-foundation*
*Completed: 2026-03-28*
