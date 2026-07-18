import unittest

from screentime.live_timer import consume_elapsed_seconds, format_timer


class LiveTimerTests(unittest.TestCase):
    def test_format_timer_uses_hh_mm_ss(self) -> None:
        self.assertEqual(format_timer(0), "00:00:00")
        self.assertEqual(format_timer(3723), "01:02:03")

    def test_fractional_updates_accumulate_into_seconds(self) -> None:
        remainder = 0.0
        seconds = 0
        for _ in range(4):
            completed, remainder = consume_elapsed_seconds(remainder, 0.25)
            seconds += completed

        self.assertEqual(seconds, 1)
        self.assertEqual(remainder, 0.0)


if __name__ == "__main__":
    unittest.main()
