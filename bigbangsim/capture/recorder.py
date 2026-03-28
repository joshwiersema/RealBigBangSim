"""Frame-locked video recorder via FFmpeg subprocess pipe (CAPT-02, CAPT-03).

Reads raw RGB framebuffer data from ModernGL, flips vertically, and pipes to
FFmpeg stdin for H.264 encoding. During recording, the simulation should use
frame_time_override instead of wall-clock frame_time to ensure output quality
is independent of GPU speed.
"""
from __future__ import annotations

import shutil
import subprocess


class VideoRecorder:
    """Frame-locked video recorder using FFmpeg subprocess pipe.

    Usage:
        recorder = VideoRecorder(width, height, fps=60)
        recorder.start()
        # In render loop:
        recorder.write_frame(ctx.fbo)
        # When done:
        recorder.stop()
    """

    def __init__(
        self,
        width: int,
        height: int,
        fps: int = 60,
        output_path: str = "recording.mp4",
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.output_path = output_path
        self._process: subprocess.Popen | None = None
        self._recording = False

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def frame_time_override(self) -> float | None:
        """Fixed frame duration for frame-locked capture (CAPT-03).

        Returns 1/fps when recording, None when not. The app's on_render
        should use this value instead of wall-clock frame_time.
        """
        if self._recording:
            return 1.0 / self.fps
        return None

    @staticmethod
    def is_available() -> bool:
        """Check if FFmpeg is installed and accessible in PATH."""
        return shutil.which("ffmpeg") is not None

    def start(self) -> None:
        """Start recording by launching FFmpeg subprocess.

        Raises:
            RuntimeError: If FFmpeg is not found in PATH.
        """
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise RuntimeError(
                "FFmpeg not found in PATH. Install via: winget install FFmpeg"
            )

        cmd = [
            ffmpeg_path,
            '-y',                                    # Overwrite output
            '-f', 'rawvideo',                        # Input format
            '-vcodec', 'rawvideo',                   # Input codec
            '-s', f'{self.width}x{self.height}',     # Frame size
            '-pix_fmt', 'rgb24',                     # 3 bytes per pixel
            '-r', str(self.fps),                     # Input frame rate
            '-i', 'pipe:0',                          # Read from stdin
            '-an',                                   # No audio
            '-vcodec', 'libx264',                    # H.264 output
            '-pix_fmt', 'yuv420p',                   # Compatible output format
            '-preset', 'medium',                     # Speed/quality tradeoff
            '-crf', '18',                            # Near-lossless quality
            self.output_path,
        ]
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._recording = True

    def write_frame(self, fbo) -> None:
        """Read framebuffer and pipe vertically-flipped RGB data to FFmpeg.

        OpenGL framebuffers have origin at bottom-left; video files expect
        top-left. This method reads raw bytes, reverses row order, and writes
        to FFmpeg's stdin pipe.

        Args:
            fbo: moderngl.Framebuffer to read (typically ctx.fbo).
        """
        if not self._recording or self._process is None:
            return

        data = fbo.read(components=3, alignment=1)
        row_size = self.width * 3
        rows = [data[i:i + row_size] for i in range(0, len(data), row_size)]
        flipped = b''.join(reversed(rows))
        try:
            self._process.stdin.write(flipped)
        except BrokenPipeError:
            self.stop()

    def stop(self) -> None:
        """Stop recording, close pipe, and wait for FFmpeg to finish."""
        if self._process is not None and self._process.stdin:
            try:
                self._process.stdin.close()
            except Exception:
                pass
            self._process.wait()
        self._recording = False
        self._process = None
