import sqlite3
from contextlib import contextmanager

from .paths import DATA_DIR, DB_PATH


def ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_time TEXT NOT NULL,
                date_key TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                idle_seconds INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_samples_date_time
            ON activity_samples(date_key, sample_time)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS focus_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_time TEXT NOT NULL,
                date_key TEXT NOT NULL,
                process_id INTEGER NOT NULL,
                app_name TEXT NOT NULL,
                executable_path TEXT,
                window_title TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_focus_samples_date_app
            ON focus_samples(date_key, app_name)
            """
        )
        conn.commit()


@contextmanager
def get_connection():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
