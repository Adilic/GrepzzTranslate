import asyncio
import logging
import sys

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage

from .config import Config
from .lookup import LookupService
from .ocr import OCRService
from .paths import PathManager
from .resources import ResourceManager
from .storage import HistoryRepository

log = logging.getLogger(__name__)


class LookupWorker(QObject):
    ready = Signal(list)
    finished = Signal(int, object)
    failed = Signal(int, str)

    def __init__(self, paths: PathManager, config: Config) -> None:
        super().__init__()
        self.paths = paths
        self.config = config
        self.ocr = None
        self.lookup = None
        self.history = None
        self.loop = None

    @Slot()
    def initialize(self) -> None:
        warnings = []
        self.ocr = None
        try:
            log.info("Resource initialization started: %s", self.paths.root)
            if self.loop is None:
                self.loop = asyncio.new_event_loop()
            resources = ResourceManager(self.paths)
            warnings.extend(filter(None, [resources.check_english_dictionary(), resources.check_japanese_dictionary()]))
            if getattr(sys, "frozen", False):
                if not (self.paths.resources / "sudachi" / "system.dic").is_file():
                    warnings.append("缺少 resources/sudachi/system.dic。")
                if warnings:
                    raise RuntimeError("程序资源不完整，请使用完整解压后的 dist/GrepzzTranslate/GrepzzTranslate.exe。\n" + "\n".join(warnings))
            self.lookup = LookupService(resources)
            if self.lookup.japanese_error:
                warnings.append(self.lookup.japanese_error)
            self.history = HistoryRepository(self.paths.data / "history.db")
            self.ocr = OCRService(self.config.ocr_languages, self.config.ocr_scale)
            if self.ocr.missing:
                warnings.append("缺少 Windows OCR 语言资源：" + ", ".join(self.ocr.missing) + "。见 README。")
        except Exception as exc:
            log.exception("Resource initialization failed")
            warnings.append(str(exc))
        finally:
            self.ready.emit(warnings)

    @Slot(int, QImage)
    def process(self, request_id: int, image: QImage) -> None:
        try:
            if not self.ocr or not self.lookup:
                raise RuntimeError("OCR 尚不可用，请安装资源后从托盘重新加载。")
            log.info("OCR started")
            text = self.loop.run_until_complete(asyncio.wait_for(self.ocr.recognize(image), timeout=20))
            log.info("OCR text: %s", text if self.config.log_ocr_text else f"[omitted; {len(text)} characters]")
            self.lookup_text(request_id, text)
        except TimeoutError:
            log.exception("OCR timed out")
            self.failed.emit(request_id, "本次识别超时，请按快捷键重新框选。")
        except Exception as exc:
            log.exception("OCR / lookup failed")
            self.failed.emit(request_id, str(exc))

    @Slot(int, str)
    def lookup_text(self, request_id: int, text: str) -> None:
        try:
            if not self.lookup:
                raise RuntimeError("词典尚未就绪，请重新加载资源。")
            result = self.lookup.lookup(text)
            if result.normalized_text and self.history:
                try:
                    self.history.record(result)
                except Exception:
                    log.exception("History write failed")
                    result.message += "\n历史记录保存失败，请检查 data 目录写入权限。"
            self.finished.emit(request_id, result)
        except Exception as exc:
            log.exception("Text lookup failed")
            self.failed.emit(request_id, str(exc))

    @Slot()
    def shutdown(self) -> None:
        self.ocr = self.lookup = self.history = None
        if self.loop:
            self.loop.close()
            self.loop = None
        self.thread().quit()
