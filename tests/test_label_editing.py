import base64
import io
import unittest
from unittest.mock import Mock, patch

from PIL import Image

import app
from app import Animator


class LabelEditingTests(unittest.TestCase):
    def setUp(self):
        self.app = Animator()
        self.app.draw = Mock()
        self.app.withdraw()
        self.addCleanup(self.app.destroy)
        image_data = io.BytesIO()
        Image.new("RGB", (80, 60), "red").save(image_data, format="PNG")
        label = {
            "id": "arrow-label", "text": "Original", "shape": "Right arrow",
            "font": "Arial Bold", "x": .5, "y": .5, "size": 28,
            "color": "#FFFFFF", "bg": "#5B46C8", "outline": "",
            "opacity": 100, "rotation": 0, "animation": "None",
            "anim_duration": .5, "delay": 0,
        }
        self.app.frames = [{
            "name": "Frame", "image": base64.b64encode(image_data.getvalue()).decode(),
            "labels": [label], "duration": 1.0, "transition": "Cut",
            "transition_duration": .3,
        }]
        self.app.current = 0
        self.app.selected = label["id"]
        self.app.load_fields()

    def test_editing_text_preserves_the_selected_label_shape(self):
        self.assertEqual(self.app.fields["shape"].get(), "Right arrow")
        self.assertEqual(self.app.fields["font"].get(), "Arial Bold")
        self.assertEqual(self.app.fields["animation"].get(), "None")
        text = self.app.fields["text"]
        text.delete("1.0", "end")
        text.insert("1.0", "Changed text")

        self.app.apply_field("text")

        label = self.app.label()
        self.assertEqual(label["text"], "Changed text")
        self.assertEqual(label["shape"], "Right arrow")

    def test_default_preset_application_preserves_shapes(self):
        self.app.presets = {"box-style": {"shape": "Box", "color": "#000000"}}
        self.app.preset_choice.set("box-style")

        self.app.apply_preset_to_matching()
        self.assertEqual(self.app.label()["shape"], "Right arrow")
        self.assertEqual(self.app.label()["color"], "#000000")

        self.app.apply_preset_to_matching(include_shape=True)
        self.assertEqual(self.app.label()["shape"], "Box")

    def test_color_picker_updates_only_the_requested_color(self):
        with patch.object(app.colorchooser, "askcolor", return_value=((18, 52, 86), "#123456")):
            self.app.pick_color("color")

        self.assertEqual(self.app.label()["color"], "#123456")
        self.assertEqual(self.app.label()["shape"], "Right arrow")

    def test_opening_a_project_normalizes_blank_label_values(self):
        animator = Animator.__new__(Animator)
        label = {"id": "label", "text": "", "shape": "", "font": "", "x": "", "y": None,
                 "size": "", "color": "", "bg": None, "outline": "bad", "opacity": "",
                 "rotation": "", "animation": "", "anim_duration": "", "delay": ""}

        Animator._normalize_label(animator, label)

        self.assertEqual(label["shape"], "Box")
        self.assertEqual(label["font"], "Arial Bold")
        self.assertEqual(label["color"], "#FFFFFF")
        self.assertEqual(label["bg"], "#5B46C8")
        self.assertEqual(label["rotation"], 0)
        self.assertEqual(label["animation"], "None")


if __name__ == "__main__":
    unittest.main()
