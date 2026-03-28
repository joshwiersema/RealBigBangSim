---
phase: 3
slug: era-content
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-28
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already installed) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | PHYS-01, PHYS-02 | unit+tdd | `python -m pytest tests/test_nucleosynthesis.py tests/test_recombination.py tests/test_structure.py -v` | TDD | ⬜ pending |
| 03-01-02 | 01 | 1 | RNDR-03 | unit+tdd | `python -m pytest tests/test_era_visual_config.py -v` | TDD | ⬜ pending |
| 03-02-01 | 02 | 1 | RNDR-03 | unit | `python -m pytest tests/test_era_shaders.py -v` | TDD | ⬜ pending |
| 03-03-01 | 03 | 2 | RNDR-03, RNDR-04 | unit | `python -m pytest tests/test_era_transitions.py tests/test_era_sequence.py -v` | TDD | ⬜ pending |
| 03-03-02 | 03 | 2 | PHYS-01, PHYS-02 | integration | `python -m pytest tests/ -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

*Plan 01 Task 1 uses TDD (tests written alongside implementation). Plan 02 and 03 similarly create tests within their tasks. No separate Wave 0 stubs needed — test creation is integrated into each task's execution.*

*Existing conftest.py and pytest infrastructure from Phase 1 covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Each era visually distinct at a glance | RNDR-03 | Perceptual color distinction | Run through all 11 eras, confirm unique visual identity per era |
| Smooth crossfade transitions | RNDR-04 | Visual smoothness is perceptual | Watch transitions between adjacent eras, confirm no jarring cuts |
| Full timeline playthrough completes | PHYS-01 | Requires real-time GPU rendering | Launch app, play full timeline from start to end |
| CMB transition shows universe becoming transparent | PHYS-02 | Physics-driven visual effect | Watch Recombination era, confirm opacity transition |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
