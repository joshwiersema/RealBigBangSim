"""Tests for fullscreen toggle and window state persistence (RNDR-05)."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_save_window_state_writes_json(tmp_path):
    """save_window_state writes JSON with position, size, fullscreen keys."""
    from bigbangsim.config import save_window_state

    wnd = MagicMock()
    wnd.position = (100, 200)
    wnd.size = (1280, 720)
    wnd.fullscreen = False

    state_path = tmp_path / "window_state.json"
    save_window_state(wnd, path=state_path)

    data = json.loads(state_path.read_text())
    assert data["position"] == [100, 200]
    assert data["size"] == [1280, 720]
    assert data["fullscreen"] is False


def test_load_window_state_returns_dict(tmp_path):
    """load_window_state returns dict when file exists with valid JSON."""
    from bigbangsim.config import load_window_state

    state_path = tmp_path / "window_state.json"
    state_path.write_text(json.dumps({
        "position": [100, 200],
        "size": [1280, 720],
        "fullscreen": False,
    }))

    result = load_window_state(path=state_path)
    assert isinstance(result, dict)
    assert result["position"] == [100, 200]
    assert result["size"] == [1280, 720]
    assert result["fullscreen"] is False


def test_load_window_state_missing_file(tmp_path):
    """load_window_state returns None when file does not exist."""
    from bigbangsim.config import load_window_state

    result = load_window_state(path=tmp_path / "nonexistent.json")
    assert result is None


def test_load_window_state_malformed_json(tmp_path):
    """load_window_state returns None when JSON is malformed."""
    from bigbangsim.config import load_window_state

    state_path = tmp_path / "window_state.json"
    state_path.write_text("{{invalid json content")

    result = load_window_state(path=state_path)
    assert result is None


def test_validate_window_position_clamps(tmp_path):
    """load_window_state clamps unreasonable coordinates."""
    from bigbangsim.config import load_window_state

    # Test negative coordinates get clamped to 0
    state_path = tmp_path / "negative.json"
    state_path.write_text(json.dumps({
        "position": [-500, -100],
        "size": [1280, 720],
        "fullscreen": False,
    }))
    result = load_window_state(path=state_path)
    assert result["position"] == [0, 0]

    # Test overly large coordinates get clamped
    state_path2 = tmp_path / "large.json"
    state_path2.write_text(json.dumps({
        "position": [5000, 3500],
        "size": [1280, 720],
        "fullscreen": False,
    }))
    result2 = load_window_state(path=state_path2)
    assert result2["position"] == [4000, 3000]
