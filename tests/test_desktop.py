import asyncio

import pytest
from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton

from grepzztranslate.capture import CaptureController, ScreenFrame, ScreenshotService
from grepzztranslate.ocr import OCRService, preprocess
from grepzztranslate.ui import LookupPopup, clamp_position
from grepzztranslate.models import LookupResult


def frame(rect, color, dpr=1):
    pixmap = QPixmap(rect.width() * dpr, rect.height() * dpr)
    pixmap.fill(QColor(color))
    pixmap.setDevicePixelRatio(dpr)
    return ScreenFrame(rect, pixmap)


def test_mixed_dpi_negative_coordinates(qt_app):
    frames = [frame(QRect(-100, 0, 100, 100), "red", 1), frame(QRect(0, 0, 100, 100), "blue", 2)]
    image = ScreenshotService.crop(frames, QRect(-50, 10, 100, 50))
    assert image.size() == QSize(200, 100)
    assert image.pixelColor(20, 20) == QColor("red")
    assert image.pixelColor(150, 20) == QColor("blue")
    assert ScreenshotService.crop(frames, QRect(-50, 0, 1, 1)).isNull()


def test_preprocess_limits_and_format(qt_app):
    image = QImage(100, 50, QImage.Format.Format_RGB32)
    result = preprocess(image, 2, 150)
    assert result.size() == QSize(150, 75)
    assert result.format() == QImage.Format.Format_ARGB32


def test_popup_clamp_and_escape(qt_app):
    available = QRect(-1920, 0, 1920, 1080)
    point = clamp_position(QRect(-20, 1040, 15, 30), QSize(390, 300), available)
    assert available.contains(QRect(point, QSize(390, 300)))
    popup = LookupPopup("dark")
    popup.show_message("测试", QRect(20, 20, 50, 20))
    QTest.keyClick(popup, Qt.Key.Key_Escape)
    assert not popup.isVisible()
    popup.deleteLater()


def test_short_definition_fits_without_scroll(qt_app):
    popup = LookupPopup("dark")
    popup.show_result(LookupResult("considerable", "considerable", "English", headword="considerable",
                                  phonetic="/kənˈsɪdərəbəl/", part_of_speech="adj.", meaning="相当大的；大量的"), QRect(20, 20, 60, 20))
    qt_app.processEvents()
    assert popup.scroll.verticalScrollBar().maximum() == 0
    popup.close()


def test_ocr_correction_and_escape(qt_app):
    popup = LookupPopup("dark")
    requests = []
    popup.lookup_requested.connect(requests.append)
    popup.show_result(LookupResult("Wind0ws", "Wind0ws", "English"), QRect(20, 20, 60, 20))
    assert not popup.editor.isVisible()
    QTest.mouseClick(popup.edit_button, Qt.MouseButton.LeftButton)
    assert popup.isVisible() and popup.editor.isVisible()
    popup.editor.setText("Windows")
    QTest.keyClick(popup.editor, Qt.Key.Key_Return)
    assert requests == ["Windows"]
    QTest.keyClick(popup.editor, Qt.Key.Key_Escape)
    assert not popup.isVisible()


def test_outside_click_dismisses_without_eating_click(qt_app):
    reading_button = QPushButton("继续阅读")
    reading_button.show()
    clicked, dismissed = [], []
    reading_button.clicked.connect(lambda: clicked.append(True))
    popup = LookupPopup("light")
    popup.dismissed.connect(lambda: dismissed.append(True))
    popup.show_message("查词结果", QRect(300, 100, 100, 20))
    QTest.mouseClick(reading_button, Qt.MouseButton.LeftButton)
    assert not popup.isVisible()
    assert not popup.monitor.handle
    assert clicked == [True]
    popup.dismiss()
    assert dismissed == [True]
    reading_button.close()


def test_deactivate_and_late_result_stay_dismissed(qt_app):
    from grepzztranslate.app import ApplicationController

    controller = ApplicationController.__new__(ApplicationController)
    QObject.__init__(controller)
    controller.request_id, controller.busy, controller.exiting = 7, True, False
    controller.anchor = QRect(50, 50, 100, 20)
    controller.popup = LookupPopup("light")
    controller.popup.dismissed.connect(controller.dismiss)
    controller.popup.show_message("正在识别", controller.anchor)
    qt_app.sendEvent(controller.popup, QEvent(QEvent.Type.WindowDeactivate))
    assert controller.request_id == 8
    controller.on_result(7, LookupResult("book", "book", "English", meaning="书"))
    assert not controller.popup.isVisible()
    assert not controller.busy


def test_overlay_cancel_and_drag(qt_app):
    controller = CaptureController()
    controller.service.capture = lambda: [frame(QRect(0, 0, 400, 300), "white")]
    received = []
    controller.captured.connect(lambda image, rect: received.append((image, rect)))
    controller.begin()
    overlay = controller.overlays[0]
    QTest.keyClick(overlay, Qt.Key.Key_Escape)
    assert not controller.active
    controller.begin()
    overlay = controller.overlays[0]
    QTest.mousePress(overlay, Qt.MouseButton.LeftButton, pos=QPoint(60, 70))
    QTest.mouseRelease(overlay, Qt.MouseButton.LeftButton, pos=QPoint(200, 140))
    assert not controller.active
    assert received and received[0][0].width() >= 140


@pytest.mark.parametrize("text,font_family", [("considerable", "Segoe UI"), ("経験", "Yu Gothic"), ("経験を積む", "Yu Gothic")])
def test_real_windows_ocr(qt_app, text, font_family):
    image = QImage(650, 100, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    painter.setPen(Qt.GlobalColor.black)
    font = QFont(font_family)
    font.setPixelSize(38)
    painter.setFont(font)
    painter.drawText(20, 60, text)
    painter.end()
    actual = asyncio.run(OCRService(["en", "ja"]).recognize(image))
    assert actual.strip() == text
