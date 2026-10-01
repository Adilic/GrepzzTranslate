import logging

from PySide6.QtCore import QObject, QPoint, QRect, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QColor, QCursor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QMessageBox, QSystemTrayIcon

from .capture import CaptureController
from .config import Config, ConfigManager
from .hotkey import HotkeyManager
from .models import LookupResult
from .paths import PathManager
from .ui import LookupPopup, SettingsDialog
from .worker import LookupWorker

log = logging.getLogger(__name__)


def app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#1b443b"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 14, 14)
    painter.setPen(QColor("#88ecd0"))
    font = painter.font()
    font.setPixelSize(42)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


class ApplicationController(QObject):
    lookup_requested = Signal(int, QImage)
    text_lookup_requested = Signal(int, str)
    reload_requested = Signal()
    shutdown_requested = Signal()

    def __init__(self, app: QApplication, paths: PathManager, config: Config) -> None:
        super().__init__()
        self.app, self.paths, self.config = app, paths, config
        self.busy = False
        self.initializing = True
        self.exiting = False
        self.request_id = 0
        self.anchor = QRect(QCursor.pos(), QCursor.pos() + QPoint(1, 1))
        self.capture = CaptureController()
        self.capture.captured.connect(self.on_capture)
        self.popup = LookupPopup(config.theme)
        self.popup.dismissed.connect(self.dismiss)
        self.popup.lookup_requested.connect(self.correct_text)
        self.popup.recapture_requested.connect(self.start_capture)
        self.hotkey = HotkeyManager(app)
        self.hotkey.triggered.connect(self.start_capture)
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip("GrepzzTranslate · " + config.capture_hotkey)
        self.menu = QMenu()
        self.menu.addAction("截图查词 · " + config.capture_hotkey, self.start_capture)
        self.menu.addSeparator()
        self.menu.addAction("Open Settings · 设置", self.settings)
        self.menu.addAction("Reload Resources · 重新加载", self.reload)
        self.menu.addSeparator()
        self.menu.addAction("Exit · 退出", self.exit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
        self.thread = QThread(self)
        self.worker = LookupWorker(paths, config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.initialize)
        self.lookup_requested.connect(self.worker.process)
        self.text_lookup_requested.connect(self.worker.lookup_text)
        self.reload_requested.connect(self.worker.initialize)
        self.shutdown_requested.connect(self.worker.shutdown)
        self.worker.ready.connect(self.on_ready, Qt.ConnectionType.QueuedConnection)
        self.worker.finished.connect(self.on_result, Qt.ConnectionType.QueuedConnection)
        self.worker.failed.connect(self.on_error, Qt.ConnectionType.QueuedConnection)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.on_thread_finished)
        self.thread.start()
        self.init_timer = QTimer(self)
        self.init_timer.setSingleShot(True)
        self.init_timer.timeout.connect(self.initialization_timeout)
        self.init_timer.start(30000)
        try:
            self.hotkey.register(config.capture_hotkey)
        except Exception as exc:
            QTimer.singleShot(0, lambda message=str(exc): self.notify(message))

    def notify(self, message: str) -> None:
        log.warning(message)
        self.tray.showMessage("GrepzzTranslate", message, QSystemTrayIcon.MessageIcon.Warning, 7000)
        self.popup.show_message(message, self.anchor)

    def tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.start_capture()

    @Slot(list)
    def on_ready(self, warnings: list[str]) -> None:
        self.init_timer.stop()
        self.initializing = False
        if self.exiting:
            return
        if warnings:
            self.notify("\n".join(warnings))
        else:
            self.tray.showMessage("GrepzzTranslate 已就绪", f"按 {self.config.capture_hotkey} 截图查词，点击外部自动收起。")
        log.info("Resources ready; warnings=%d", len(warnings))

    def initialization_timeout(self) -> None:
        if self.initializing and not self.exiting:
            self.notify("启动超过 30 秒仍未完成。请退出后使用完整发行目录中的程序重新打开；详细信息见 logs/grepzztranslate.log。")

    def start_capture(self) -> None:
        if self.exiting or self.capture.active:
            return
        if self.busy or self.initializing:
            message = "正在初始化本地资源…" if self.initializing else "正在本地识别或翻译上一个选区…"
            if self.initializing and not self.init_timer.isActive():
                message = "启动未完成，请退出后重新打开完整发行版。详细信息见 logs/grepzztranslate.log。"
            self.tray.showMessage("GrepzzTranslate", message)
            return
        self.request_id += 1
        self.popup.hide()
        # 浮窓を隠した次のイベントで画面を取得する。
        QTimer.singleShot(60, self.begin_capture)

    def begin_capture(self) -> None:
        if self.exiting:
            return
        try:
            self.capture.begin()
        except Exception as exc:
            log.exception("Capture failed")
            self.notify(str(exc))

    def on_capture(self, image: QImage, rect: QRect) -> None:
        self.anchor = rect if self.config.popup_position == "capture" else QRect(QCursor.pos(), QPoint(QCursor.pos().x()+1, QCursor.pos().y()+1))
        if image.width() < 20 or image.height() < 12:
            self.popup.show_result(LookupResult("", "", "Unknown", message="选区太小，请框选完整单词，并在文字周围留少量边距。"), self.anchor)
            return
        self.busy = True
        self.popup.show_message("正在本地识别与查询…", self.anchor)
        self.lookup_requested.emit(self.request_id, image)

    def correct_text(self, text: str) -> None:
        if self.busy or self.initializing or self.exiting:
            return
        self.request_id += 1
        self.busy = True
        self.popup.show_message("正在查询本地词库…", self.anchor)
        self.text_lookup_requested.emit(self.request_id, text)

    @Slot(int, object)
    def on_result(self, request_id: int, result: LookupResult) -> None:
        self.busy = False
        if request_id == self.request_id and not self.exiting:
            self.popup.show_result(result, self.anchor)

    @Slot(int, str)
    def on_error(self, request_id: int, message: str) -> None:
        self.busy = False
        if request_id == self.request_id and not self.exiting:
            self.popup.show_message(message, self.anchor)

    def dismiss(self) -> None:
        self.request_id += 1

    def reload(self) -> None:
        if self.busy or self.initializing or self.exiting:
            self.tray.showMessage("GrepzzTranslate", "请等待当前识别或初始化完成。")
            return
        self.initializing = True
        self.init_timer.start(30000)
        self.reload_requested.emit()

    def settings(self) -> None:
        if self.busy or self.initializing or self.capture.active:
            self.tray.showMessage("GrepzzTranslate", "请等待当前操作完成。")
            return
        dialog = SettingsDialog(self.config)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        old = self.config
        try:
            config = dialog.value()
            self.hotkey.register(config.capture_hotkey)
            try:
                ConfigManager(self.paths.config).save(config)
            except Exception:
                self.hotkey.register(old.capture_hotkey)
                raise
            self.config = config
            self.worker.config = config
            self.popup.hide()
            self.popup.deleteLater()
            self.popup = LookupPopup(config.theme)
            self.popup.dismissed.connect(self.dismiss)
            self.popup.lookup_requested.connect(self.correct_text)
            self.popup.recapture_requested.connect(self.start_capture)
            self.tray.setToolTip("GrepzzTranslate · " + config.capture_hotkey)
            self.menu.actions()[0].setText("截图查词 · " + config.capture_hotkey)
        except Exception as exc:
            log.exception("Settings save failed")
            QMessageBox.warning(None, "设置未保存", str(exc))

    def exit(self) -> None:
        if self.exiting:
            return
        self.exiting = True
        self.hotkey.unregister()
        self.capture.cancel()
        self.popup.hide()
        self.tray.hide()
        self.shutdown_requested.emit()

    def on_thread_finished(self) -> None:
        if self.exiting:
            log.info("Application stopped")
            self.app.quit()
