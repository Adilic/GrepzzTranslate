import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

log = logging.getLogger(__name__)


@dataclass
class ScreenFrame:
    geometry: QRect
    pixmap: QPixmap


class ScreenshotService:
    def capture(self) -> list[ScreenFrame]:
        frames = [ScreenFrame(screen.geometry(), screen.grabWindow(0)) for screen in QApplication.screens()]
        if not frames or any(frame.pixmap.isNull() for frame in frames):
            raise RuntimeError("无法读取屏幕画面。锁屏或受保护内容可能无法截图。")
        return frames

    @staticmethod
    def crop(frames: list[ScreenFrame], selection: QRect) -> QImage:
        selected = [frame for frame in frames if frame.geometry.intersects(selection)]
        if not selected or selection.width() < 3 or selection.height() < 3:
            return QImage()
        scale = max(frame.pixmap.width() / frame.geometry.width() for frame in selected)
        # 大きな仮想デスクトップでも一時画像のメモリを制限する。
        scale = min(scale, 8192 / max(selection.width(), selection.height()))
        image = QImage(round(selection.width() * scale), round(selection.height() * scale), QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        for frame in selected:
            intersect = selection.intersected(frame.geometry)
            sx = frame.pixmap.width() / frame.geometry.width()
            sy = frame.pixmap.height() / frame.geometry.height()
            source = QRectF((intersect.x() - frame.geometry.x()) * sx, (intersect.y() - frame.geometry.y()) * sy,
                            intersect.width() * sx, intersect.height() * sy)
            target = QRectF((intersect.x() - selection.x()) * scale, (intersect.y() - selection.y()) * scale,
                            intersect.width() * scale, intersect.height() * scale)
            native = frame.pixmap.toImage()
            native.setDevicePixelRatio(1)
            painter.drawImage(target, native, source)
        painter.end()
        return image


class CaptureOverlay(QWidget):
    def __init__(self, frame: ScreenFrame, controller: "CaptureController") -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.frame = frame
        self.controller = controller
        self.setGeometry(frame.geometry)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.frame.pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 115))
        if self.controller.selection is not None:
            rect = self.controller.selection.translated(-self.frame.geometry.topLeft())
            painter.save()
            painter.setClipRect(rect)
            painter.drawPixmap(self.rect(), self.frame.pixmap)
            painter.restore()
            painter.setPen(QPen(QColor("#70dec9"), 2))
            painter.drawRect(rect)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(24, 34, "GrepzzTranslate  ·  拖动框选文字  ·  Esc / 右键取消")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.controller.cancel()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.controller.start = event.globalPosition().toPoint()
            self.controller.update_selection(self.controller.start)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.controller.start is not None:
            self.controller.update_selection(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.controller.start is not None:
            self.controller.update_selection(event.globalPosition().toPoint())
            self.controller.finish()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.controller.cancel()


class CaptureController(QObject):
    captured = Signal(QImage, QRect)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.service = ScreenshotService()
        self.frames: list[ScreenFrame] = []
        self.overlays: list[CaptureOverlay] = []
        self.start: QPoint | None = None
        self.selection: QRect | None = None

    @property
    def active(self) -> bool:
        return bool(self.overlays)

    def begin(self) -> None:
        if self.active:
            return
        self.frames = self.service.capture()
        self.start = None
        self.selection = None
        self.overlays = [CaptureOverlay(frame, self) for frame in self.frames]
        for overlay in self.overlays:
            overlay.show()
        from PySide6.QtGui import QCursor
        focused = next((o for o in self.overlays if o.frame.geometry.contains(QCursor.pos())), self.overlays[0])
        focused.activateWindow()
        focused.setFocus()
        log.info("Capture started")

    def update_selection(self, end: QPoint) -> None:
        self.selection = QRect(self.start, end).normalized()
        for overlay in self.overlays:
            overlay.update()

    def close_overlays(self) -> None:
        for overlay in self.overlays:
            overlay.close()
            overlay.deleteLater()
        self.overlays.clear()

    def cancel(self) -> None:
        self.close_overlays()
        self.frames.clear()
        self.start = self.selection = None
        log.info("Capture cancelled")
        self.cancelled.emit()

    def finish(self) -> None:
        rect = self.selection
        self.close_overlays()
        try:
            image = self.service.crop(self.frames, rect) if rect else QImage()
        finally:
            self.frames.clear()
            self.start = self.selection = None
        if image.isNull():
            self.cancelled.emit()
            return
        log.info("Capture completed: %dx%d", image.width(), image.height())
        self.captured.emit(image, rect)
