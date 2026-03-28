# BigBangSim

## What This Is

A cinematic, scientifically accurate Big Bang simulation that renders the full 13.8 billion year cosmic timeline in real-time 3D. Built in Python with ModernGL and GPU-accelerated GLSL shaders, it takes the user on a guided journey from the initial singularity through inflation, particle formation, nucleosynthesis, the cosmic microwave background, dark ages, first stars, and galaxy formation — with rich educational overlays, generative ambient soundscapes, and stunning realistic visuals.

## Core Value

The simulation must be both scientifically accurate AND visually stunning — real cosmological physics driving beautiful real-time 3D rendering that teaches as it mesmerizes.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Full cosmic timeline simulation (singularity through galaxy formation)
- [ ] Real-time 3D rendering via ModernGL with GLSL shaders
- [ ] GPU-accelerated particle system (100K-1M particles)
- [ ] Scientifically accurate physics for each cosmological era
- [ ] Cinematic auto-camera with smooth era transitions
- [ ] Manual camera override (orbit, zoom, pan) when paused
- [ ] Rich educational HUD (era labels, physics explanations, temperature/density readouts, milestone markers)
- [ ] Generative ambient soundscape evolving per era
- [ ] Screenshot capture (high-res, any moment)
- [ ] Video recording (full cinematic run to MP4)
- [ ] Cosmological eras: Planck epoch, Grand Unification, Inflation, Quark-Gluon Plasma, Hadron epoch, Nucleosynthesis, Recombination/CMB, Dark Ages, Reionization/First Stars, Galaxy Formation, Large-Scale Structure

### Out of Scope

- Web-based rendering — desktop OpenGL application only
- Multiplayer or networked features — single-user experience
- VR/AR support — standard windowed 3D rendering
- Real-time N-body gravity simulation at galactic scale — use approximations and visual techniques for structure formation
- Mobile support — desktop Python application

## Context

- **Domain:** Computational cosmology visualization. The simulation spans physics from quantum field theory (early universe) to gravitational dynamics (structure formation). Each era requires different mathematical models.
- **Key physics models needed:** Friedmann equations (expansion), nucleosynthesis yields (BBN), recombination physics (Saha equation), Jeans instability (structure formation), Press-Schechter formalism (halo mass function).
- **Visual challenge:** Each era looks fundamentally different — from pure energy/radiation through plasma to discrete matter structures. Shader programs must transition smoothly between visual paradigms.
- **Audio challenge:** Generative ambient soundscape must be tied to physical parameters (temperature, density, expansion rate) so it feels connected to what's happening, not arbitrary.
- **Target audience:** Anyone curious about cosmology — from students to enthusiasts. The educational overlay should be accessible but not dumbed down.

## Constraints

- **Tech Stack**: Python 3.10+, ModernGL, GLSL shaders, PyOpenAL or similar for audio — chosen for balance of GPU performance and Python ecosystem
- **Performance**: Must maintain 30+ FPS on a modern GPU (GTX 1060 or equivalent) with 100K+ particles
- **Scientific Accuracy**: All physics parameters must come from published cosmological data (Planck 2018 results, PDG values). No made-up numbers.
- **Platform**: Windows primary (user's environment), but code should be cross-platform compatible
- **Dependencies**: Minimize exotic dependencies. Prefer well-maintained PyPI packages.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ModernGL for rendering | Best Python OpenGL wrapper — clean API, shader-first design, good performance | -- Pending |
| GLSL shaders for particle rendering | GPU acceleration essential for 100K+ particles at 30+ FPS | -- Pending |
| Cinematic-first with manual override | Guided experience is primary, exploration is secondary | -- Pending |
| Generative audio tied to physics | Sound should feel connected to simulation state, not pre-recorded tracks | -- Pending |
| Full timeline scope | Covering all major eras makes this a complete educational tool | -- Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-27 after initialization*
