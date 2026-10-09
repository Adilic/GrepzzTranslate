import ctypes

import pytest
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from grepzztranslate.config import Config
from grepzztranslate.lookup import LookupService
from grepzztranslate.resources import ResourceManager
from grepzztranslate.selection import SelectionReader, _Input


class Backend:
    window = 123
    revision = 10
    held = False
    copies = 0
    owner_matches = True

    def foreground(self):
        return self.window

    def sequence(self):
        return self.revision

    def owns_copy(self, target):
        return self.owner_matches

    def keys_down(self):
        return self.held

    def copy(self):
        self.copies += 1


class Clipboard:
    def __init__(self):
        self.data = QMimeData()
        self.data.setText("previous clipboard")
        self.data.setHtml("<b>previous clipboard</b>")

    def mimeData(self):
        return self.data

    def text(self):
        return self.data.text()

    def setMimeData(self, data):
        self.data = data


@pytest.fixture
def reader():
    app = QApplication.instance() or QApplication([])
    backend, clipboard, now = Backend(), Clipboard(), [0.0]
    reader = SelectionReader(backend=backend, clipboard=clipboard, clock=lambda: now[0])
    selected, errors = [], []
    reader.selected.connect(selected.append)
    reader.failed.connect(errors.append)
    yield reader, backend, clipboard, now, selected, errors
    reader.cancel()


def test_wait_for_alt_release_and_restore_all_formats(reader):
    r, backend, clipboard, _, selected, errors = reader
    backend.held = True
    r.start()
    r.poll()
    assert backend.copies == 0
    backend.held = False
    r.poll()
    assert backend.copies == 1
    copied = QMimeData()
    copied.setText("  I am reading a book.\n")
    clipboard.setMimeData(copied)
    backend.revision += 1
    r.poll()
    assert selected == ["I am reading a book."] and not errors
    assert clipboard.text() == "previous clipboard"
    assert clipboard.mimeData().html() == "<b>previous clipboard</b>"
    assert not r.active


def test_no_selection_does_not_translate_old_clipboard(reader):
    r, backend, clipboard, now, selected, errors = reader
    r.start()
    r.poll()
    r.poll()
    assert not selected
    now[0] = 2
    r.poll()
    assert errors and not selected
    assert clipboard.text() == "previous clipboard"


def test_window_switch_cancels_without_copying(reader):
    r, backend, _, _, selected, errors = reader
    r.start()
    backend.window = 456
    r.poll()
    assert errors and backend.copies == 0 and not selected


def test_repeated_trigger_does_not_copy_twice(reader):
    r, backend, _, _, _, _ = reader
    r.start()
    r.start()
    r.poll()
    r.poll()
    assert backend.copies == 1


def test_copy_failure_stops_timer(reader):
    r, backend, _, _, selected, errors = reader
    def fail():
        raise RuntimeError("blocked")
    backend.copy = fail
    r.start()
    r.poll()
    assert errors == ["blocked"] and not selected and not r.timer.isActive()


def test_cancel_does_not_overwrite_a_new_clipboard(reader):
    r, backend, clipboard, _, selected, _ = reader
    r.start()
    r.poll()
    clipboard.data.setText("new user copy")
    backend.revision += 1
    r.cancel()
    r.poll()
    assert not selected and clipboard.text() == "new user copy"


def test_native_input_layout_and_reserved_hotkey():
    assert ctypes.sizeof(_Input) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
    with pytest.raises(ValueError, match="划词"):
        Config(capture_hotkey="ALT + 1").validate()


def test_external_clipboard_change_is_not_translated_or_overwritten(reader):
    r, backend, clipboard, _, selected, errors = reader
    r.start()
    r.poll()
    clipboard.data.setText("other application")
    backend.revision += 1
    backend.owner_matches = False
    r.poll()
    assert not selected and errors
    assert clipboard.text() == "other application"


@pytest.mark.parametrize("text", ["qwertyabc", "This is a sentence.", "今日はいい天気です。"])
def test_unlisted_word_and_sentence_use_model(paths, text):
    service = LookupService(ResourceManager(paths))
    calls = []
    service.translation.available = lambda language: True
    def translate(value, language):
        calls.append((value, language))
        return "模型译文"
    service.translation.translate = translate
    result = service.lookup(text)
    assert result.translated and result.meaning == "模型译文"
    assert calls[0][0] == text
    if result.language == "Japanese":
        assert result.tokens and result.reading


def test_known_word_does_not_load_model(paths):
    service = LookupService(ResourceManager(paths))
    def unexpected(*args):
        pytest.fail("Known word should use dictionary")
    service.translation.translate = unexpected
    result = service.lookup("book")
    assert result.meaning and not result.translated
