"""FBO-based crossfade transition manager between cosmological eras (RNDR-04).

During era transitions, the scene is rendered twice (outgoing + incoming era)
into separate FBOs, then composited with a smoothstep blend factor that ramps
from 0.0 to 1.0 over the transition duration.

The EraTransitionManager uses the same RGBA16F FBO pattern as the
PostProcessingPipeline for consistent HDR rendering throughout the pipeline.

Usage:
    transition = EraTransitionManager(ctx, width, height)
    # Each frame:
    transition.check_transition(current_era, era_progress, transition_seconds)
    if transition.in_transition:
        transition.begin_outgoing()
        # ... render outgoing era ...
        transition.composite(incoming_texture, target_fbo)
"""
from __future__ import annotations

import moderngl
from moderngl_window import geometry

from bigbangsim.rendering.shader_loader import load_shader_source


def _smoothstep(t: float) -> float:
    """Hermite smoothstep interpolation: t*t*(3 - 2*t).

    Args:
        t: Input value, should be in [0, 1] range.

    Returns:
        Smoothly interpolated value in [0, 1].
    """
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class EraTransitionManager:
    """FBO-based crossfade between adjacent cosmological eras (RNDR-04).

    During era transitions, renders the scene twice (outgoing + incoming era),
    then composites with a blend factor that ramps from 0.0 to 1.0 over the
    transition duration. The blend factor follows a smoothstep curve for
    perceptually smooth transitions.

    Attributes:
        in_transition: Whether a crossfade is currently active.
        blend_factor: Current blend value (0.0 = outgoing, 1.0 = incoming).
        outgoing_era: Era index of the outgoing (fading out) era.
        incoming_era: Era index of the incoming (fading in) era.
    """

    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx

        # Transition FBO (same RGBA16F pattern as PostProcessingPipeline)
        self.transition_texture = ctx.texture((width, height), 4, dtype="f2")
        self.transition_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.transition_fbo = ctx.framebuffer(
            color_attachments=[self.transition_texture]
        )

        # Composite shader: fullscreen.vert + era_crossfade.frag
        fs_vert = load_shader_source("postprocess/fullscreen.vert")
        crossfade_frag = load_shader_source("postprocess/era_crossfade.frag")
        self.composite_prog = ctx.program(
            vertex_shader=fs_vert, fragment_shader=crossfade_frag
        )
        self.quad = geometry.quad_fs()

        # Transition state
        self.in_transition: bool = False
        self.blend_factor: float = 0.0
        self.outgoing_era: int = 0
        self.incoming_era: int = 0
        self.transition_elapsed: float = 0.0
        self.transition_duration: float = 2.0  # Updated from EraVisualConfig

        # Track previous era to detect changes
        self._prev_era: int = -1

    def check_transition(
        self,
        current_era: int,
        frame_time: float,
        transition_seconds: float,
    ) -> None:
        """Check if we should start/continue/end a transition.

        Called once per frame. Starts a transition when the current era
        changes from the previous era. Advances the blend factor during
        an active transition.

        Args:
            current_era: The current era index from the simulation.
            frame_time: Wall-clock seconds elapsed since last frame.
            transition_seconds: Duration of crossfade from the incoming
                               era's EraVisualConfig.
        """
        if self._prev_era == -1:
            # First frame: initialize without triggering transition
            self._prev_era = current_era
            return

        if current_era != self._prev_era and not self.in_transition:
            # Era just changed: start transition
            self.in_transition = True
            self.outgoing_era = self._prev_era
            self.incoming_era = current_era
            self.transition_elapsed = 0.0
            self.transition_duration = max(0.01, transition_seconds)
            self.blend_factor = 0.0

        if self.in_transition:
            self.transition_elapsed += frame_time
            raw_t = self.transition_elapsed / self.transition_duration
            raw_t = max(0.0, min(1.0, raw_t))
            self.blend_factor = _smoothstep(raw_t)

            if self.blend_factor >= 1.0:
                # Transition complete
                self.in_transition = False
                self.blend_factor = 1.0
                self._prev_era = current_era
        else:
            # No transition active: track current era
            self._prev_era = current_era

    def begin_outgoing(self) -> None:
        """Bind transition FBO for rendering the outgoing era.

        After calling this, render the outgoing era's scene. The result
        will be stored in self.transition_texture for compositing.
        """
        self.transition_fbo.use()
        self.transition_fbo.clear(0.0, 0.0, 0.0, 0.0)

    def composite(
        self,
        incoming_texture: moderngl.Texture,
        target_fbo,
    ) -> None:
        """Composite outgoing + incoming textures with blend factor.

        Renders a fullscreen quad that samples both textures and blends
        them according to the current blend_factor.

        Args:
            incoming_texture: Texture containing the incoming era's rendered scene.
            target_fbo: Target framebuffer for the composited result.
        """
        target_fbo.use()
        self.transition_texture.use(location=0)
        incoming_texture.use(location=1)
        self.composite_prog["u_outgoing"].value = 0
        self.composite_prog["u_incoming"].value = 1
        self.composite_prog["u_blend_factor"].value = self.blend_factor
        self.quad.render(self.composite_prog)

    def resize(self, width: int, height: int) -> None:
        """Recreate transition FBO for new window dimensions.

        Args:
            width: New window width in pixels.
            height: New window height in pixels.
        """
        self.transition_texture.release()
        self.transition_fbo.release()

        self.transition_texture = self.ctx.texture(
            (width, height), 4, dtype="f2"
        )
        self.transition_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.transition_fbo = self.ctx.framebuffer(
            color_attachments=[self.transition_texture]
        )

    def release(self) -> None:
        """Release all GPU resources."""
        self.transition_texture.release()
        self.transition_fbo.release()
        self.composite_prog.release()
