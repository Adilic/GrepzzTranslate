import ctypes
import logging
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal
from PySide6.QtWidgets import QApplication

log = logging.getLogger(__name__)


def parse_hotkey(value: str) -> tuple[int, int]:
    if not isinstance(value, str):
        raise ValueError("快捷键必须是字符串")
    parts = value.lower().replace(" ", "").split("+")
    modifiers = {"alt": 0x1, "ctrl": 0x2, "shift": 0x4, "win": 0x8}
    if len(parts) < 2 or any(p not in modifiers for p in parts[:-1]) or len(set(parts)) != len(parts):
        raise ValueError("快捷键格式示例：alt+q、ctrl+shift+q")
    key = parts[-1]
    if len(key) == 1 and key.isascii() and key.isalnum():
        vk = ord(key.upper())
    elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x70 + int(key[1:]) - 1
    else:
        raise ValueError("快捷键请使用字母、数字或 F1–F24")
    return sum(modifiers[p] for p in parts[:-1]) | 0x4000, vk


class _NativeFilter(QAbstractNativeEventFilter):
    def __init__(self, owner: "HotkeyManager") -> None:
        super().__init__()
        self.owner = owner

    def nativeEventFilter(self, event_type: bytes, message: int) -> tuple[bool, int]:
        if bytes(event_type) in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == self.owner.hotkey_id:
                log.info("Capture hotkey triggered")
                self.owner.triggered.emit()
                return True, 0
        return False, 0


class HotkeyManager(QObject):
    triggered = Signal()

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.hotkey_id = 0x4754
        self.registered = False
        self.value = ""
        self.filter = _NativeFilter(self)
        app.installNativeEventFilter(self.filter)

    def register(self, value: str) -> None:
        if sys.platform != "win32":
            raise RuntimeError("全局快捷键需要 Windows 10/11")
        flags, key = parse_hotkey(value)
        old = self.value if self.registered else ""
        self.unregister()
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        if not user32.RegisterHotKey(None, self.hotkey_id, flags, key):
            error = ctypes.get_last_error()
            if old:
                old_flags, old_key = parse_hotkey(old)
                self.registered = bool(user32.RegisterHotKey(None, self.hotkey_id, old_flags, old_key))
            log.error("Hotkey registration failed: %s (%s)", value, error)
            raise RuntimeError(f"无法注册 {value}，可能已被其他程序占用（Windows {error}）。")
        self.registered = True
        self.value = value
        log.info("Hotkey registered: %s", value)

    def unregister(self) -> None:
        if self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, self.hotkey_id)
            self.registered = False
