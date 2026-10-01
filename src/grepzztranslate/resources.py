import sqlite3
from contextlib import closing

from .paths import PathManager


class ResourceManager:
    def __init__(self, paths: PathManager) -> None:
        self.paths = paths

    def dictionary_path(self, language: str):
        return self.paths.resources / "dictionaries" / f"{language}.db"

    def check_dictionary(self, language: str) -> str:
        path = self.dictionary_path(language)
        if not path.exists():
            return f"{language.title()} dictionary is not installed. 请运行 scripts/build_demo_dictionaries.py。"
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
                connection.execute("SELECT headword, reading, phonetic, part_of_speech, meaning FROM entries LIMIT 1")
                connection.execute("SELECT form, headword FROM forms LIMIT 1")
        except sqlite3.Error as exc:
            return f"{language} dictionary is invalid: {exc}"
        return ""

    def check_english_dictionary(self) -> str:
        return self.check_dictionary("english")

    def check_japanese_dictionary(self) -> str:
        return self.check_dictionary("japanese")

    def check_ocr_models(self) -> list[str]:
        from .ocr import OCRService

        return OCRService.available_languages()
