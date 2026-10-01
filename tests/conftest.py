import importlib.util
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from grepzztranslate.paths import PathManager


@pytest.fixture(scope="session")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def paths(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("build_demo", root / "scripts" / "build_demo_dictionaries.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    paths = PathManager(tmp_path)
    paths.prepare()
    for language in ("english", "japanese"):
        builder.build(root / "resources" / "dictionaries" / f"{language}.demo.json",
                      paths.resources / "dictionaries" / f"{language}.db")
    return paths
