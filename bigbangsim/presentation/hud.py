"""imgui-based HUD overlay manager for BigBangSim (HUD-01..HUD-05).

Renders all educational HUD panels using imgui: era info, live physics
readouts, educational text, milestone notifications, timeline bar, and
controls hint. HUDManager does NOT own the imgui context or renderer --
those live in app.py. It receives simulation state and delegates
rendering to per-panel methods.

Design follows PhET principles: transparent, non-intrusive overlays that
inform without obstructing the visual experience.
"""
from __future__ import annotations

from imgui_bundle import imgui

from bigbangsim.presentation.educational_content import ERA_DESCRIPTIONS
from bigbangsim.presentation.milestones import MilestoneManager
from bigbangsim.simulation.eras import EraDefinition


# ---------------------------------------------------------------------------
# imgui window flags for all HUD panels: no title bar, no resize, no move,
# no scrollbar, always auto-resize, no saved settings.
# ---------------------------------------------------------------------------

HUD_FLAGS = (
    imgui.WindowFlags_.no_title_bar
    | imgui.WindowFlags_.no_resize
    | imgui.WindowFlags_.no_move
    | imgui.WindowFlags_.no_scrollbar
    | imgui.WindowFlags_.always_auto_resize
    | imgui.WindowFlags_.no_saved_settings
)

# ---------------------------------------------------------------------------
# Era colors for timeline bar (same 11 colors as the old GLSL timeline bar).
# Each tuple is (R, G, B, A) with alpha 0.8.
# ---------------------------------------------------------------------------

ERA_COLORS: list[tuple[float, float, float, float]] = [
    (1.0, 1.0, 1.0, 0.8),      # 0: Planck - white
    (0.8, 0.6, 1.0, 0.8),      # 1: GUT - lavender
    (1.0, 0.9, 0.3, 0.8),      # 2: Inflation - yellow
    (1.0, 0.3, 0.1, 0.8),      # 3: QGP - orange-red
    (0.9, 0.5, 0.2, 0.8),      # 4: Hadron - orange
    (0.3, 0.8, 0.3, 0.8),      # 5: Nucleosynthesis - green
    (1.0, 0.8, 0.4, 0.8),      # 6: CMB - warm yellow
    (0.15, 0.1, 0.2, 0.8),     # 7: Dark Ages - near black
    (0.4, 0.6, 1.0, 0.8),      # 8: First Stars - blue
    (0.6, 0.4, 0.8, 0.8),      # 9: Galaxy Formation - purple
    (0.3, 0.5, 0.9, 0.8),      # 10: LSS - deep blue
]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_physics_value(value: float, unit: str) -> str:
    """Format a physics value with appropriate notation.

    Uses scientific notation for very large or very small values,
    and fixed-point for moderate values.

    Args:
        value: The numeric value.
        unit: The SI unit string (e.g., "K", "kg/m^3").

    Returns:
        Formatted string like "1.00e+32 K" or "2725.0000 K".
    """
    if abs(value) < 1e-3 or abs(value) > 1e6:
        return f"{value:.2e} {unit}"
    return f"{value:.4f} {unit}"


def format_cosmic_time(seconds: float) -> str:
    """Format cosmic time in human-readable units.

    Automatically selects the most appropriate unit (seconds, minutes,
    hours, years, Myr, Gyr) based on magnitude.

    Args:
        seconds: Cosmic time in seconds after the Big Bang.

    Returns:
        Formatted string like "3.80e+05 yr" or "13.80 Gyr".
    """
    year = 86400.0 * 365.25

    if seconds < 60:
        return f"{seconds:.2e} s"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    if seconds < year:
        return f"{seconds / 3600:.1f} hr"
    if seconds < year * 1e6:
        return f"{seconds / year:.2e} yr"
    if seconds < year * 1e9:
        return f"{seconds / (year * 1e6):.2f} Myr"
    return f"{seconds / (year * 1e9):.2f} Gyr"


# ---------------------------------------------------------------------------
# HUDManager
# ---------------------------------------------------------------------------

class HUDManager:
    """Renders all HUD overlay panels via imgui.

    Does NOT manage imgui context or renderer (those stay in app.py).
    Receives simulation state and delegates rendering to panel methods.

    Attributes:
        visible: Whether the entire HUD is drawn.
        show_physics: Whether the physics readout panel is drawn.
        show_education: Whether the educational text panel is drawn.
        show_milestones: Whether milestone notifications are drawn.
    """

    def __init__(self) -> None:
        self.visible: bool = True
        self.show_physics: bool = True
        self.show_education: bool = True
        self.show_milestones: bool = True

    def toggle(self) -> None:
        """Toggle the entire HUD on/off."""
        self.visible = not self.visible

    def render(
        self,
        state,
        sim,
        milestones: MilestoneManager,
        camera_auto: bool,
        eras: list[EraDefinition],
    ) -> None:
        """Render all HUD panels for the current frame.

        Must be called between imgui.new_frame() and imgui.render(),
        which are managed by app.py.

        Args:
            state: PhysicsState snapshot from the simulation engine.
            sim: SimulationEngine (for screen_time, timeline access).
            milestones: MilestoneManager with active notifications.
            camera_auto: Whether the cinematic camera is in auto mode.
            eras: List of EraDefinition objects (the 11 eras).
        """
        if not self.visible:
            return

        display_size = imgui.get_io().display_size

        self._render_era_panel(state, eras, display_size)

        if self.show_physics:
            self._render_physics_panel(state, display_size)

        if self.show_education:
            self._render_education_panel(state, display_size)

        if self.show_milestones:
            self._render_milestone_notifications(milestones, display_size)

        self._render_timeline_bar(state, sim, eras, display_size)
        self._render_controls_hint(camera_auto, display_size)

    # ------------------------------------------------------------------
    # Panel methods
    # ------------------------------------------------------------------

    def _render_era_panel(self, state, eras, display_size) -> None:
        """Top-left: current era name and short description."""
        imgui.set_next_window_pos(imgui.ImVec2(20, 20))
        imgui.set_next_window_bg_alpha(0.6)
        imgui.begin("Era Info", None, HUD_FLAGS)

        era = eras[state.current_era] if 0 <= state.current_era < len(eras) else None

        if era is not None:
            imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(1.0, 0.9, 0.7, 1.0))
            imgui.set_window_font_scale(1.5)
            imgui.text(era.name)
            imgui.set_window_font_scale(1.0)
            imgui.pop_style_color()
            imgui.text(era.description)

        imgui.end()

    def _render_physics_panel(self, state, display_size) -> None:
        """Top-right: live physics readouts."""
        imgui.set_next_window_pos(imgui.ImVec2(display_size.x - 280, 20))
        imgui.set_next_window_bg_alpha(0.6)
        imgui.begin("Physics", None, HUD_FLAGS)

        imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(0.7, 0.9, 1.0, 1.0))
        imgui.text("Physics")
        imgui.pop_style_color()
        imgui.separator()

        imgui.text(f"Temperature: {format_physics_value(state.temperature, 'K')}")
        imgui.text(f"Scale Factor: {state.scale_factor:.6e}")
        imgui.text(f"Matter Density: {format_physics_value(state.matter_density, 'kg/m^3')}")
        imgui.text(f"Radiation Density: {format_physics_value(state.radiation_density, 'kg/m^3')}")
        imgui.text(f"Hubble Parameter: {format_physics_value(state.hubble_param, 'km/s/Mpc')}")
        imgui.text(f"Cosmic Time: {format_cosmic_time(state.cosmic_time)}")

        imgui.end()

    def _render_education_panel(self, state, display_size) -> None:
        """Left side below era panel: rich era description text."""
        imgui.set_next_window_pos(imgui.ImVec2(20, 120))
        imgui.set_next_window_bg_alpha(0.5)
        imgui.begin("Education", None, HUD_FLAGS)

        imgui.push_text_wrap_pos(350.0)
        desc = ERA_DESCRIPTIONS.get(state.current_era, "")
        imgui.text_wrapped(desc)
        imgui.pop_text_wrap_pos()

        imgui.end()

    def _render_milestone_notifications(self, milestones, display_size) -> None:
        """Center-top: stacked milestone notifications with fade effect."""
        notifications = milestones.get_active_notifications()
        if not notifications:
            return

        center_x = display_size.x / 2.0
        base_y = 60.0

        for i, notif in enumerate(notifications):
            alpha = milestones.get_notification_alpha(notif)
            y_pos = base_y + i * 80.0

            imgui.set_next_window_pos(imgui.ImVec2(center_x - 200, y_pos))
            imgui.set_next_window_bg_alpha(0.8 * alpha)

            # Unique window ID per notification to prevent imgui ID conflicts
            imgui.begin(f"Milestone##{notif.milestone.name}", None, HUD_FLAGS)

            imgui.push_style_color(
                imgui.Col_.text,
                imgui.ImVec4(1.0, 0.85, 0.4, alpha),
            )
            imgui.set_window_font_scale(1.3)
            imgui.text(notif.milestone.name)
            imgui.set_window_font_scale(1.0)
            imgui.pop_style_color()

            imgui.push_style_color(
                imgui.Col_.text,
                imgui.ImVec4(0.9, 0.9, 0.9, alpha),
            )
            imgui.push_text_wrap_pos(380.0)
            imgui.text_wrapped(notif.milestone.description)
            imgui.pop_text_wrap_pos()
            imgui.pop_style_color()

            imgui.end()

    def _render_timeline_bar(self, state, sim, eras, display_size) -> None:
        """Bottom: era timeline bar drawn via imgui foreground draw list.

        Each era gets a colored segment proportional to its screen_seconds.
        A white vertical line marks the current playback position.
        Era name labels are drawn on segments wide enough (>40px).
        """
        draw_list = imgui.get_foreground_draw_list()

        bar_height = 30.0
        bar_y = display_size.y - 40.0
        bar_x_start = 20.0
        bar_x_end = display_size.x - 20.0
        bar_width = bar_x_end - bar_x_start

        total_screen = sum(e.screen_seconds for e in eras)
        if total_screen <= 0:
            return

        # Draw era segments
        cumulative = 0.0
        for i, era in enumerate(eras):
            x0 = bar_x_start + (cumulative / total_screen) * bar_width
            x1 = bar_x_start + ((cumulative + era.screen_seconds) / total_screen) * bar_width
            y0 = bar_y
            y1 = bar_y + bar_height

            r, g, b, a = ERA_COLORS[i] if i < len(ERA_COLORS) else (0.5, 0.5, 0.5, 0.8)
            color = imgui.get_color_u32(imgui.ImVec4(r, g, b, a))
            draw_list.add_rect_filled(imgui.ImVec2(x0, y0), imgui.ImVec2(x1, y1), color)

            # Draw era name label on segments wide enough
            seg_width = x1 - x0
            if seg_width > 40:
                text_color = imgui.get_color_u32(imgui.ImVec4(0.0, 0.0, 0.0, 0.9))
                # Truncate name if segment is narrow
                label = era.name[:int(seg_width / 7)] if seg_width < len(era.name) * 7 else era.name
                draw_list.add_text(imgui.ImVec2(x0 + 3, y0 + 8), text_color, label)

            cumulative += era.screen_seconds

        # Draw progress indicator (white vertical line)
        total_duration = sim.timeline.total_duration()
        progress = sim.screen_time / total_duration if total_duration > 0 else 0.0
        indicator_x = bar_x_start + progress * bar_width
        indicator_color = imgui.get_color_u32(imgui.ImVec4(1.0, 1.0, 1.0, 1.0))
        draw_list.add_line(
            imgui.ImVec2(indicator_x, bar_y - 4),
            imgui.ImVec2(indicator_x, bar_y + bar_height + 4),
            indicator_color,
            2.0,
        )

    def _render_controls_hint(self, camera_auto, display_size) -> None:
        """Bottom-right corner: keyboard controls hint."""
        imgui.set_next_window_pos(imgui.ImVec2(display_size.x - 280, display_size.y - 70))
        imgui.set_next_window_bg_alpha(0.4)
        imgui.begin("Controls", None, HUD_FLAGS)

        cam_mode = "Auto" if camera_auto else "Free"
        imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(0.7, 0.7, 0.7, 1.0))
        imgui.text(f"H: HUD | C: Cam [{cam_mode}] | F12: Screenshot")
        imgui.text("Space: Pause | +/-: Speed | F11: Fullscreen")
        imgui.pop_style_color()

        imgui.end()
