import ctypes
from ctypes import wintypes

from grepzztranslate.outside_click import MouseEvent, OutsideClickMonitor


class NativeMouseStub:
    def __init__(self):
        self.forwarded = []

    def GetWindowRect(self, window_id, rect):
        rect._obj.left, rect._obj.top, rect._obj.right, rect._obj.bottom = -200, 20, 200, 300
        return True

    def CallNextHookEx(self, handle, code, message, address):
        self.forwarded.append(message)
        return 123


def test_native_click_bounds_and_passthrough(qt_app):
    monitor = OutsideClickMonitor()
    monitor.user32 = NativeMouseStub()
    monitor.handle = 1
    generations = []
    monitor.clicked.connect(generations.append)
    for x, message in [(0, 0x201), (300, 0x200), (300, 0x201), (-201, 0x204)]:
        event = MouseEvent(point=wintypes.POINT(x, 100))
        assert monitor._on_mouse(0, message, ctypes.addressof(event)) == 123
    assert generations == [0, 0]
    assert len(monitor.user32.forwarded) == 4
    monitor.handle = None
