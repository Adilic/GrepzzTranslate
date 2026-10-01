import logging
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

log = logging.getLogger(__name__)


def select_ocr_text(outputs: dict[str, str]) -> str:
    japanese, english = outputs.get("ja", ""), outputs.get("en", "")
    japanese_count = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", japanese))
    latin_count = len(re.findall(r"[A-Za-z]", japanese))
    # 少数の誤認識漢字だけで英文を上書きしない。
    if japanese_count and (japanese_count >= latin_count or not english.strip()):
        japanese = "".join(line.strip() for line in japanese.splitlines())
        return re.sub(r"(?<=[\u3000-\u9fff]) +(?=[\u3000-\u9fff])", "", japanese)
    return english or japanese


def preprocess(image: QImage, scale: float = 2.0, max_dimension: int = 4096) -> QImage:
    if image.isNull():
        raise ValueError("截图为空")
    factor = min(scale, max_dimension / max(image.width(), image.height()))
    processed = image.scaled(max(1, round(image.width() * factor)), max(1, round(image.height() * factor)),
                             Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return processed.convertToFormat(QImage.Format.Format_ARGB32)


class OCRService:
    @staticmethod
    def available_languages() -> list[str]:
        import winrt.windows.foundation.collections
        from winrt.windows.media.ocr import OcrEngine

        return [language.language_tag for language in OcrEngine.available_recognizer_languages]

    def __init__(self, languages: list[str], scale: float = 2.0) -> None:
        from winrt.windows.globalization import Language
        from winrt.windows.media.ocr import OcrEngine

        self.scale = scale
        self.max_dimension = OcrEngine.max_image_dimension
        self.engines = {}
        self.missing = []
        for code in languages:
            engine = OcrEngine.try_create_from_language(Language({"en": "en-US", "ja": "ja-JP"}[code]))
            if engine:
                self.engines[code] = engine
            else:
                self.missing.append(code)
        if not self.engines:
            raise RuntimeError("未安装可用的 Windows OCR 英语/日语语言资源。请查看 README 的 OCR 资源说明。")
        log.info("OCR initialized: %s; missing: %s", list(self.engines), self.missing)

    async def recognize(self, image: QImage) -> str:
        text = await self._recognize_scale(image, self.scale)
        # 大きな日本語文字は拡大後に認識されない場合がある。
        if not text.strip() and self.scale != 1:
            text = await self._recognize_scale(image, 1.0)
        return text

    async def _recognize_scale(self, image: QImage, scale: float) -> str:
        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.storage.streams import DataWriter

        processed = preprocess(image, scale, self.max_dimension)
        writer = DataWriter()
        writer.write_bytes(bytes(processed.constBits()))
        bitmap = SoftwareBitmap.create_copy_from_buffer(writer.detach_buffer(), BitmapPixelFormat.BGRA8,
                                                        processed.width(), processed.height())
        writer.close()
        outputs = {}
        try:
            for code, engine in self.engines.items():
                result = await engine.recognize_async(bitmap)
                outputs[code] = "\n".join(line.text for line in result.lines)
        finally:
            bitmap.close()
        return select_ocr_text(outputs)
