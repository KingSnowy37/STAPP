import ctypes
import logging
import threading
import time
import webbrowser
from datetime import datetime

import pystray
from PIL import Image, ImageDraw

from .activity import get_idle_seconds
from .db import ensure_db, get_connection
from .paths import DATA_DIR, LOG_PATH
from .report import open_report
from .reporting import format_minutes, get_today_stats
from .updates import check_for_update, get_available_update, is_check_due

SAMPLE_INTERVAL_SECONDS = 60
ACTIVE_IDLE_THRESHOLD_SECONDS = 5 * 60
TRACKER_MUTEX_NAME = "Local\\ScreenTimeTracker"
ERROR_ALREADY_EXISTS = 183


def configure_logging() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def record_sample(now: datetime, idle_seconds: int, is_active: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO activity_samples (sample_time, date_key, is_active, idle_seconds)
            VALUES (?, ?, ?, ?)
            """,
            (
                now.isoformat(timespec="seconds"),
                now.date().isoformat(),
                1 if is_active else 0,
                idle_seconds,
            ),
        )
        conn.commit()


def sleep_until_next_minute() -> None:
    current_time = time.time()
    remainder = current_time % SAMPLE_INTERVAL_SECONDS
    delay = SAMPLE_INTERVAL_SECONDS - remainder
    time.sleep(max(1, delay))


def _create_tray_icon_image() -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=14, fill=(184, 92, 56, 255))
    draw.ellipse((18, 18, 46, 46), fill=(255, 248, 241, 255))
    draw.line((32, 32, 32, 22), fill=(184, 92, 56, 255), width=4)
    draw.line((32, 32, 40, 38), fill=(184, 92, 56, 255), width=4)
    return image


class TrackerService:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self) -> None:
        configure_logging()
        ensure_db()
        logging.info("Tracker service started")
        self.thread.start()

    def stop(self) -> None:
        logging.info("Tracker service stopping")
        self.stop_event.set()
        self.thread.join(timeout=5)

    def _run_loop(self) -> None:
        while not self.stop_event.is_set():
            now = datetime.now()
            try:
                idle_seconds = get_idle_seconds()
                is_active = idle_seconds < ACTIVE_IDLE_THRESHOLD_SECONDS
                record_sample(now, idle_seconds, is_active)
                logging.info(
                    "Recorded sample active=%s idle_seconds=%s",
                    is_active,
                    idle_seconds,
                )
            except Exception as exc:
                logging.exception("Tracker loop failed: %s", exc)

            if self.stop_event.wait(_seconds_until_next_minute()):
                break


def _seconds_until_next_minute() -> int:
    current_time = time.time()
    remainder = current_time % SAMPLE_INTERVAL_SECONDS
    delay = int(SAMPLE_INTERVAL_SECONDS - remainder)
    return max(1, delay)


def _open_report_from_tray(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    del icon, item
    open_report()


def _today_total_label(item: pystray.MenuItem) -> str:
    del item
    active_minutes = get_today_stats()["active_minutes"]
    return f"Today active: {format_minutes(active_minutes)}"


def _update_label(item: pystray.MenuItem) -> str:
    del item
    update = get_available_update()
    return f"Update available: v{update.version}" if update else "Check for updates"


def _open_update_download(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    del icon, item
    update = get_available_update()
    if update:
        webbrowser.open(update.download_url or update.release_url)


def _has_update(item: pystray.MenuItem) -> bool:
    del item
    return get_available_update() is not None


def _check_for_updates(icon: pystray.Icon, notify_when_current: bool) -> None:
    update = check_for_update()
    icon.update_menu()
    if update:
        icon.notify(
            f"Version {update.version} is ready. Right-click the tray icon to download it.",
            "Screen Time Tracker update",
        )
    elif notify_when_current:
        icon.notify("You are using the latest version.", "Screen Time Tracker")


def _check_for_updates_from_tray(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    del item
    threading.Thread(
        target=_check_for_updates,
        args=(icon, True),
        daemon=True,
    ).start()


def _check_for_updates_on_start(icon: pystray.Icon) -> None:
    if is_check_due():
        _check_for_updates(icon, False)


def _quit_from_tray(service: TrackerService):
    def handler(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        del item
        service.stop()
        icon.stop()

    return handler


def run_tray_app() -> None:
    ctypes.set_last_error(0)
    mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, TRACKER_MUTEX_NAME)
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        return

    service = TrackerService()
    service.start()

    menu = pystray.Menu(
        pystray.MenuItem(_today_total_label, None, enabled=False),
        pystray.MenuItem("Open report", _open_report_from_tray, default=True),
        pystray.MenuItem(_update_label, _check_for_updates_from_tray),
        pystray.MenuItem("Download update", _open_update_download, visible=_has_update),
        pystray.MenuItem("Quit", _quit_from_tray(service)),
    )

    icon = pystray.Icon(
        "screen-time-tracker",
        icon=_create_tray_icon_image(),
        title="Screen Time Tracker",
        menu=menu,
    )

    logging.info("Tray icon starting")
    threading.Thread(target=_check_for_updates_on_start, args=(icon,), daemon=True).start()
    try:
        icon.run()
    finally:
        service.stop()
        ctypes.windll.kernel32.CloseHandle(mutex_handle)


def run_tracker() -> None:
    configure_logging()
    ensure_db()
    logging.info("Tracker started")

    while True:
        now = datetime.now()
        try:
            idle_seconds = get_idle_seconds()
            is_active = idle_seconds < ACTIVE_IDLE_THRESHOLD_SECONDS
            record_sample(now, idle_seconds, is_active)
            logging.info(
                "Recorded sample active=%s idle_seconds=%s",
                is_active,
                idle_seconds,
            )
        except Exception as exc:
            logging.exception("Tracker loop failed: %s", exc)

        sleep_until_next_minute()
