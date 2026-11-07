import base64
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import app
from app import Animator


class _Stream:
    def __init__(self):
        self.closed = False
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def close(self):
        self.closed = True


class _Process:
    def __init__(self):
        self.stdin = _Stream()
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()

    def wait(self):
        return 0

    def poll(self):
        return 0

    def terminate(self):
        raise AssertionError("successful export must not terminate FFmpeg")


class ExportStreamTests(unittest.TestCase):
    def setUp(self):
        self.app = Animator()
        self.app.withdraw()
        self.addCleanup(self.app.destroy)
        image_data = io.BytesIO()
        Image.new("RGB", (4, 2), "red").save(image_data, format="PNG")
        self.app.frames = [{
            "name": "Frame",
            "image": base64.b64encode(image_data.getvalue()).decode(),
            "labels": [],
            "duration": 1.0,
            "transition": "Cut",
            "transition_duration": .3,
        }]
        self.app.current = 0
        self.app.fps.set(1)

    def test_export_sends_each_rendered_frame_directly_to_ffmpeg(self):
        process = _Process()
        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "animation.mp4")
            def start(command, **kwargs):
                Path(command[-1]).write_bytes(b"video")
                return process
            with patch.object(app.subprocess, "Popen", side_effect=start) as popen:
                self.app._export_video("ffmpeg", target, 1, self.app.frames, None)

        command = popen.call_args.args[0]
        self.assertIn("rawvideo", command)
        self.assertIn("rgb24", command)
        self.assertIn("veryfast", command)
        self.assertIn("17", command)
        self.assertNotIn("concat", command)
        self.assertEqual(process.stdin.writes, [b"\xff\x00\x00" * 8])
        self.assertEqual(self.app._export_result, (target, ""))

    def test_export_uses_the_first_frame_as_its_stable_canvas_size(self):
        process = _Process()
        portrait_data = io.BytesIO()
        Image.new("RGB", (2, 4), "blue").save(portrait_data, format="PNG")
        self.app.frames.append({
            "name": "Portrait", "image": base64.b64encode(portrait_data.getvalue()).decode(),
            "labels": [], "duration": 1.0, "transition": "Cut", "transition_duration": .3,
        })
        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "animation.mp4")
            def start(command, **kwargs):
                Path(command[-1]).write_bytes(b"video")
                return process
            with patch.object(app.subprocess, "Popen", side_effect=start) as popen:
                self.app._export_video("ffmpeg", target, 1, self.app.frames, None)

        command = popen.call_args.args[0]
        self.assertEqual(command[command.index("-s:v") + 1], "4x2")


if __name__ == "__main__":
    unittest.main()
