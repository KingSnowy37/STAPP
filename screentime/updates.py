import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .paths import DATA_DIR, UPDATE_STATE_PATH
from .version import APP_VERSION

RELEASE_API_URL = "https://api.github.com/repos/KingSnowy37/STAPP/releases/latest"
INSTALLER_ASSET_NAME = "ScreenTimeTracker-Setup.exe"
CHECK_INTERVAL = timedelta(days=1)


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    release_url: str


def _version_key(value: str) -> tuple[int, ...]:
    normalized = value.strip().lstrip("vV")
    parts = normalized.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        raise ValueError(f"Unsupported version format: {value}")
    return tuple(int(part) for part in parts)


def _read_state() -> dict:
    try:
        return json.loads(UPDATE_STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPDATE_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def is_check_due() -> bool:
    last_checked = _read_state().get("last_checked")
    if not last_checked:
        return True

    try:
        checked_at = datetime.fromisoformat(last_checked)
    except ValueError:
        return True

    return datetime.now(timezone.utc) - checked_at >= CHECK_INTERVAL


def get_available_update() -> UpdateInfo | None:
    stored_update = _read_state().get("available_update")
    if not isinstance(stored_update, dict):
        return None

    try:
        update = UpdateInfo(**stored_update)
        return update if _version_key(update.version) > _version_key(APP_VERSION) else None
    except (TypeError, ValueError):
        return None


def check_for_update() -> UpdateInfo | None:
    request = Request(
        RELEASE_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Screen-Time-Tracker",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            release = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        logging.info("Update check failed: %s", exc)
        return None

    release_version = str(release.get("tag_name", ""))
    try:
        is_newer = _version_key(release_version) > _version_key(APP_VERSION)
    except ValueError:
        logging.warning("Ignored release with invalid version tag: %s", release_version)
        return None

    update = None
    if is_newer:
        for asset in release.get("assets", []):
            if asset.get("name") == INSTALLER_ASSET_NAME:
                update = UpdateInfo(
                    version=release_version.lstrip("vV"),
                    download_url=str(asset.get("browser_download_url", "")),
                    release_url=str(release.get("html_url", "")),
                )
                break

    _write_state(
        {
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "available_update": asdict(update) if update else None,
        }
    )
    return update


def download_update(update: UpdateInfo) -> Path:
    """Download the release installer locally; the tray app starts it only after a user click."""
    download_dir = DATA_DIR / "updates"
    download_dir.mkdir(parents=True, exist_ok=True)
    installer_path = download_dir / INSTALLER_ASSET_NAME
    request = Request(update.download_url, headers={"User-Agent": "Screen-Time-Tracker"})

    with urlopen(request, timeout=60) as response:
        installer_path.write_bytes(response.read())

    return installer_path
