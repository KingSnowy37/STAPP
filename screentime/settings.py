import json

from .paths import DATA_DIR, SETTINGS_PATH


def is_live_timer_enabled() -> bool:
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return bool(settings.get("live_timer_enabled", False))
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def set_live_timer_enabled(enabled: bool) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps({"live_timer_enabled": enabled}, indent=2),
        encoding="utf-8",
    )
