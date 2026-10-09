import json
import logging
import time
import ctypes
import sys

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from .app import ApplicationController
from .config import Config
from .storage import HistoryRepository
from .selection import _Input, _Keyboard

log = logging.getLogger(__name__)


def run_self_test(app, paths) -> int:
    controller = ApplicationController(app, paths, Config())
    window = QWidget(None, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
    window.setWindowTitle("GrepzzTranslate · 自动验收")
    window.setStyleSheet("background: white; color: black;")
    layout = QVBoxLayout(window)
    layout.setContentsMargins(35, 35, 35, 35)
    label = QLabel("considerable")
    label.setFixedHeight(110)
    label.setStyleSheet("font-family: 'Yu Gothic', 'Segoe UI'; font-size: 38px;")
    layout.addWidget(label)
    continue_button = QPushButton("继续阅读")
    layout.addWidget(continue_button)
    outside_clicks = []
    continue_button.clicked.connect(lambda: outside_clicks.append(True))
    window.resize(600, 240)
    window.move(app.primaryScreen().availableGeometry().center() - QPoint(300, 90))
    records = []
    results = []
    errors = []
    controller.worker.finished.connect(lambda request_id, result: results.append(result))
    controller.worker.failed.connect(lambda request_id, message: errors.append(message))
    controller.selection.failed.connect(errors.append)
    controller.capture.captured.connect(lambda image, rect: image.save(str(paths.logs / f"self-test-capture-{len(results)}.png")))

    def wait_until(predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while not predicate():
            app.processEvents()
            if time.monotonic() > deadline:
                raise TimeoutError("验收超时")
            time.sleep(0.01)
        app.processEvents()

    def settle(seconds=0.6):
        deadline = time.monotonic() + seconds
        wait_until(lambda: time.monotonic() >= deadline)

    error = ""
    try:
        wait_until(lambda: not controller.initializing)
        if not controller.hotkey.registered:
            raise RuntimeError("快捷键未注册，可能已有另一个实例运行")
        # 検証履歴を個人の履歴データベースから分離する。
        controller.worker.history = HistoryRepository(paths.data / "self-test-history.db")
        samples = [("considerable", None), ("Windows", None), ("apple", None), ("経験", "けいけん"),
                   ("beautiful world", None), ("The situation deteriorated rapidly.", None), ("今日はいい天気です。", None)]
        if "--selection-only" in sys.argv:
            samples = []
        for index, (text, reading) in enumerate(samples):
            label.setStyleSheet("font-family: 'Yu Gothic', 'Segoe UI'; font-size: " + ("24px;" if len(text) > 25 else "38px;"))
            label.setText(text)
            window.show()
            window.raise_()
            window.activateWindow()
            settle()
            target = QRect(label.mapToGlobal(QPoint(0, 0)), label.size())
            controller.start_capture()
            wait_until(lambda: controller.capture.active)
            overlay = next(o for o in controller.capture.overlays if o.frame.geometry.contains(target.center()))
            local = target.translated(-overlay.frame.geometry.topLeft())
            QTest.mousePress(overlay, Qt.MouseButton.LeftButton, pos=local.topLeft())
            QTest.mouseRelease(overlay, Qt.MouseButton.LeftButton, pos=local.bottomRight())
            wait_until(lambda: len(results) > index or errors)
            if errors:
                raise RuntimeError(errors[0])
            result = results[index]
            if result.language == "Japanese":
                from .furigana import FuriganaText
                assert result.reading and result.tokens, "日语读音丢失"
                assert controller.popup.findChild(FuriganaText) is not None, "日语注音未显示"
            if index >= 4:
                expected = ["美丽", "恶化", "天气"][index - 4]
                if not result.translated or expected not in (result.meaning or ""):
                    raise AssertionError(f"Expected translation of {text}; actual {result}")
            elif (result.headword or "").casefold() != text.casefold() or (reading and result.reading != reading):
                raise AssertionError(f"Expected {text}; actual {result}")
            settle(0.1)
            if not controller.popup.isVisible():
                raise AssertionError("结果浮窗未显示")
            assert controller.popup.monitor.handle, "Windows 外部点击监听未安装"
            controller.popup.grab().save(str(paths.logs / f"self-test-popup-{index}.png"))
            if index % 2 == 0:
                before = len(outside_clicks)
                QTest.mouseClick(continue_button, Qt.MouseButton.LeftButton)
                assert len(outside_clicks) == before + 1
                close_method = "outside_click"
            else:
                QTest.keyClick(controller.popup, Qt.Key.Key_Escape)
                close_method = "escape"
            assert not controller.popup.isVisible()
            assert controller.thread.isRunning()
            records.append({"sample": text, "reading": result.reading, "translation": result.meaning if result.translated else None, "popup_closed": True,
                            "close_method": close_method,
                            "native_monitor_installed": True,
                            "background_alive": True, "hotkey_registered": controller.hotkey.registered})
        assert controller.selection_hotkey.registered, "Alt+1 注册失败"
        editor = QLineEdit(window)
        layout.addWidget(editor)
        clipboard = app.clipboard()
        original = clipboard.mimeData()
        from PySide6.QtCore import QMimeData
        saved = QMimeData()
        if original:
            for fmt in original.formats():
                saved.setData(fmt, original.data(fmt))
        try:
            for text in ("book", "I am reading a book.", "今日はいい天気です。"):
                controller.popup.hide()
                window.show()
                window.raise_()
                window.activateWindow()
                editor.setText(text)
                editor.setFocus()
                editor.selectAll()
                settle()
                api = controller.selection.backend.api
                api.SetForegroundWindow.argtypes = [ctypes.c_void_p]
                api.SetForegroundWindow.restype = ctypes.c_int
                api.SetForegroundWindow(int(window.winId()))
                settle(0.2)
                # A real click restores keyboard focus after dismissing a popup.
                from ctypes import wintypes
                previous_cursor = wintypes.POINT()
                api.GetCursorPos(ctypes.byref(previous_cursor))
                local = editor.mapTo(window, editor.rect().center())
                ratio = window.devicePixelRatioF()
                point = wintypes.POINT(round(local.x() * ratio), round(local.y() * ratio))
                api.ClientToScreen.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.POINT)]
                api.ClientToScreen(int(window.winId()), ctypes.byref(point))
                api.SetCursorPos(point.x, point.y)
                clicks = (_Input * 2)()
                clicks[0].payload.mouse.flags = 0x0002
                clicks[1].payload.mouse.flags = 0x0004
                api.SendInput(2, clicks, ctypes.sizeof(_Input))
                settle(0.2)
                api.SetCursorPos(previous_cursor.x, previous_cursor.y)
                editor.selectAll()
                assert controller.selection.backend.foreground() == int(window.winId()), "测试窗口未获得焦点"
                clipboard.setText("selection self-test sentinel")
                count = len(results)
                keys = (_Input * 4)()
                for event, (vk, flags) in zip(keys, [(0x12, 0), (0x31, 0), (0x31, 2), (0x12, 2)]):
                    event.type = 1
                    event.payload.keyboard = _Keyboard(vk, 0, flags, 0, 0)
                assert controller.selection.backend.api.SendInput(4, keys, ctypes.sizeof(_Input)) == 4
                wait_until(lambda: len(results) > count or errors, timeout=30)
                assert not errors, errors
                result = results[-1]
                assert result.normalized_text == text and result.meaning
                assert result.translated == (text != "book")
                assert clipboard.text() == "selection self-test sentinel"
                assert controller.popup.isVisible()
                QTest.mouseClick(continue_button, Qt.MouseButton.LeftButton)
                assert not controller.popup.isVisible()
                records.append({"selection": text, "native_alt_1": True,
                                "translated": result.translated, "clipboard_restored": True,
                                "outside_dismiss": True})
        finally:
            clipboard.setMimeData(saved)
    except Exception as exc:
        log.exception("Self-test failed")
        error = str(exc)
    finally:
        window.close()
        controller.exit()
        wait_until(lambda: not controller.thread.isRunning())
    report = {"passed": not error, "error": error, "checks": records,
              "note": "真实屏幕截图；框选和外部点击由 Qt 测试事件驱动；Alt+1 由 Windows SendInput 触发，原生复制读取可编辑测试文本。未覆盖 Chrome PDF。"}
    (paths.logs / "self-test.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Self-test: %s", report)
    return 1 if error else 0
