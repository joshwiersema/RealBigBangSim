---
phase: 01-foundation
plan: 01
subsystem: simulation
tags: [cosmology, planck-2018, pdg, dataclass, constants, physics-state, interpolation]

# Dependency graph
requires: []
provides:
  - "Cosmological constants module with Planck 2018/PDG citations (bigbangsim/simulation/constants.py)"
  - "PhysicsState dataclass with lerp interpolation (bigbangsim/simulation/state.py)"
  - "Python package skeleton installable via pip (pyproject.toml)"
  - "Test infrastructure with pytest (tests/conftest.py)"
affects: [01-02, 01-03, 02-particles, 03-eras, 04-audio]

# Tech tracking
tech-stack:
  added: [moderngl-5.12.0, moderngl-window-3.1.1, PyGLM-2.8.3, numpy-2.4.3, scipy-1.17.1, pytest-9.0.2, ruff-0.15.8]
  patterns: [tdd-red-green, simulation-rendering-boundary, citation-registry]

key-files:
  created:
    - pyproject.toml
    - bigbangsim/__init__.py
    - bigbangsim/__main__.py
    - bigbangsim/config.py
    - bigbangsim/simulation/__init__.py
    - bigbangsim/simulation/constants.py
    - bigbangsim/simulation/state.py
    - bigbangsim/rendering/__init__.py
    - bigbangsim/shaders/.gitkeep
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_constants.py
    - tests/test_state.py
    - .gitignore
  modified: []

key-decisions:
  - "Used Python 3.14 (user's installed version) instead of 3.11 -- all Phase 1 deps have wheels/source builds for 3.14, audio (pyo) deferred to Phase 4"
  - "pyproject.toml build-backend set to setuptools.build_meta (standard setuptools PEP 517 backend)"

patterns-established:
  - "Simulation-rendering boundary: simulation modules have zero imports from rendering layer"
  - "Citation registry: every cosmological constant has a CITATIONS dict entry with source paper reference"
  - "TDD workflow: tests written before implementation, RED commit then GREEN commit"
  - "PhysicsState as one-way communication interface: simulation writes, rendering reads"

requirements-completed: [PHYS-05, PHYS-07]

# Metrics
duration: 6min
completed: 2026-03-28
---

# Phase 1 Plan 01: Project Scaffolding Summary

**Planck 2018/PDG cosmological constants with citation registry, PhysicsState dataclass with lerp interpolation, and installable Python package skeleton**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T04:07:57Z
- **Completed:** 2026-03-28T04:13:51Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Centralized cosmological constants module with 12+ constants from Planck 2018, PDG 2024, CODATA 2018, each with inline citation comments and a CITATIONS registry dict
- PhysicsState dataclass providing the one-way interface between simulation and rendering layers, with lerp() interpolation that correctly handles discrete fields (current_era)
- Full Python package installable via `pip install -e ".[dev]"` with moderngl, PyGLM, numpy, scipy dependencies
- 19 passing tests covering constant values, citation completeness, self-consistency (Omega sum, flat universe), interpolation correctness, and layer isolation

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Cosmological constants module** (TDD)
   - `4afb0e1` test(01-01): add failing tests for cosmological constants module (TDD RED)
   - `b6c8025` feat(01-01): project scaffolding and cosmological constants module (TDD GREEN)
2. **Task 2: PhysicsState dataclass** (TDD)
   - `587e598` test(01-01): add failing tests for PhysicsState dataclass (TDD RED)
   - `26720d0` feat(01-01): PhysicsState dataclass with lerp interpolation (TDD GREEN)
3. **Housekeeping**
   - `2b0b1c4` chore(01-01): add .gitignore for Python project

## Files Created/Modified
- `pyproject.toml` - Project configuration with dependencies (moderngl, PyGLM, numpy, scipy)
- `bigbangsim/__init__.py` - Package init with version
- `bigbangsim/__main__.py` - Placeholder entry point
- `bigbangsim/config.py` - Window size, physics dt, speed control defaults
- `bigbangsim/simulation/__init__.py` - Simulation subpackage
- `bigbangsim/simulation/constants.py` - Planck 2018/PDG cosmological constants with citations
- `bigbangsim/simulation/state.py` - PhysicsState dataclass with lerp interpolation
- `bigbangsim/rendering/__init__.py` - Rendering subpackage (empty)
- `bigbangsim/shaders/.gitkeep` - Shader directory placeholder
- `tests/__init__.py` - Test package
- `tests/conftest.py` - Shared test fixtures
- `tests/test_constants.py` - 12 tests verifying constant values and citations
- `tests/test_state.py` - 7 tests verifying PhysicsState construction and lerp
- `.gitignore` - Python project gitignore

## Decisions Made
- Used Python 3.14 (user's installed version) instead of stack-recommended 3.11. All Phase 1 deps install cleanly. Audio (pyo) compatibility deferred to Phase 4.
- Set build backend to `setuptools.build_meta` (standard PEP 517 backend, not the legacy backend initially attempted).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pyproject.toml build backend**
- **Found during:** Task 1 (pip install -e ".[dev]")
- **Issue:** Plan specified no build-system section; initial attempt used `setuptools.backends._legacy:_Backend` which does not exist
- **Fix:** Set build-backend to `setuptools.build_meta` (standard PEP 517)
- **Files modified:** pyproject.toml
- **Verification:** `pip install -e ".[dev]"` succeeds
- **Committed in:** b6c8025

**2. [Rule 2 - Missing Critical] Added .gitignore**
- **Found during:** After Task 2 (git status showed untracked generated files)
- **Issue:** No .gitignore existed, __pycache__ and egg-info directories showing as untracked
- **Fix:** Created .gitignore covering Python build artifacts, caches, IDE files, OS files
- **Files modified:** .gitignore
- **Verification:** `git status --short` shows clean working tree
- **Committed in:** 2b0b1c4

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes necessary for correct project setup. No scope creep.

## Issues Encountered
- Python 3.14 not available as `python` command on PATH; resolved by using `py -3.14` launcher

## Known Stubs
- `bigbangsim/__main__.py` - Contains placeholder `print("BigBangSim v0.1.0 - launching...")`. Will be replaced in Plan 03 with actual simulation loop. **Intentional per plan.**

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Constants module ready for use by cosmology engine (Plan 03)
- PhysicsState interface ready for simulation loop and rendering layer
- Test infrastructure ready for additional test modules
- Package installable for development workflow

## Self-Check: PASSED

All 15 files verified present. All 5 commits verified in git log.

---
*Phase: 01-foundation*
*Completed: 2026-03-28*
