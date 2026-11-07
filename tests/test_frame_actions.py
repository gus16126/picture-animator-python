import base64
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

import app
from app import Animator


class FrameActionsTests(unittest.TestCase):
    def setUp(self):
        self.app = Animator()
        self.app.withdraw()
        self.app.draw = Mock()
        self.addCleanup(self.app.destroy)
        image_data = io.BytesIO()
        Image.new("RGB", (80, 60), "red").save(image_data, format="PNG")
        self.raw_image = image_data.getvalue()
        self.app.frames = [{
            "name": "Front cab", "image": base64.b64encode(self.raw_image).decode(),
            "labels": [], "duration": 1.0, "transition": "Cut", "transition_duration": .3,
        }]
        self.app.current = 0
        self.app.refresh()

    def test_selected_frame_download_includes_its_labels(self):
        self.app.frames[0]["labels"] = [{
            "id": "label", "text": "Label", "shape": "Box", "font": "Arial Bold",
            "x": .5, "y": .5, "size": 16, "color": "#FFFFFF", "bg": "#00FF00",
            "outline": "", "opacity": 100, "rotation": 0, "animation": "None",
            "anim_duration": .5, "delay": 0,
        }]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "frame.png"
            with patch.object(app.filedialog, "asksaveasfilename", return_value=str(output)):
                self.app.save_selected_frame()

            with Image.open(output) as picture:
                self.assertEqual(picture.format, "PNG")
                self.assertEqual(picture.size, (80, 60))
            self.assertNotEqual(output.read_bytes(), self.raw_image)
            self.assertEqual(self.app.status.get(), "Downloaded labelled frame: frame.png")

    def test_rename_uses_the_frame_selected_in_the_list(self):
        self.app.listbox.selection_clear(0, "end")
        self.app.listbox.selection_set(0)
        self.app.rename_frame()
        dialog = next(child for child in self.app.winfo_children() if isinstance(child, app.tk.Toplevel))
        entry = next(child for child in dialog.winfo_children() if child.winfo_class() == "TEntry")
        entry.delete(0, "end")
        entry.insert(0, "Renamed frame")
        button = next(child for child in dialog.winfo_children() if child.winfo_class() == "TButton")
        button.invoke()

        self.assertEqual(self.app.frames[0]["name"], "Renamed frame")
        self.assertEqual(self.app.listbox.get(0), "1. Renamed frame")


if __name__ == "__main__":
    unittest.main()
