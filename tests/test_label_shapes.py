import unittest

from PIL import Image

from app import ANIMATIONS, ARROW_TIP, Animator


class LabelShapeTests(unittest.TestCase):
    def test_arrow_backgrounds_have_a_real_arrowhead(self):
        points = Animator.shape(None, "Right arrow", 100, 50, 200, 80)

        self.assertEqual(len(points), 10)
        self.assertEqual(points[4:6], [200, 50])
        self.assertEqual(points[2], 200 - ARROW_TIP)
        self.assertEqual(points[6], 200 - ARROW_TIP)

    def test_arrow_labels_reserve_space_for_the_tip(self):
        animator = Animator.__new__(Animator)
        animator._text_measure = lambda label: (100, 30)

        box_width, box_height = animator._label_box({"shape": "Right arrow"})
        normal_width, normal_height = animator._label_box({"shape": "Box"})
        up_width, up_height = animator._label_box({"shape": "Up arrow"})

        self.assertEqual(box_width, normal_width + ARROW_TIP)
        self.assertEqual(box_height, normal_height)
        self.assertEqual(up_width, normal_width)
        self.assertEqual(up_height, normal_height + ARROW_TIP)

    def test_attention_animations_move_or_scale_labels_during_playback(self):
        animator = Animator.__new__(Animator)
        animator.frame_image = lambda frame: Image.new("RGB", (400, 200), "white")
        animator.frame_duration = lambda frame: 2.0
        calls = []
        animator.draw_export_label = lambda *args: calls.append(args)

        for animation in ("Pulse", "Bounce", "Wiggle"):
            with self.subTest(animation=animation):
                calls.clear()
                Animator.render_frame_image(animator, {"labels": [{"animation": animation, "delay": 0, "anim_duration": .5}]}, .25)
                _, _, progress, _, offset_x, offset_y, extra_rotation = calls[0]
                if animation == "Pulse":
                    self.assertGreater(progress, 1)
                elif animation == "Bounce":
                    self.assertLess(offset_y, 0)
                else:
                    self.assertNotEqual(offset_x, 0)
                    self.assertNotEqual(extra_rotation, 0)

    def test_attention_animations_are_available_to_the_label_editor(self):
        self.assertTrue({"Pulse", "Bounce", "Wiggle"}.issubset(ANIMATIONS))


if __name__ == "__main__":
    unittest.main()
