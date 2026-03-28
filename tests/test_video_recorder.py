"""Tests for VideoRecorder (CAPT-02, CAPT-03)."""
import pytest
from unittest.mock import MagicMock, patch, call
from bigbangsim.capture.recorder import VideoRecorder


class TestVideoRecorderInit:
    def test_stores_dimensions(self):
        rec = VideoRecorder(1280, 720, fps=60, output_path="test.mp4")
        assert rec.width == 1280
        assert rec.height == 720
        assert rec.fps == 60
        assert rec.output_path == "test.mp4"

    def test_defaults(self):
        rec = VideoRecorder(800, 600)
        assert rec.fps == 60
        assert rec.output_path == "recording.mp4"
        assert rec.recording is False


class TestFFmpegDetection:
    @patch("bigbangsim.capture.recorder.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_available_when_found(self, mock_which):
        assert VideoRecorder.is_available() is True
        mock_which.assert_called_once_with("ffmpeg")

    @patch("bigbangsim.capture.recorder.shutil.which", return_value=None)
    def test_unavailable_when_not_found(self, mock_which):
        assert VideoRecorder.is_available() is False


class TestStartStop:
    @patch("bigbangsim.capture.recorder.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("bigbangsim.capture.recorder.subprocess.Popen")
    def test_start_launches_ffmpeg(self, mock_popen, mock_which):
        rec = VideoRecorder(1280, 720, fps=60, output_path="out.mp4")
        rec.start()
        assert rec.recording is True
        # Verify ffmpeg command includes key arguments
        args = mock_popen.call_args
        cmd = args[0][0]  # First positional arg is the command list
        assert "-f" in cmd and "rawvideo" in cmd
        assert "-pix_fmt" in cmd and "rgb24" in cmd
        assert "-s" in cmd and "1280x720" in cmd
        assert "-r" in cmd and "60" in cmd
        assert "-vcodec" in cmd and "libx264" in cmd
        assert "-crf" in cmd and "18" in cmd
        assert "out.mp4" in cmd

    @patch("bigbangsim.capture.recorder.shutil.which", return_value=None)
    def test_start_raises_when_ffmpeg_missing(self, mock_which):
        rec = VideoRecorder(1280, 720)
        with pytest.raises(RuntimeError, match="FFmpeg not found"):
            rec.start()

    @patch("bigbangsim.capture.recorder.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("bigbangsim.capture.recorder.subprocess.Popen")
    def test_stop_closes_stdin_and_waits(self, mock_popen, mock_which):
        proc = MagicMock()
        mock_popen.return_value = proc
        rec = VideoRecorder(1280, 720)
        rec.start()
        rec.stop()
        proc.stdin.close.assert_called_once()
        proc.wait.assert_called_once()
        assert rec.recording is False

    def test_stop_safe_when_not_recording(self):
        rec = VideoRecorder(1280, 720)
        rec.stop()  # Should not raise


class TestWriteFrame:
    @patch("bigbangsim.capture.recorder.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("bigbangsim.capture.recorder.subprocess.Popen")
    def test_write_frame_reads_fbo_and_writes(self, mock_popen, mock_which):
        proc = MagicMock()
        mock_popen.return_value = proc

        rec = VideoRecorder(2, 2, fps=30)  # Tiny 2x2 for easy verification
        rec.start()

        fbo = MagicMock()
        # 2x2 RGB: row0=[R,G,B,R,G,B] row1=[R,G,B,R,G,B]
        # Bottom row first (OpenGL), top row first (video)
        row0 = b'\x01\x02\x03\x04\x05\x06'  # bottom row
        row1 = b'\x07\x08\x09\x0a\x0b\x0c'  # top row
        fbo.read.return_value = row0 + row1
        rec.write_frame(fbo)

        fbo.read.assert_called_once_with(components=3, alignment=1)
        # Should be flipped: top row first
        expected = row1 + row0
        proc.stdin.write.assert_called_once_with(expected)

    def test_write_frame_noop_when_not_recording(self):
        rec = VideoRecorder(1280, 720)
        fbo = MagicMock()
        rec.write_frame(fbo)  # Should not raise, should not call fbo.read
        fbo.read.assert_not_called()


class TestFrameLocking:
    def test_frame_time_override_when_recording(self):
        rec = VideoRecorder(1280, 720, fps=60)
        assert rec.frame_time_override is None
        # Simulate recording state
        rec._recording = True
        assert rec.frame_time_override == pytest.approx(1.0 / 60.0)

    def test_frame_time_override_30fps(self):
        rec = VideoRecorder(1280, 720, fps=30)
        rec._recording = True
        assert rec.frame_time_override == pytest.approx(1.0 / 30.0)
