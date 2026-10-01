import csv
import importlib.util
from pathlib import Path

import pytest

from grepzztranslate.dictionary import EnglishDictionaryService


def importer():
    path = Path(__file__).resolve().parents[1] / "scripts" / "install_ecdict.py"
    spec = importlib.util.spec_from_file_location("install_ecdict", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.import_dictionary


def test_import_real_format_and_exchange(tmp_path):
    source = tmp_path / "sample.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["word", "translation", "definition", "phonetic", "pos", "exchange"])
        writer.writeheader()
        writer.writerows([
            {"word": "windows", "translation": "n. 微软操作系统", "phonetic": "windouz"},
            {"word": "perceive", "translation": "v. 察觉\\n理解", "exchange": "p:perceived/d:perceived/i:perceiving", "pos": "v:100"},
            {"word": "WINDOWS", "translation": "duplicate"},
            {"word": "test", "definition": "an assessment"},
        ])
    target = tmp_path / "english.db"
    metadata = importer()(source, target)
    dictionary = EnglishDictionaryService(target)
    assert metadata["entries"] == "3"
    assert dictionary.lookup("Windows")["meaning"] == "n. 微软操作系统"
    assert dictionary.lookup("perceived")["headword"] == "perceive"
    assert dictionary.lookup("perceiving")["meaning"] == "v. 察觉\n理解"
    assert dictionary.lookup("test")["meaning"].startswith("英文释义")
    assert "ECDICT" in dictionary.description()


def test_bad_import_keeps_existing_dictionary(tmp_path):
    target = tmp_path / "english.db"
    target.write_bytes(b"original")
    source = tmp_path / "invalid.csv"
    source.write_text("not,a,dictionary", encoding="utf-8")
    with pytest.raises(ValueError):
        importer()(source, target)
    assert target.read_bytes() == b"original"
