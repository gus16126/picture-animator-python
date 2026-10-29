import unittest

from app import ARROW_TIP, Animator


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


if __name__ == "__main__":
    unittest.main()
