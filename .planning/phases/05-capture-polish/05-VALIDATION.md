---
phase: 5
slug: capture-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `py -3.14 -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `py -3.14 -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `py -3.14 -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `py -3.14 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CAPT-01 | unit | `py -3.14 -m pytest tests/test_screenshot.py -v` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | RNDR-05 | unit | `py -3.14 -m pytest tests/test_fullscreen.py -v` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | CAPT-02, CAPT-03 | unit | `py -3.14 -m pytest tests/test_video_recorder.py -v` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | CAPT-02 | integration | `py -3.14 -m pytest tests/test_app.py -v -k capture` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_screenshot.py` — stubs for CAPT-01 screenshot capture
- [ ] `tests/test_fullscreen.py` — stubs for RNDR-05 fullscreen and window state persistence
- [ ] `tests/test_video_recorder.py` — stubs for CAPT-02/CAPT-03 video recording and frame-locking

*Existing test infrastructure (pytest, conftest.py) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual screenshot quality | CAPT-01 | Requires visual inspection of output PNG | Capture screenshot, open file, verify it matches rendered scene |
| Video playback smoothness | CAPT-02 | Requires media player inspection | Record 10s clip, play in VLC, verify smooth playback |
| Fullscreen toggle visual | RNDR-05 | Requires window manager interaction | Press F11, verify window fills screen without artifacts |
| Window state restore | RNDR-05 | Requires app restart cycle | Resize window, close app, relaunch, verify same position/size |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
