import unittest
from unittest.mock import patch

from screentime.tracker import _seconds_until_next_minute


class TrackerTimingTests(unittest.TestCase):
    def test_wait_preserves_fractional_time_to_next_minute(self) -> None:
        with patch("screentime.tracker.time.time", return_value=119.75):
            self.assertAlmostEqual(_seconds_until_next_minute(), 0.25)

    def test_wait_is_full_minute_on_exact_boundary(self) -> None:
        with patch("screentime.tracker.time.time", return_value=120.0):
            self.assertEqual(_seconds_until_next_minute(), 60.0)


if __name__ == "__main__":
    unittest.main()
