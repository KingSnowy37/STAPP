import sqlite3
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import patch

from screentime.reporting import get_recent_days, get_top_apps_today


class ReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(
            """
            CREATE TABLE activity_samples (
                sample_time TEXT,
                date_key TEXT,
                is_active INTEGER,
                idle_seconds INTEGER
            );
            CREATE TABLE focus_samples (
                sample_time TEXT,
                date_key TEXT,
                process_id INTEGER,
                app_name TEXT,
                executable_path TEXT,
                window_title TEXT
            );
            """
        )

        @contextmanager
        def connection_context():
            yield self.connection

        self.connection_patch = patch(
            "screentime.reporting.get_connection",
            connection_context,
        )
        self.connection_patch.start()

    def tearDown(self) -> None:
        self.connection_patch.stop()
        self.connection.close()

    def test_recent_days_returns_daily_active_minutes(self) -> None:
        today = date.today()
        yesterday = today - timedelta(days=1)
        self.connection.executemany(
            "INSERT INTO activity_samples VALUES (?, ?, ?, ?)",
            [
                (f"{today}T10:00:00", str(today), 1, 0),
                (f"{today}T10:01:00", str(today), 0, 400),
                (f"{yesterday}T10:00:00", str(yesterday), 1, 0),
            ],
        )

        self.assertEqual(
            get_recent_days(2),
            [(str(today), 1), (str(yesterday), 1)],
        )

    def test_top_apps_combines_equivalent_names_before_limiting(self) -> None:
        today = str(date.today())
        self.connection.executemany(
            "INSERT INTO focus_samples VALUES (?, ?, ?, ?, ?, ?)",
            [
                (f"{today}T10:00:00", today, 1, "chrome.exe", None, ""),
                (f"{today}T10:01:00", today, 1, "Google Chrome", None, ""),
                (f"{today}T10:02:00", today, 2, "notepad.exe", None, "Notes"),
            ],
        )

        self.assertEqual(
            get_top_apps_today(limit=1),
            [("Google Chrome", 2)],
        )


if __name__ == "__main__":
    unittest.main()
