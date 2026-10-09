"""Read a foreground selection without showing UI or reusing stale clipboard text."""
import ctypes
from ctypes import wintypes
import time

from PySide6.QtCore import QMimeData, QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication


class _Keyboard(ctypes.Structure):
    _fields_ = [("vk", wintypes.WORD), ("scan", wintypes.WORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("extra", ctypes.c_size_t)]


class _Mouse(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG),
                ("data", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("extra", ctypes.c_size_t)]


class _Payload(ctypes.Union):
    _fields_ = [("keyboard", _Keyboard), ("mouse", _Mouse)]


class _Input(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("payload", _Payload)]


class WindowsSelectionBackend:
    def __init__(self):
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        self.api.GetForegroundWindow.restype = wintypes.HWND
        self.api.GetClipboardOwner.restype = wintypes.HWND
        self.api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.api.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.api.GetClipboardSequenceNumber.restype = wintypes.DWORD
        self.api.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.api.GetAsyncKeyState.restype = ctypes.c_short
        self.api.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(_Input), ctypes.c_int]
        self.api.SendInput.restype = wintypes.UINT

    def foreground(self):
        return self.api.GetForegroundWindow()

    def sequence(self):
        return self.api.GetClipboardSequenceNumber()

    def owns_copy(self, target):
        owner = self.api.GetClipboardOwner()
        if not owner:
            return False
        owner_pid, target_pid = wintypes.DWORD(), wintypes.DWORD()
        self.api.GetWindowThreadProcessId(owner, ctypes.byref(owner_pid))
        self.api.GetWindowThreadProcessId(target, ctypes.byref(target_pid))
        return owner_pid.value != 0 and owner_pid.value == target_pid.value

    def keys_down(self):
        # Never synthesize Ctrl+C while the user's Alt/Shift/etc. is still held.
        return any(self.api.GetAsyncKeyState(key) & 0x8000
                   for key in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0x31))

    def copy(self):
        events = (_Input * 4)()
        for event, (vk, flags) in zip(events, [(0x11, 0), (0x43, 0), (0x43, 2), (0x11, 2)]):
            event.type = 1
            event.payload.keyboard = _Keyboard(vk, 0, flags, 0, 0)
        sent = self.api.SendInput(4, events, ctypes.sizeof(_Input))
        if sent != 4:
            # Release only keys that our partial sequence may have pressed.
            if sent:
                releases = (_Input * 2)(events[2], events[3])
                self.api.SendInput(2, releases, ctypes.sizeof(_Input))
            raise RuntimeError("无法读取选中文字。请确认阅读器与本工具以相同权限运行。")


class SelectionReader(QObject):
    selected = Signal(str)
    failed = Signal(str)

    def __init__(self, parent=None, *, backend=None, clipboard=None, clock=time.monotonic):
        super().__init__(parent)
        self.backend = backend or WindowsSelectionBackend()
        self.clipboard = clipboard if clipboard is not None else QApplication.clipboard()
        self.clock = clock
        self.active = False
        self.saved = None
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.poll)

    def start(self):
        if self.active:
            return
        self.target = self.backend.foreground()
        if not self.target:
            self.failed.emit("请先在阅读器中选中文字，再按 Alt+1。")
            return
        self.active = True
        self.phase = "release"
        self.deadline = self.clock() + 2
        self.timer.start()

    def cancel(self):
        self.timer.stop()
        self.active = False
        self.saved = None

    def fail(self, message):
        self.cancel()
        self.failed.emit(message)

    def poll(self):
        if not self.active:
            return
        try:
            if self.backend.foreground() != self.target:
                self.fail("窗口已切换，请在阅读器中重新选择文字并按 Alt+1。")
                return
            if self.clock() >= self.deadline:
                self.fail("没有读到选中文字。请选中可复制的文字后按 Alt+1；扫描图片可用截图翻译。")
                return
            if self.phase == "release":
                if self.backend.keys_down():
                    return
                # Clone, since Qt's original QMimeData becomes invalid after copying.
                self.saved = QMimeData()
                original = self.clipboard.mimeData()
                if original is not None:
                    for fmt in original.formats():
                        self.saved.setData(fmt, original.data(fmt))
                self.sequence = self.backend.sequence()
                self.backend.copy()
                self.phase = "copy"
                self.deadline = self.clock() + 1.5
                return
            sequence = self.backend.sequence()
            if sequence == self.sequence:
                return  # No new copy: never translate the pre-existing clipboard.
            if not self.backend.owns_copy(self.target):
                self.fail("剪贴板被其他程序更新，请重新选择文字并按 Alt+1。")
                return
            text = self.clipboard.text().strip()
            # Delayed rendering can update the sequence during text retrieval.
            if sequence != self.backend.sequence():
                return
            saved = self.saved
            self.cancel()
            if saved is not None and self.backend.sequence() == sequence:
                self.clipboard.setMimeData(saved)
            if text:
                self.selected.emit(text)
            else:
                self.failed.emit("选区没有可复制的文字，请改用截图翻译。")
        except Exception as exc:
            self.fail(str(exc))
