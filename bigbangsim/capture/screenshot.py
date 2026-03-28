"""Screenshot capture via Pillow (CAPT-01).

Reads the default framebuffer after all rendering (including HUD) and
saves a vertically-flipped PNG to the screenshots/ directory with a
timestamped filename.
"""
from __future__ import annotations

import os
from datetime import datetime

from PIL import Image


def take_screenshot(
    fbo,
    width: int,
    height: int,
    output_dir: str = "screenshots",
) -> str:
    """Capture framebuffer contents to a PNG file.

    Reads RGB data from the given framebuffer, flips vertically (OpenGL
    origin is bottom-left, image origin is top-left), and saves as PNG.

    Args:
        fbo: moderngl.Framebuffer to read from (typically ctx.fbo after
             compositing and HUD rendering).
        width: Framebuffer width in pixels.
        height: Framebuffer height in pixels.
        output_dir: Directory to save screenshots into. Created if missing.

    Returns:
        Absolute path to the saved PNG file.
    """
    os.makedirs(output_dir, exist_ok=True)
    data = fbo.read(components=3, alignment=1)
    img = Image.frombytes("RGB", (width, height), data)
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"bigbangsim_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    return os.path.abspath(filepath)
