import base64
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import app
from app import Animator


class _Process:
    def __init__(self):
        self.stdin = None
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

    def test_export_uses_timed_still_images_for_unchanged_frames(self):
        process = _Process()
        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "animation.mp4")
            def start(command, **kwargs):
                Path(command[-1]).write_bytes(b"video")
                return process
            with patch.object(app.subprocess, "Popen", side_effect=start) as popen:
                self.app._export_video("ffmpeg", target, 1, self.app.frames, None)

        command = popen.call_args.args[0]
        self.assertIn("concat", command)
        self.assertIn("cfr", command)
        self.assertIn("-r", command)
        self.assertIn("ultrafast", command)
        self.assertNotIn("rawvideo", command)
        self.assertEqual(self.app._export_result, (target, ""))

    def test_static_frame_is_rendered_once_not_once_per_export_fps_tick(self):
        self.assertEqual(self.app.export_sample_times(0, 10), [0.0])


if __name__ == "__main__":
    unittest.main()
