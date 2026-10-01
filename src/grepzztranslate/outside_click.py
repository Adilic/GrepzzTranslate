import ctypes
import logging
import sys
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

log = logging.getLogger(__name__)


class MouseEvent(ctypes.Structure):
    _fields_ = [("point", wintypes.POINT), ("mouse_data", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD), ("extra", ctypes.c_size_t)]


class OutsideClickMonitor(QObject):
    clicked = Signal(int)
    BUTTON_DOWN = {0x0201, 0x0204, 0x0207, 0x020B}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.handle = None
        self.window_id = 0
        self.generation = 0
        self.user32 = None
        self.callback = None
        if sys.platform == "win32":
            self.user32 = ctypes.WinDLL("user32", use_last_error=True)
            procedure = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t)
            self.callback = procedure(self._on_mouse)
            self.user32.SetWindowsHookExW.argtypes = [ctypes.c_int, procedure, wintypes.HINSTANCE, wintypes.DWORD]
            self.user32.SetWindowsHookExW.restype = wintypes.HANDLE
            self.user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_size_t, ctypes.c_ssize_t]
            self.user32.CallNextHookEx.restype = ctypes.c_ssize_t
            self.user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
            self.user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]

    def start(self, window_id: int) -> None:
        self.stop()
        self.window_id = window_id
        if self.user32:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
            kernel32.GetModuleHandleW.restype = wintypes.HMODULE
            self.handle = self.user32.SetWindowsHookExW(14, self.callback, kernel32.GetModuleHandleW(None), 0)
            if not self.handle:
                log.warning("Outside click hook unavailable (%s); using focus fallback", ctypes.get_last_error())

    def stop(self) -> None:
        if self.handle:
            self.user32.UnhookWindowsHookEx(self.handle)
        self.handle = None
        self.generation += 1

    def _on_mouse(self, code: int, message: int, address: int) -> int:
        # クリックは必ず次のアプリへ渡し、閉じる処理だけを Qt に通知する。
        try:
            if code >= 0 and self.handle and message in self.BUTTON_DOWN:
                event = MouseEvent.from_address(address)
                rect = wintypes.RECT()
                if self.user32.GetWindowRect(self.window_id, ctypes.byref(rect)):
                    if not (rect.left <= event.point.x < rect.right and rect.top <= event.point.y < rect.bottom):
                        self.clicked.emit(self.generation)
        except Exception:
            log.exception("Outside click monitor failed")
        return self.user32.CallNextHookEx(self.handle, code, message, address)
