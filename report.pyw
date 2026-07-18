import ctypes
import logging

from screentime.native_report import launch_report_window
from screentime.paths import DATA_DIR, LOG_PATH


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        launch_report_window()
    except Exception as exc:
        logging.exception("Report window failed to start: %s", exc)
        ctypes.windll.user32.MessageBoxW(
            None,
            "The report could not open. Details were saved to tracker.log.",
            "Screen Time Tracker",
            0x10,
        )
