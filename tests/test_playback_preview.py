import unittest
from unittest.mock import Mock

from app import Animator


class PlaybackPreviewTests(unittest.TestCase):
    def test_playback_redraws_the_timeline_on_every_tick(self):
        animator = Animator.__new__(Animator)
        animator.playing = True
        animator.play_started = __import__("time").perf_counter()
        animator.play_origin = 0
        animator.total_duration = Mock(return_value=5)
        animator.timeline = Mock()
        animator.timeline_text = Mock()
        animator.format_time = Mock(return_value="0:00")
        animator.render_timeline = Mock()
        animator.after = Mock()

        Animator.play_tick(animator)

        self.assertTrue(animator.playing)
        animator.render_timeline.assert_called_once()
        animator.after.assert_called_once_with(30, animator.play_tick)


if __name__ == "__main__":
    unittest.main()
