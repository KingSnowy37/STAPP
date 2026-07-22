import unittest

from screentime.live_timer import (
    ActiveTimeClock,
    SWP_NOACTIVATE,
    SWP_NOMOVE,
    SWP_NOSIZE,
    WS_EX_NOACTIVATE,
    WS_EX_TOPMOST,
    consume_elapsed_seconds,
    format_timer,
)


class LiveTimerTests(unittest.TestCase):
    def test_overlay_style_is_topmost_without_activation(self) -> None:
        self.assertTrue(WS_EX_TOPMOST)
        self.assertTrue(WS_EX_NOACTIVATE)
        self.assertEqual(SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE, 0x0013)

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

    def test_clock_keeps_counting_while_overlay_is_hidden(self) -> None:
        clock = ActiveTimeClock(initial_seconds=60)

        clock.advance(2.4, is_active=True)
        clock.advance(5.0, is_active=False)
        clock.advance(0.6, is_active=True)

        self.assertEqual(clock.total_seconds, 63)

    def test_database_reconciliation_never_resets_live_seconds(self) -> None:
        clock = ActiveTimeClock(initial_seconds=60)
        clock.advance(12.0, is_active=True)

        self.assertEqual(clock.reconcile(60), 72)
        self.assertEqual(clock.reconcile(120), 120)


if __name__ == "__main__":
    unittest.main()
