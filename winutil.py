"""Win32 helpers. Every ctypes signature is declared: undeclared calls assume
32-bit ints and fail silently when a window handle doesn't fit."""

import ctypes
import os
from ctypes import wintypes

HWND_TOPMOST = -1
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010
GWL_EXSTYLE = -20
GWLP_HWNDPARENT = -8          # for a top-level window: its OWNER window
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
ERROR_ALREADY_EXISTS = 183

if os.name == "nt":
    U = ctypes.WinDLL("user32", use_last_error=True)
    K = ctypes.WinDLL("kernel32", use_last_error=True)
    U.SetWindowPos.argtypes = (wintypes.HWND, wintypes.HWND, ctypes.c_int,
                               ctypes.c_int, ctypes.c_int, ctypes.c_int,
                               wintypes.UINT)
    U.SetWindowPos.restype = wintypes.BOOL
    U.GetWindowLongPtrW.argtypes = (wintypes.HWND, ctypes.c_int)
    U.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    U.SetWindowLongPtrW.argtypes = (wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t)
    U.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    U.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
    U.FindWindowW.restype = wintypes.HWND
    U.FindWindowExW.argtypes = (wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR)
    U.FindWindowExW.restype = wintypes.HWND
    U.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
    U.GetWindowRect.restype = wintypes.BOOL
    U.GetForegroundWindow.argtypes = ()
    U.GetForegroundWindow.restype = wintypes.HWND
    U.WindowFromPoint.argtypes = (wintypes.POINT,)
    U.WindowFromPoint.restype = wintypes.HWND
    U.MessageBoxW.argtypes = (wintypes.HWND, wintypes.LPCWSTR,
                              wintypes.LPCWSTR, wintypes.UINT)
    U.MessageBoxW.restype = ctypes.c_int
    K.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    K.CreateMutexW.restype = wintypes.HANDLE
    K.CloseHandle.argtypes = (wintypes.HANDLE,)
    K.CloseHandle.restype = wintypes.BOOL


def pin_topmost(hwnd):
    """Re-assert always-on-top without stealing focus."""
    if os.name != "nt":
        return
    try:
        U.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                       SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
    except (AttributeError, OSError, ValueError):
        pass


def set_ex_style(hwnd, add=0, remove=0):
    if os.name != "nt":
        return
    try:
        style = U.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        U.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, (style | add) & ~remove)
    except (AttributeError, OSError, ValueError):
        pass


def no_activate(hwnd):
    """Clicking this window never takes focus away from your game or editor."""
    set_ex_style(hwnd, add=WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)


def click_through(hwnd, on):
    """On: every click goes straight through the window to what's under it."""
    if on:
        set_ex_style(hwnd, add=WS_EX_TRANSPARENT)
    else:
        set_ex_style(hwnd, remove=WS_EX_TRANSPARENT)


def taskbars():
    """Every taskbar window: the main one and those on other monitors."""
    if os.name != "nt":
        return []
    found = []
    try:
        for name in ("Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
            hwnd = U.FindWindowW(name, None)
            while hwnd:
                found.append(hwnd)
                hwnd = U.FindWindowExW(None, hwnd, name, None)
    except (AttributeError, OSError, ValueError):
        pass
    return found


def window_rect(hwnd):
    """(left, top, right, bottom) in physical screen pixels, or None."""
    if os.name != "nt":
        return None
    try:
        r = wintypes.RECT()
        if U.GetWindowRect(hwnd, ctypes.byref(r)):
            return r.left, r.top, r.right, r.bottom
    except (AttributeError, OSError, ValueError):
        pass
    return None


def taskbar_under(hwnd):
    """The taskbar this window overlaps, or None. Physical pixels on both
    sides, so it is right at any display scaling."""
    mine = window_rect(hwnd)
    if mine is None:
        return None
    for bar in taskbars():
        r = window_rect(bar)
        if r and mine[0] < r[2] and mine[2] > r[0] and mine[1] < r[3] and mine[3] > r[1]:
            return bar
    return None


def set_owner(hwnd, owner):
    """Make `owner` this window's owner (0 = none). Windows always keeps an
    owned window above its owner, so a bar owned by the taskbar stays on top
    of it even right after the taskbar is clicked (the taskbar jumps to the
    front of the always-on-top windows when clicked)."""
    if os.name != "nt":
        return False
    try:
        ctypes.set_last_error(0)
        previous = U.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, int(owner or 0))
        return bool(previous or ctypes.get_last_error() == 0)
    except (AttributeError, OSError, ValueError):
        return False


def owner_of(hwnd):
    if os.name != "nt":
        return 0
    try:
        return int(U.GetWindowLongPtrW(hwnd, GWLP_HWNDPARENT) or 0)
    except (AttributeError, OSError, ValueError):
        return 0


def foreground():
    if os.name != "nt":
        return 0
    try:
        return int(U.GetForegroundWindow() or 0)
    except (AttributeError, OSError, ValueError):
        return 0


def window_at(x, y):
    if os.name != "nt":
        return None
    return U.WindowFromPoint(wintypes.POINT(int(x), int(y)))


_INSTANCE_HANDLE = None


def acquire_single_instance(name="Local\\DesktopPark"):
    """Named mutex so two copies never overwrite each other's save file."""
    global _INSTANCE_HANDLE
    if os.name != "nt":
        return True
    handle = K.CreateMutexW(None, False, name)
    err = ctypes.get_last_error()
    if not handle:
        return True
    if err == ERROR_ALREADY_EXISTS:
        K.CloseHandle(handle)
        return False
    _INSTANCE_HANDLE = handle
    return True


def message_box(text, title):
    if os.name == "nt":
        U.MessageBoxW(None, text, title, 0x40)
