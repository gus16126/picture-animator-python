import base64
import copy
import io
import unittest
from unittest.mock import Mock

from PIL import Image

from app import Animator


class DuplicateFrameTests(unittest.TestCase):
    def setUp(self):
        self.app = Animator()
        self.app.draw = Mock()
        self.app.withdraw()
        self.addCleanup(self.app.destroy)
        self.callback_errors = []
        self.app.report_callback_exception = (
            lambda kind, error, traceback: self.callback_errors.append(error)
        )
        image_data = io.BytesIO()
        Image.new("RGB", (80, 60), "red").save(image_data, format="PNG")
        self.encoded_image = base64.b64encode(image_data.getvalue()).decode()
        widgets = list(self.app.winfo_children())
        while widgets:
            widget = widgets.pop()
            if widget.winfo_class() == "TButton" and widget.cget("text") == "Duplicate":
                self.duplicate_button = widget
                break
            widgets.extend(widget.winfo_children())
        else:
            self.fail("Duplicate button is missing")

    def make_frame(self, index):
        return {
            "name": f"Frame {index}",
            "image": self.encoded_image,
            "labels": [{
                "id": f"label-{index}", "text": "Original label", "shape": "Box",
                "font": "Arial Bold", "x": 0.5, "y": 0.5, "size": 12,
                "color": "#FFFFFF", "bg": "#5B46C8", "outline": "",
                "opacity": 100, "rotation": 0, "delay": 0,
            }],
            "duration": 1.25 + index,
            "transition": "Fade",
            "transition_duration": 0.3,
        }

    def test_should_duplicate_selected_frame_in_visible_list(self):
        # Specified oracle: exactly one independent copy after the source,
        # selected and visible, with its timing and labels preserved.
        # Singleton plus first/middle/last selections cover the index boundaries.
        for count, selected in ((1, 0), (3, 0), (3, 1), (3, 2)):
            with self.subTest(count=count, selected=selected):
                self.app.frames = [self.make_frame(i) for i in range(count)]
                before = copy.deepcopy(self.app.frames)
                self.app.current = selected
                self.app.selected = before[selected]["labels"][0]["id"]
                self.callback_errors.clear()
                self.app.draw.reset_mock()

                self.duplicate_button.invoke()

                expected_copy = copy.deepcopy(before[selected])
                expected_copy["name"] += " copy"
                expected = before[:selected + 1] + [expected_copy] + before[selected + 1:]
                self.assertEqual(self.app.frames, expected)
                self.assertEqual(
                    self.app.listbox.size(), count + 1,
                    f"Frame copy must be visible; callback errors: {self.callback_errors!r}",
                )
                self.assertEqual(self.callback_errors, [])
                self.assertEqual(
                    self.app.listbox.get(0, "end"),
                    tuple(f"{i + 1}. {frame['name']}" for i, frame in enumerate(expected)),
                )
                self.assertEqual(self.app.current, selected + 1)
                self.assertEqual(self.app.listbox.curselection(), (selected + 1,))
                self.assertIsNone(self.app.selected)
                self.assertEqual(self.app.status.get(), "Duplicated frame.")
                self.assertEqual(float(self.app.duration.get()), expected_copy["duration"])
                self.assertAlmostEqual(
                    float(self.app.timeline_scale.cget("to")),
                    sum(frame["duration"] for frame in expected),
                )
                self.app.draw.assert_called_once_with()
                self.app.frames[selected + 1]["labels"][0]["text"] = "Edited copy"
                self.assertEqual(self.app.frames[selected], before[selected])

    def test_should_leave_frames_unchanged_without_a_selection(self):
        for frames in ([], [self.make_frame(0)]):
            with self.subTest(frame_count=len(frames)):
                self.app.frames = frames
                before = copy.deepcopy(frames)
                self.app.current = -1

                self.duplicate_button.invoke()

                self.assertEqual(self.app.frames, before)
                self.assertEqual(self.app.current, -1)
                self.assertEqual(self.callback_errors, [])


if __name__ == "__main__":
    unittest.main()
