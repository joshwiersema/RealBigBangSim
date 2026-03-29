"""Application configuration constants.

Window, physics timing, speed control defaults, and window state
persistence (RNDR-05).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
PHYSICS_DT = 1.0 / 60.0
TARGET_FPS = 60
MIN_SPEED = 0.125
MAX_SPEED = 32.0
DEFAULT_SPEED = 1.0


# ---------------------------------------------------------------------------
# Window state persistence (RNDR-05)
# ---------------------------------------------------------------------------

def _get_settings_path() -> Path:
    """Get cross-platform settings file path.

    Windows: LOCALAPPDATA/BigBangSim/window_state.json
    Other: ~/.config/BigBangSim/window_state.json
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", str(Path.home()))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    settings_dir = Path(base) / "BigBangSim"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "window_state.json"


def save_window_state(wnd, path: Path | None = None) -> None:
    """Save window position, size, and fullscreen state to JSON.

    Args:
        wnd: The moderngl-window window object (has .position, .size,
             .fullscreen attributes).
        path: Optional explicit path for the JSON file. Uses the
              platform-appropriate settings directory by default.
    """
    state = {
        "position": list(wnd.position),
        "size": list(wnd.size),
        "fullscreen": wnd.fullscreen,
    }
    target = path or _get_settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2))


def load_window_state(path: Path | None = None) -> dict | None:
    """Load saved window state, or None if not found/corrupt.

    If the saved position is outside reasonable screen bounds, clamp it
    to prevent the window from appearing off-screen (Pitfall 5 from
    research -- monitor config change).

    Args:
        path: Optional explicit path for the JSON file. Uses the
              platform-appropriate settings directory by default.

    Returns:
        Dict with "position", "size", "fullscreen" keys, or None if the
        file is missing or contains invalid JSON.
    """
    target = path or _get_settings_path()
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text())
        # Validate and clamp position to reasonable bounds.
        # Y must be >= 40 to keep the title bar visible on screen
        # (Windows title bar is ~30px, plus margin).
        if "position" in data:
            x, y = data["position"]
            data["position"] = [max(0, min(x, 4000)), max(40, min(y, 3000))]
        return data
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
