from datetime import date, timedelta
from collections import defaultdict

from .activity import normalize_app_name
from .db import get_connection


def get_today_stats() -> dict:
    today_key = date.today().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_samples,
                COALESCE(SUM(is_active), 0) AS active_samples,
                COALESCE(AVG(idle_seconds), 0) AS avg_idle_seconds
            FROM activity_samples
            WHERE date_key = ?
            """,
            (today_key,),
        ).fetchone()

    total_samples, active_samples, avg_idle_seconds = row
    return {
        "date": today_key,
        "tracked_minutes": int(total_samples or 0),
        "active_minutes": int(active_samples or 0),
        "avg_idle_seconds": int(avg_idle_seconds or 0),
    }


def get_recent_days(days: int = 7) -> list[tuple[str, int]]:
    start_key = (date.today() - timedelta(days=days - 1)).isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date_key, COALESCE(SUM(is_active), 0) AS active_minutes
            FROM activity_samples
            WHERE date_key >= ?
            GROUP BY date_key
            ORDER BY date_key DESC
            """,
            (start_key,),
        ).fetchall()
    return [(row[0], int(row[1])) for row in rows]


def get_all_days() -> list[tuple[str, int, int]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                date_key,
                COUNT(*) AS tracked_minutes,
                COALESCE(SUM(is_active), 0) AS active_minutes
            FROM activity_samples
            GROUP BY date_key
            ORDER BY date_key DESC
            """
        ).fetchall()
    return [(row[0], int(row[1]), int(row[2])) for row in rows]


def get_top_apps_today(limit: int = 5) -> list[tuple[str, int]]:
    today_key = date.today().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT app_name, COUNT(*) AS active_minutes
            FROM focus_samples
            WHERE date_key = ?
            GROUP BY app_name
            ORDER BY active_minutes DESC, app_name ASC
            """,
            (today_key,),
        ).fetchall()
    normalized_totals: dict[str, int] = defaultdict(int)
    for app_name, active_minutes in rows:
        normalized_totals[normalize_app_name(app_name)] += int(active_minutes)

    return sorted(normalized_totals.items(), key=lambda item: (-item[1], item[0]))[:limit]


def format_minutes(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"
