---
phase: 4
slug: presentation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already installed) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~12 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 12 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | HUD-01, HUD-02, HUD-03, HUD-04, HUD-05 | unit+tdd | `python -m pytest tests/test_hud.py -v` | TDD | ⬜ pending |
| 04-01-02 | 01 | 1 | PHYS-04 | unit+tdd | `python -m pytest tests/test_milestones.py -v` | TDD | ⬜ pending |
| 04-02-01 | 02 | 1 | CAMR-02, CAMR-03 | unit+tdd | `python -m pytest tests/test_auto_camera.py -v` | TDD | ⬜ pending |
| 04-03-01 | 03 | 2 | all | integration | `python -m pytest tests/ -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

*Plan tasks use TDD — tests written alongside implementation. No separate Wave 0 stubs needed.*

*Existing conftest.py and pytest infrastructure from Phase 1 covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Era name displayed prominently | HUD-01 | Visual layout assessment | Launch app, verify era name visible in HUD |
| Physics readouts update in real-time | HUD-02 | Requires running simulation | Watch temperature/density values change as sim progresses |
| Educational text appears at key moments | HUD-03 | Content review | Play through eras, confirm explanations appear |
| Milestone notifications visible | PHYS-04 | Visual notification assessment | Play timeline, confirm ~20 milestone popups |
| Auto-camera navigates smoothly | CAMR-02 | Visual smoothness assessment | Enable auto-camera, watch full era tour |
| Pause/resume auto-camera works | CAMR-03 | Interactive behavior | During auto-camera, press key to pause, orbit freely, resume |
| HUD toggle on/off | HUD-05 | Interactive behavior | Press H key, verify HUD hides/shows |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 12s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-28
