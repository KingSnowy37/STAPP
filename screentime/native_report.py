import ctypes
import logging
from ctypes import wintypes

from .reporting import format_minutes, get_all_days, get_today_stats, get_top_apps_today
from .settings import is_live_timer_enabled, set_live_timer_enabled

WINDOW_CLASS_NAME = "ScreenTimeReportWindow"
WINDOW_TITLE = "Screen Time Tracker - Report"
REFRESH_BUTTON_ID = 1001
MINIMIZE_TO_TRAY_BUTTON_ID = 1002
CLOSE_BUTTON_ID = 1003
LIVE_TIMER_BUTTON_ID = 1004

WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_SIZE = 0x0005
WM_SYSCOMMAND = 0x0112
WM_SETFONT = 0x0030
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_BORDER = 0x00800000
WS_VSCROLL = 0x00200000
WS_EX_CLIENTEDGE = 0x00000200
WS_CAPTION = 0x00C00000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_THICKFRAME = 0x00040000
ES_MULTILINE = 0x0004
ES_AUTOVSCROLL = 0x0040
ES_READONLY = 0x0800
BS_GROUPBOX = 0x0007
BS_AUTOCHECKBOX = 0x0003
SC_MINIMIZE = 0xF020
BM_GETCHECK = 0x00F0
BM_SETCHECK = 0x00F1
BST_CHECKED = 0x0001
SW_SHOW = 5
SW_RESTORE = 9
COLOR_WINDOW = 5
IDC_ARROW = 32512
DEFAULT_GUI_FONT = 17
CW_USEDEFAULT = -2147483648

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


def _format_daily_totals() -> str:
    rows = get_all_days()
    if not rows:
        return "No tracking data yet.\r\n\r\nKeep the tracker running to collect activity."

    lines = ["DATE                 TRACKED            ACTIVE", ""]
    lines.extend(
        f"{day_key:<20} {format_minutes(tracked_minutes):<18} {format_minutes(active_minutes)}"
        for day_key, tracked_minutes, active_minutes in rows
    )
    return "\r\n".join(lines)


def _format_top_apps() -> str:
    apps = get_top_apps_today()
    if not apps:
        return "No active app samples yet."

    lines = ["APPLICATION                              TIME", ""]
    lines.extend(
        f"{app_name[:38]:<40} {format_minutes(active_minutes)}"
        for app_name, active_minutes in apps
    )
    return "\r\n".join(lines)


def launch_report_window() -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    existing_window = user32.FindWindowW(WINDOW_CLASS_NAME, None)
    if existing_window:
        user32.ShowWindow(existing_window, SW_RESTORE)
        user32.SetForegroundWindow(existing_window)
        return

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
    user32.LoadCursorW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    user32.LoadCursorW.restype = wintypes.HANDLE
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    user32.RegisterClassW.restype = wintypes.ATOM
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = LRESULT
    user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
    user32.SetWindowTextW.restype = wintypes.BOOL
    user32.MoveWindow.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.BOOL,
    ]
    user32.MoveWindow.restype = wintypes.BOOL
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetClientRect.restype = wintypes.BOOL
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.restype = wintypes.BOOL
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.PostQuitMessage.restype = None
    user32.UpdateWindow.argtypes = [wintypes.HWND]
    user32.UpdateWindow.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.GetMessageW.restype = wintypes.BOOL
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.TranslateMessage.restype = wintypes.BOOL
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = LRESULT
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HANDLE
    gdi32 = ctypes.windll.gdi32
    gdi32.GetStockObject.argtypes = [ctypes.c_int]
    gdi32.GetStockObject.restype = wintypes.HANDLE
    instance = kernel32.GetModuleHandleW(None)
    default_font = gdi32.GetStockObject(DEFAULT_GUI_FONT)
    controls: dict[str, int] = {}

    def layout(client_width: int, client_height: int) -> None:
        if "today_group" not in controls:
            return

        margin = 24
        inner_margin = 24
        section_gap = 14
        content_width = max(320, client_width - (margin * 2))
        inner_width = max(272, content_width - (inner_margin * 2))
        today_height = 108
        apps_height = 146
        footer_height = 54

        today_y = margin
        apps_y = today_y + today_height + section_gap
        history_y = apps_y + apps_height + section_gap
        history_height = max(120, client_height - history_y - footer_height)
        footer_y = client_height - 42

        user32.MoveWindow(
            controls["today_group"], margin, today_y, content_width, today_height, True
        )
        user32.MoveWindow(
            controls["today"], margin + inner_margin, today_y + 32, inner_width, 22, True
        )
        user32.MoveWindow(
            controls["tracked"], margin + inner_margin, today_y + 58, inner_width, 22, True
        )
        user32.MoveWindow(
            controls["idle"], margin + inner_margin, today_y + 84, inner_width, 22, True
        )

        user32.MoveWindow(
            controls["apps_group"], margin, apps_y, content_width, apps_height, True
        )
        user32.MoveWindow(
            controls["apps"],
            margin + inner_margin,
            apps_y + 28,
            inner_width,
            apps_height - 52,
            True,
        )

        user32.MoveWindow(
            controls["history_group"],
            margin,
            history_y,
            content_width,
            history_height,
            True,
        )
        user32.MoveWindow(
            controls["history"],
            margin + inner_margin,
            history_y + 28,
            inner_width,
            max(68, history_height - 52),
            True,
        )

        user32.MoveWindow(controls["live_timer"], margin, footer_y, 160, 30, True)
        right = client_width - margin
        user32.MoveWindow(controls["close"], right - 64, footer_y, 64, 30, True)
        right -= 74
        user32.MoveWindow(controls["minimize"], right - 116, footer_y, 116, 30, True)
        right -= 126
        user32.MoveWindow(controls["refresh"], right - 94, footer_y, 94, 30, True)

    def refresh() -> None:
        today = get_today_stats()
        user32.SetWindowTextW(
            controls["today"],
            f"Today active: {format_minutes(today['active_minutes'])}",
        )
        user32.SetWindowTextW(
            controls["tracked"],
            f"Tracked today: {format_minutes(today['tracked_minutes'])}",
        )
        user32.SetWindowTextW(
            controls["idle"],
            f"Average idle time: {today['avg_idle_seconds']} seconds",
        )
        user32.SetWindowTextW(controls["apps"], _format_top_apps())
        user32.SetWindowTextW(controls["history"], _format_daily_totals())

    @WNDPROC
    def window_proc(hwnd, message, w_param, l_param):
        try:
            if message == WM_COMMAND:
                command_id = w_param & 0xFFFF
                if command_id == REFRESH_BUTTON_ID:
                    refresh()
                    return 0
                if command_id == LIVE_TIMER_BUTTON_ID:
                    is_checked = (
                        user32.SendMessageW(controls["live_timer"], BM_GETCHECK, 0, 0)
                        == BST_CHECKED
                    )
                    set_live_timer_enabled(is_checked)
                    return 0
                if command_id in {MINIMIZE_TO_TRAY_BUTTON_ID, CLOSE_BUTTON_ID}:
                    user32.DestroyWindow(hwnd)
                    return 0
            if message == WM_SIZE:
                layout(l_param & 0xFFFF, (l_param >> 16) & 0xFFFF)
                return 0
            if message == WM_SYSCOMMAND and (w_param & 0xFFF0) == SC_MINIMIZE:
                # The tray tracker remains running and can reopen this report.
                user32.DestroyWindow(hwnd)
                return 0
            if message == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except Exception as exc:
            logging.exception("Report window command failed: %s", exc)
        return user32.DefWindowProcW(hwnd, message, w_param, l_param)

    window_class = WNDCLASSW()
    window_class.lpfnWndProc = window_proc
    window_class.hInstance = instance
    window_class.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
    window_class.hbrBackground = COLOR_WINDOW + 1
    window_class.lpszClassName = WINDOW_CLASS_NAME
    if not user32.RegisterClassW(ctypes.byref(window_class)):
        raise ctypes.WinError()

    window_style = (
        WS_CAPTION
        | WS_SYSMENU
        | WS_MINIMIZEBOX
        | WS_MAXIMIZEBOX
        | WS_THICKFRAME
    )
    hwnd = user32.CreateWindowExW(
        0,
        WINDOW_CLASS_NAME,
        WINDOW_TITLE,
        window_style,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        640,
        590,
        None,
        None,
        instance,
        None,
    )

    if not hwnd:
        raise ctypes.WinError()

    def create_control(class_name, text, style, x, y, width, height, control_id=0, ex_style=0):
        control = user32.CreateWindowExW(
            ex_style,
            class_name,
            text,
            style,
            x,
            y,
            width,
            height,
            hwnd,
            ctypes.c_void_p(control_id),
            instance,
            None,
        )
        if not control:
            raise ctypes.WinError()
        user32.SendMessageW(control, WM_SETFONT, default_font, True)
        return control

    controls["today_group"] = create_control(
        "BUTTON", "Today", WS_CHILD | WS_VISIBLE | BS_GROUPBOX, 24, 24, 576, 108
    )
    controls["today"] = create_control("STATIC", "", WS_CHILD | WS_VISIBLE, 48, 56, 500, 22)
    controls["tracked"] = create_control("STATIC", "", WS_CHILD | WS_VISIBLE, 48, 82, 500, 22)
    controls["idle"] = create_control("STATIC", "", WS_CHILD | WS_VISIBLE, 48, 108, 500, 22)

    controls["apps_group"] = create_control(
        "BUTTON",
        "Most Used Applications",
        WS_CHILD | WS_VISIBLE | BS_GROUPBOX,
        24,
        146,
        576,
        146,
    )
    controls["apps"] = create_control(
        "EDIT",
        "",
        WS_CHILD | WS_VISIBLE | WS_BORDER | ES_MULTILINE | ES_READONLY,
        48,
        174,
        528,
        94,
        ex_style=WS_EX_CLIENTEDGE,
    )

    controls["history_group"] = create_control(
        "BUTTON", "Daily History", WS_CHILD | WS_VISIBLE | BS_GROUPBOX, 24, 306, 576, 202
    )
    controls["history"] = create_control(
        "EDIT",
        "",
        WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL | ES_READONLY,
        48,
        334,
        528,
        150,
        ex_style=WS_EX_CLIENTEDGE,
    )
    controls["refresh"] = create_control(
        "BUTTON", "Refresh", WS_CHILD | WS_VISIBLE, 282, 526, 94, 30, REFRESH_BUTTON_ID
    )
    controls["live_timer"] = create_control(
        "BUTTON",
        "Show live timer",
        WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
        24,
        526,
        160,
        30,
        LIVE_TIMER_BUTTON_ID,
    )
    if is_live_timer_enabled():
        user32.SendMessageW(controls["live_timer"], BM_SETCHECK, BST_CHECKED, 0)
    controls["minimize"] = create_control(
        "BUTTON",
        "Minimize to tray",
        WS_CHILD | WS_VISIBLE,
        386,
        526,
        116,
        30,
        MINIMIZE_TO_TRAY_BUTTON_ID,
    )
    controls["close"] = create_control(
        "BUTTON", "Close", WS_CHILD | WS_VISIBLE, 512, 526, 64, 30, CLOSE_BUTTON_ID
    )

    client_rect = wintypes.RECT()
    if user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        layout(client_rect.right - client_rect.left, client_rect.bottom - client_rect.top)
    refresh()
    user32.ShowWindow(hwnd, SW_SHOW)
    user32.UpdateWindow(hwnd)

    message = wintypes.MSG()
    while True:
        result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
        if result == -1:
            raise ctypes.WinError()
        if result == 0:
            break
        user32.TranslateMessage(ctypes.byref(message))
        user32.DispatchMessageW(ctypes.byref(message))
