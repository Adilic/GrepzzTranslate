import json
import logging
import time

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from .app import ApplicationController
from .config import Config
from .storage import HistoryRepository

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
    except Exception as exc:
        log.exception("Self-test failed")
        error = str(exc)
    finally:
        window.close()
        controller.exit()
        wait_until(lambda: not controller.thread.isRunning())
    report = {"passed": not error, "error": error, "checks": records,
              "note": "真实屏幕截图；框选通过 Qt 测试事件驱动。物理 Alt+Q 另行验证。"}
    (paths.logs / "self-test.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Self-test: %s", report)
    return 1 if error else 0
