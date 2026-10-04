"""開発用の依存関係、辞書、モデル、OCR を読み取り専用で確認する。"""
import importlib
import sqlite3
import struct
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
failures = []


def check(name, action):
    try:
        detail = action()
        print(f"[OK] {name}: {detail}")
    except Exception as exc:
        failures.append(name)
        print(f"[FAIL] {name}: {exc}")


def python_version():
    assert sys.version_info[:2] == (3, 12) and struct.calcsize("P") == 8, "需要 Python 3.12 x64"
    return sys.version.split()[0]


def dictionaries():
    counts = {}
    for language in ("english", "japanese"):
        with sqlite3.connect((root / "resources/dictionaries" / f"{language}.db").as_uri() + "?mode=ro", uri=True) as connection:
            counts[language] = connection.execute("select count(*) from entries").fetchone()[0]
    assert counts["english"] >= 500000 and counts["japanese"] > 0, "词库未安装完整，运行 setup-dev.ps1"
    return counts


def translation():
    from grepzztranslate.translation import TranslationService
    service = TranslationService(root / "resources/translation")
    english = service.translate("beautiful world", "English")
    japanese = service.translate("今日はいい天気です。", "Japanese")
    assert english and japanese, "模型未产生译文"
    return f"英中={english}；日中={japanese}"


def japanese_reading():
    from grepzztranslate.language import JapaneseLanguageService
    return [(t.surface, t.reading) for t in JapaneseLanguageService().analyze("本書")]


def ocr():
    from grepzztranslate.ocr import OCRService
    languages = OCRService.available_languages()
    assert any(x.startswith("en") for x in languages) and any(x.startswith("ja") for x in languages), f"需要安装 Windows 英日 OCR；当前：{languages}"
    return languages


check("Python", python_version)
for module in ("PySide6", "ctranslate2", "sentencepiece", "sudachipy", "grepzztranslate"):
    check(module, lambda name=module: importlib.import_module(name).__file__)
check("词库", dictionaries)
check("日语注音", japanese_reading)
check("离线模型实际推理", translation)
check("Windows OCR", ocr)
print("全部检查通过" if not failures else f"{len(failures)} 项未通过，请查看 docs/DEVELOPMENT.md")
raise SystemExit(bool(failures))
