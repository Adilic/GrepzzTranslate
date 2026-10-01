import json
import sqlite3
from contextlib import closing

import pytest

from grepzztranslate.config import Config, ConfigManager
from grepzztranslate.hotkey import parse_hotkey
from grepzztranslate.language import LanguageDetector, normalize
from grepzztranslate.lookup import LookupService
from grepzztranslate.resources import ResourceManager
from grepzztranslate.storage import HistoryRepository


@pytest.mark.parametrize("text, expected", [(" considerable\n", "considerable"), ("don't", "don't"), ("経験\nを  積む", "経験 を 積む"), ("cafe\u0301", "café")])
def test_normalization(text, expected):
    assert normalize(text) == expected


@pytest.mark.parametrize("text, expected", [("経験を積む", "Japanese"), ("considerable", "English"), ("123 !", "Unknown"), ("経験 test English", "English")])
def test_language(text, expected):
    assert LanguageDetector().detect(text) == expected


def test_config_roundtrip_and_invalid(tmp_path):
    manager = ConfigManager(tmp_path / "config.json")
    assert manager.load() == Config()
    manager.path.write_text(json.dumps({"ocr_languages": ["xx"]}), encoding="utf-8")
    with pytest.raises(ValueError):
        manager.load()
    with pytest.raises(ValueError):
        parse_hotkey("alt+alt+q")
    assert parse_hotkey("ctrl+shift+f12") == (0x4006, 0x7B)


@pytest.mark.parametrize("text, headword", [("considerable", "considerable"), ("deteriorated", "deteriorate"), ("BOOKS", "book"), ("studies", "study"), ("running", "run"), ("went", "go"), ("take care of", "take care of")])
def test_english_lookup(paths, text, headword):
    result = LookupService(ResourceManager(paths)).lookup(text)
    assert result.headword == headword
    assert result.meaning


def test_japanese_reading_tokens(paths):
    service = LookupService(ResourceManager(paths))
    result = service.lookup("経験を積む")
    assert result.reading == "けいけんをつむ"
    assert result.meaning == "积累经验"
    assert [(t.surface, t.dictionary_form) for t in result.tokens] == [("経験", "経験"), ("を", "を"), ("積む", "積む")]
    assert service.lookup("美しかった").tokens[0].dictionary_form == "美しい"


def test_missing_empty_sentence(paths):
    service = LookupService(ResourceManager(paths))
    assert service.lookup("").message.startswith("No text recognized.")
    assert service.lookup("123").message.startswith("Unsupported language.")
    assert service.lookup("qwertyabc").message.startswith("No definition found.")
    phrase = service.lookup("The situation deteriorated rapidly.")
    assert "不是整句翻译" in phrase.message
    assert any(part.headword == "deteriorate" for part in phrase.components)
    service.english.path.unlink()
    assert "not installed" in service.lookup("book").message
    assert "not installed" in ResourceManager(paths).check_english_dictionary()


def test_history_merge_by_lemma(paths):
    service = LookupService(ResourceManager(paths))
    history = HistoryRepository(paths.data / "history.db")
    history.record(service.lookup("deteriorated"))
    history.record(service.lookup("deteriorate"))
    with closing(sqlite3.connect(history.path)) as conn:
        assert conn.execute("SELECT headword, lookup_count, synced FROM history").fetchall() == [("deteriorate", 2, 0)]


def test_corrupt_dictionary(paths):
    resources = ResourceManager(paths)
    resources.dictionary_path("english").write_bytes(b"bad database")
    assert "invalid" in resources.check_english_dictionary()
    assert LookupService(resources).lookup("book").message


def test_spelling_suggestion(paths):
    service = LookupService(ResourceManager(paths))
    result = service.lookup("considrable")
    assert result.headword is None
    assert "considerable" in result.suggestions
