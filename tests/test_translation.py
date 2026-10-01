from pathlib import Path

import pytest

from grepzztranslate.ocr import select_ocr_text
from grepzztranslate.translation import TranslationService
from grepzztranslate.lookup import LookupService
from grepzztranslate.paths import PathManager
from grepzztranslate.resources import ResourceManager


def test_english_ocr_not_overridden_by_stray_kanji():
    assert select_ocr_text({"en": "beautiful world", "ja": "beautiful wor旧"}) == "beautiful world"
    assert select_ocr_text({"en": "oo", "ja": "経験を積む"}) == "経験を積む"


def test_empty_enlarged_ocr_retries_original_scale():
    import asyncio
    from grepzztranslate.ocr import OCRService
    service = OCRService.__new__(OCRService)
    service.scale = 2
    calls = []
    async def recognize(image, scale):
        calls.append(scale)
        return "今日はいい天気です。" if scale == 1 else ""
    service._recognize_scale = recognize
    assert asyncio.run(service.recognize(None)) == "今日はいい天気です。"
    assert calls == [2, 1]


def test_missing_models_and_length_limit(tmp_path):
    service = TranslationService(tmp_path)
    with pytest.raises(RuntimeError, match="未安装"):
        service.translate("beautiful world", "English")
    with pytest.raises(ValueError, match="1200"):
        service.translate("a" * 1201, "English")


@pytest.mark.parametrize("text,language,expected", [
    ("beautiful world", "English", "美丽"),
    ("The situation deteriorated rapidly.", "English", "恶化"),
    ("I am reading a book.", "English", "书"),
    ("今日はいい天気です。", "Japanese", "天气"),
])
def test_real_offline_translation(text, language, expected):
    root = Path(__file__).resolve().parents[1]
    service = LookupService(ResourceManager(PathManager(root)))
    if not service.translation.available(language):
        pytest.skip("Install offline models for integration tests")
    result = service.lookup(text)
    assert result.translated and expected in result.meaning
    assert "▁" not in result.meaning
    assert result.normalized_text == text
    assert not result.components


def test_dictionary_still_preferred():
    root = Path(__file__).resolve().parents[1]
    result = LookupService(ResourceManager(PathManager(root))).lookup("apple")
    assert result.meaning and not result.translated
