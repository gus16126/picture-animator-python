import unittest
from unittest.mock import Mock

from app import Animator


class _Status:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class PlaybackPreviewTests(unittest.TestCase):
    def test_playback_clock_waits_for_background_preview_frames(self):
        animator = Animator.__new__(Animator)
        animator.playing = True
        animator.play_started = None
        animator._play_ready = False
        animator._play_frames = []
        animator.status = _Status()
        animator.after = Mock()

        Animator.play_tick(animator)

        self.assertTrue(animator.playing)
        self.assertIsNone(animator.play_started)
        self.assertEqual(animator.status.value, "Preparing preview...")
        animator.after.assert_called_once_with(30, animator.play_tick)


if __name__ == "__main__":
    unittest.main()
