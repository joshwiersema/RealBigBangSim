---
phase: 2
slug: core-rendering
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already installed from Phase 1) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
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
| 02-01-01 | 01 | 1 | RNDR-01 | unit+integration | `python -m pytest tests/test_particles.py -v` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | RNDR-01 | unit | `python -m pytest tests/test_particles.py -v` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | RNDR-02 | unit | `python -m pytest tests/test_postprocess.py -v` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | RNDR-06 | unit | `python -m pytest tests/test_shaders.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_particles.py` — stubs for RNDR-01 (particle system compute shaders, SSBO management)
- [ ] `tests/test_postprocess.py` — stubs for RNDR-02 (bloom, HDR, tone mapping pipeline)
- [ ] `tests/test_shaders.py` — stubs for RNDR-06 (shader architecture, include preprocessing, per-era programs)

*Existing conftest.py and pytest infrastructure from Phase 1 covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 30+ FPS with 100K particles | RNDR-01 | Requires GPU and real-time rendering | Launch app, observe FPS counter in title bar with 100K particles |
| Visible bloom glow effect | RNDR-02 | Visual quality is perceptual | Launch app, verify bright particles have visible glow halos |
| Visual distinction between 2 shader variants | RNDR-06 | Visual difference is perceptual | Switch between hot/cool shader variants, confirm different color palettes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
