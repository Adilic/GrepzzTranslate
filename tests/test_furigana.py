from pathlib import Path
from PySide6.QtCore import QRect
from grepzztranslate.furigana import FuriganaText
from grepzztranslate.lookup import LookupService
from grepzztranslate.paths import PathManager
from grepzztranslate.resources import ResourceManager
from grepzztranslate.ui import LookupPopup


def test_translated_japanese_keeps_annotations(qt_app):
    root = Path(__file__).resolve().parents[1]
    result = LookupService(ResourceManager(PathManager(root))).lookup("本書は多くの人から影響を受けた。")
    assert result.translated and result.reading and result.tokens
    popup = LookupPopup()
    popup.show_result(result, QRect(20, 20, 100, 20))
    ruby = popup.findChild(FuriganaText)
    assert ruby is not None
    assert any(t.surface == "本書" and ruby.annotation(t) == "ほんしょ" for t in result.tokens)
    assert all(not ruby.annotation(t) for t in result.tokens if t.surface == "は")
    assert ruby.heightForWidth(150) > ruby.heightForWidth(320)
    popup.close()
