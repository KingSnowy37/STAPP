import ctypes
import re
from dataclasses import dataclass
from ctypes import wintypes
from pathlib import Path


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


@dataclass(frozen=True)
class FocusedApp:
    process_id: int
    app_name: str
    executable_path: str | None
    window_title: str


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
KNOWN_BROWSERS = {
    "brave.exe",
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "opera.exe",
    "vivaldi.exe",
}
BROWSER_DISPLAY_NAMES = {
    "Brave",
    "Firefox",
    "Google Chrome",
    "Microsoft Edge",
    "Opera",
    "Vivaldi",
}
APP_NAME_ALIASES = {
    "applicationframehost": "Windows App",
    "brave": "Brave",
    "chatgpt": "ChatGPT",
    "chrome": "Google Chrome",
    "code": "Visual Studio Code",
    "discord": "Discord",
    "explorer": "File Explorer",
    "firefox": "Firefox",
    "msedge": "Microsoft Edge",
    "notepad": "Notepad",
    "py": "Python",
    "python": "Python",
    "pythonw": "Python",
    "robloxplayerbeta": "Roblox",
    "steam": "Steam",
    "windows-terminal": "Windows Terminal",
}


def get_idle_seconds() -> int:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
    user32.GetLastInputInfo.restype = wintypes.BOOL
    kernel32.GetTickCount.argtypes = []
    kernel32.GetTickCount.restype = wintypes.DWORD

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        raise ctypes.WinError()

    elapsed_ms = (kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF
    return max(0, int(elapsed_ms / 1000))


def get_focused_app() -> FocusedApp | None:
    """Return privacy-limited metadata for the current foreground window."""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    if not process_id.value:
        return None

    executable_path = _get_process_path(kernel32, process_id.value)
    process_name = Path(executable_path).name if executable_path else f"Process {process_id.value}"
    app_name = normalize_app_name(process_name)
    window_title = _get_window_title(user32, hwnd)

    return FocusedApp(
        process_id=process_id.value,
        app_name=app_name,
        executable_path=executable_path,
        window_title=sanitize_window_title(app_name, window_title),
    )


def sanitize_window_title(app_name: str, window_title: str) -> str:
    """Avoid retaining browser page names while keeping other app titles short."""
    if app_name.lower() in KNOWN_BROWSERS or app_name in BROWSER_DISPLAY_NAMES:
        return ""
    return window_title.strip()[:160]


def normalize_app_name(process_name: str) -> str:
    """Turn executable names into stable, readable labels for reports."""
    filename = Path(process_name).name
    stem = filename[:-4] if filename.lower().endswith(".exe") else filename
    normalized_key = stem.lower()
    if re.fullmatch(r"pythonw?(?:\d+(?:\.\d+)*)?", normalized_key):
        return "Python"
    if normalized_key in APP_NAME_ALIASES:
        return APP_NAME_ALIASES[normalized_key]

    if normalized_key.startswith("process "):
        return process_name

    spaced_name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stem)
    spaced_name = re.sub(r"[_-]+", " ", spaced_name).strip()
    return spaced_name.title() or "Unknown App"


def _get_window_title(user32, hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""

    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value.strip()


def _get_process_path(kernel32, process_id: int) -> str | None:
    process_handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
    if not process_handle:
        return None

    try:
        buffer = ctypes.create_unicode_buffer(32768)
        path_length = wintypes.DWORD(len(buffer))
        if kernel32.QueryFullProcessImageNameW(
            process_handle,
            0,
            buffer,
            ctypes.byref(path_length),
        ):
            return buffer.value
    finally:
        kernel32.CloseHandle(process_handle)

    return None
