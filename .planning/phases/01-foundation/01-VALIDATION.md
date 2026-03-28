---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml (Wave 0 creates) |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PHYS-05 | unit | `pytest tests/test_constants.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CAMR-01 | integration | `pytest tests/test_camera.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | CAMR-04 | integration | `pytest tests/test_controls.py` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | PHYS-06 | unit | `pytest tests/test_simulation.py` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | PHYS-03 | unit | `pytest tests/test_timeline.py` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 2 | PHYS-07 | unit | `pytest tests/test_coordinates.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (mock window context, test constants)
- [ ] `tests/test_constants.py` — stubs for PHYS-05 (constant values, citations)
- [ ] `tests/test_camera.py` — stubs for CAMR-01 (orbit, zoom, pan, damping)
- [ ] `tests/test_controls.py` — stubs for CAMR-04 (play/pause, speed)
- [ ] `tests/test_simulation.py` — stubs for PHYS-06 (fixed timestep, interpolation)
- [ ] `tests/test_timeline.py` — stubs for PHYS-03 (logarithmic mapping, era budgets)
- [ ] `tests/test_coordinates.py` — stubs for PHYS-07 (camera-relative, era-specific coords)
- [ ] `pytest` install — add to dev dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Camera orbit/zoom feels smooth | CAMR-01 | Subjective damping feel | Launch app, drag to orbit, scroll to zoom — no jitter, smooth deceleration |
| Timeline bar is visually intuitive | PHYS-03 | Visual layout judgment | Launch app, observe timeline bar — eras visible, position indicator tracks time |
| 3D window launches correctly | CAMR-01 | GPU/OS dependent | Run `python -m bigbangsim` — window appears, no black screen, test scene visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
