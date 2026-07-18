import sys
import os
from pathlib import Path


def _resolve_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_ROOT = _resolve_app_root()
if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", APP_ROOT)) / "Screen Time Tracker"
else:
    DATA_DIR = APP_ROOT / "data"
DB_PATH = DATA_DIR / "screentime.db"
LOG_PATH = DATA_DIR / "tracker.log"
REPORT_PATH = DATA_DIR / "report.html"
UPDATE_STATE_PATH = DATA_DIR / "update_state.json"
