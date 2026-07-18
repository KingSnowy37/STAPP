import subprocess
import sys
import ctypes
import logging
from ctypes import wintypes
from pathlib import Path

from .paths import APP_ROOT


def _show_existing_report() -> bool:
    user32 = ctypes.windll.user32
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    hwnd = user32.FindWindowW("ScreenTimeReportWindow", None)
    if not hwnd:
        return False
    user32.ShowWindow(hwnd, 9)
    user32.SetForegroundWindow(hwnd)
    return True


def open_report() -> bool:
    """Launch the separately packaged native report window without blocking the tray app."""
    if _show_existing_report():
        return True

    if getattr(sys, "frozen", False):
        report_executable = Path(sys.executable).with_name("ScreenTimeReport.exe")
        if report_executable.exists():
            subprocess.Popen([str(report_executable)], cwd=report_executable.parent)
            return True
        raise FileNotFoundError(f"Report executable not found: {report_executable}")

    report_script = APP_ROOT / "report.pyw"
    if not report_script.exists():
        raise FileNotFoundError(f"Report script not found: {report_script}")
    subprocess.Popen([sys.executable, str(report_script)], cwd=APP_ROOT)
    logging.info("Report window launched")
    return True
