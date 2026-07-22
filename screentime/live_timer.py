import ctypes
import logging
import os
import threading
import time
from ctypes import wintypes
from datetime import date

from .activity import get_idle_seconds
from .reporting import get_today_stats
from .settings import is_live_timer_enabled

WINDOW_CLASS_NAME = "ScreenTimeLiveTimer"
WINDOW_TITLE = "Screen Time Timer"

WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_NCHITTEST = 0x0084
WM_PAINT = 0x000F
HTCAPTION = 2

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST = wintypes.HWND(-1)
LWA_COLORKEY = 0x00000001
TRANSPARENT = 1
DT_CENTER = 0x00000001
DT_VCENTER = 0x00000004
DT_SINGLELINE = 0x00000020
PM_REMOVE = 0x0001
SPI_GETWORKAREA = 0x0030
SM_CXSCREEN = 0

ACTIVE_IDLE_THRESHOLD_SECONDS = 5 * 60
TIMER_WIDTH = 172
TIMER_HEIGHT = 48
TIMER_MARGIN = 16
TIMER_TRANSPARENT_COLOR = 0x00010001
TIMER_TEXT_COLOR = 0x00F2F2F2

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HANDLE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HANDLE),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


def format_timer(total_seconds: int) -> str:
    hours, remainder = divmod(max(0, total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def consume_elapsed_seconds(remainder: float, elapsed: float) -> tuple[int, float]:
    """Convert fractional loop time into whole display seconds without losing time."""
    total = max(0.0, remainder) + max(0.0, elapsed)
    completed_seconds = int(total + 1e-9)
    return completed_seconds, max(0.0, total - completed_seconds)


class ActiveTimeClock:
    """Keep the live total independent from the optional overlay window."""

    def __init__(self, initial_seconds: int = 0) -> None:
        self.total_seconds = max(0, int(initial_seconds))
        self.remainder = 0.0

    def advance(self, elapsed: float, is_active: bool) -> int:
        if not is_active:
            return self.total_seconds

        completed_seconds, self.remainder = consume_elapsed_seconds(
            self.remainder,
            elapsed,
        )
        self.total_seconds += completed_seconds
        return self.total_seconds

    def reconcile(self, database_seconds: int) -> int:
        self.total_seconds = max(self.total_seconds, max(0, int(database_seconds)))
        return self.total_seconds


class LiveTimerOverlay:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.hwnd: int | None = None
        self._window_proc = None
        self.font_handle = None
        self.background_brush = None
        self.display_text = "00:00:00"

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="live-timer", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.hwnd:
            user32 = ctypes.windll.user32
            user32.PostMessageW.argtypes = [
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            ]
            user32.PostMessageW.restype = wintypes.BOOL
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.thread = None
        self.hwnd = None

    def _run(self) -> None:
        try:
            self._run_window()
        except Exception as exc:
            logging.exception("Live timer failed: %s", exc)
        finally:
            self.hwnd = None

    def _run_window(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        gdi32 = ctypes.windll.gdi32
        self._configure_win32(user32, kernel32, gdi32)
        instance = kernel32.GetModuleHandleW(None)
        class_name = f"{WINDOW_CLASS_NAME}_{os.getpid()}_{time.monotonic_ns()}"

        @WNDPROC
        def window_proc(hwnd, message, w_param, l_param):
            try:
                if message == WM_NCHITTEST:
                    return HTCAPTION
                if message == WM_PAINT:
                    self._paint_timer(user32, gdi32, hwnd)
                    return 0
                if message == WM_CLOSE:
                    user32.DestroyWindow(hwnd)
                    return 0
                if message == WM_DESTROY:
                    self.stop_event.set()
                    return 0
            except Exception as exc:
                logging.exception("Live timer window command failed: %s", exc)
            return user32.DefWindowProcW(hwnd, message, w_param, l_param)

        self._window_proc = window_proc
        self.background_brush = gdi32.CreateSolidBrush(TIMER_TRANSPARENT_COLOR)
        if not self.background_brush:
            raise ctypes.WinError()
        self.font_handle = gdi32.CreateFontW(
            24, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 0, 0, "Segoe UI"
        )
        if not self.font_handle:
            raise ctypes.WinError()

        window_class = WNDCLASSW()
        window_class.lpfnWndProc = window_proc
        window_class.hInstance = instance
        window_class.hbrBackground = self.background_brush
        window_class.lpszClassName = class_name
        class_registered = bool(user32.RegisterClassW(ctypes.byref(window_class)))
        if not class_registered:
            raise ctypes.WinError()

        try:
            x, y = self._top_right_position(user32)
            hwnd = user32.CreateWindowExW(
                WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST,
                class_name,
                WINDOW_TITLE,
                WS_POPUP,
                x,
                y,
                TIMER_WIDTH,
                TIMER_HEIGHT,
                None,
                None,
                instance,
                None,
            )
            if not hwnd:
                raise ctypes.WinError()

            self.hwnd = hwnd
            if not user32.SetLayeredWindowAttributes(
                hwnd,
                TIMER_TRANSPARENT_COLOR,
                255,
                LWA_COLORKEY,
            ):
                raise ctypes.WinError()
            if not user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                x,
                y,
                TIMER_WIDTH,
                TIMER_HEIGHT,
                SWP_SHOWWINDOW | SWP_NOACTIVATE,
            ):
                raise ctypes.WinError()

            message = wintypes.MSG()
            last_topmost_refresh = time.monotonic()

            while not self.stop_event.is_set():
                while user32.PeekMessageW(
                    ctypes.byref(message), None, 0, 0, PM_REMOVE
                ):
                    user32.TranslateMessage(ctypes.byref(message))
                    user32.DispatchMessageW(ctypes.byref(message))

                now = time.monotonic()
                if now - last_topmost_refresh >= 1:
                    if not user32.SetWindowPos(
                        hwnd,
                        HWND_TOPMOST,
                        0,
                        0,
                        0,
                        0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
                    ):
                        logging.warning("Could not refresh live timer topmost status")
                    last_topmost_refresh = now

                user32.InvalidateRect(hwnd, None, True)
                self.stop_event.wait(0.25)
        finally:
            if self.hwnd and user32.IsWindow(self.hwnd):
                user32.DestroyWindow(self.hwnd)
            self.hwnd = None
            if class_registered:
                user32.UnregisterClassW(class_name, instance)
            if self.font_handle:
                gdi32.DeleteObject(self.font_handle)
                self.font_handle = None
            if self.background_brush:
                gdi32.DeleteObject(self.background_brush)
                self.background_brush = None

    @staticmethod
    def _configure_win32(user32, kernel32, gdi32) -> None:
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HANDLE,
            wintypes.HANDLE,
            wintypes.LPVOID,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.DefWindowProcW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.DefWindowProcW.restype = LRESULT
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.RegisterClassW.restype = wintypes.ATOM
        user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE]
        user32.UnregisterClassW.restype = wintypes.BOOL
        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.SetLayeredWindowAttributes.argtypes = [
            wintypes.HWND,
            wintypes.DWORD,
            wintypes.BYTE,
            wintypes.DWORD,
        ]
        user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
        user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
        user32.BeginPaint.restype = wintypes.HANDLE
        user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
        user32.EndPaint.restype = wintypes.BOOL
        user32.DrawTextW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCWSTR,
            ctypes.c_int,
            ctypes.POINTER(wintypes.RECT),
            wintypes.UINT,
        ]
        user32.DrawTextW.restype = ctypes.c_int
        user32.FillRect.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.RECT),
            wintypes.HANDLE,
        ]
        user32.FillRect.restype = ctypes.c_int
        user32.InvalidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL]
        user32.InvalidateRect.restype = wintypes.BOOL
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.DestroyWindow.restype = wintypes.BOOL
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        user32.PeekMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.PeekMessageW.restype = wintypes.BOOL
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.TranslateMessage.restype = wintypes.BOOL
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.restype = LRESULT
        user32.SystemParametersInfoW.argtypes = [
            wintypes.UINT,
            wintypes.UINT,
            ctypes.c_void_p,
            wintypes.UINT,
        ]
        user32.SystemParametersInfoW.restype = wintypes.BOOL
        user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        user32.GetSystemMetrics.restype = ctypes.c_int
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HANDLE
        gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
        gdi32.CreateSolidBrush.restype = wintypes.HANDLE
        gdi32.CreateFontW.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPCWSTR,
        ]
        gdi32.CreateFontW.restype = wintypes.HANDLE
        gdi32.SelectObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        gdi32.SelectObject.restype = wintypes.HANDLE
        gdi32.SetBkMode.argtypes = [wintypes.HANDLE, ctypes.c_int]
        gdi32.SetBkMode.restype = ctypes.c_int
        gdi32.SetTextColor.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        gdi32.SetTextColor.restype = wintypes.DWORD
        gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
        gdi32.DeleteObject.restype = wintypes.BOOL

    @staticmethod
    def _top_right_position(user32) -> tuple[int, int]:
        work_area = wintypes.RECT()
        if user32.SystemParametersInfoW(
            SPI_GETWORKAREA, 0, ctypes.byref(work_area), 0
        ):
            return (
                max(work_area.left + TIMER_MARGIN, work_area.right - TIMER_WIDTH - TIMER_MARGIN),
                work_area.top + TIMER_MARGIN,
            )
        return (
            max(TIMER_MARGIN, user32.GetSystemMetrics(SM_CXSCREEN) - TIMER_WIDTH - TIMER_MARGIN),
            TIMER_MARGIN,
        )

    def _paint_timer(self, user32, gdi32, hwnd) -> None:
        paint = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(paint))
        if not hdc:
            return
        try:
            bounds = wintypes.RECT(0, 0, TIMER_WIDTH, TIMER_HEIGHT)
            user32.FillRect(hdc, ctypes.byref(bounds), self.background_brush)
            if self.font_handle:
                gdi32.SelectObject(hdc, self.font_handle)
            gdi32.SetBkMode(hdc, TRANSPARENT)

            gdi32.SetTextColor(hdc, TIMER_TEXT_COLOR)
            user32.DrawTextW(
                hdc,
                self.display_text,
                -1,
                ctypes.byref(bounds),
                DT_CENTER | DT_VCENTER | DT_SINGLELINE,
            )
        finally:
            user32.EndPaint(hwnd, ctypes.byref(paint))


class LiveTimerController:
    def __init__(self) -> None:
        self.overlay = LiveTimerOverlay()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name="live-timer-controller",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.overlay.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.thread = None

    def _run(self) -> None:
        current_day = date.today()
        database_seconds = int(get_today_stats()["active_minutes"] * 60)
        clock = ActiveTimeClock(database_seconds)
        self.overlay.display_text = format_timer(clock.total_seconds)
        last_tick = time.monotonic()
        last_database_refresh = last_tick
        last_setting_check = 0.0

        while not self.stop_event.is_set():
            now = time.monotonic()
            elapsed = max(0.0, now - last_tick)
            last_tick = now

            today = date.today()
            if today != current_day:
                current_day = today
                database_seconds = int(get_today_stats()["active_minutes"] * 60)
                clock = ActiveTimeClock(database_seconds)
                last_database_refresh = now

            try:
                is_active = get_idle_seconds() < ACTIVE_IDLE_THRESHOLD_SECONDS
            except Exception as exc:
                logging.exception("Live timer idle check failed: %s", exc)
                is_active = False

            clock.advance(elapsed, is_active)

            if now - last_database_refresh >= 30:
                database_seconds = int(get_today_stats()["active_minutes"] * 60)
                clock.reconcile(database_seconds)
                last_database_refresh = now

            self.overlay.display_text = format_timer(clock.total_seconds)

            if now - last_setting_check >= 1:
                if is_live_timer_enabled():
                    self.overlay.start()
                else:
                    self.overlay.stop()
                last_setting_check = now

            self.stop_event.wait(0.25)
