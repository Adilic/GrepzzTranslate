import sqlite3
import difflib
from contextlib import closing
from pathlib import Path


class DictionaryService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def lookup(self, text: str) -> dict | None:
        if not self.path.is_file():
            raise FileNotFoundError(f"Dictionary is not installed: {self.path.name}")
        with closing(sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM entries WHERE headword = ? COLLATE NOCASE LIMIT 1", (text,)
            ).fetchone()
            if row is None:
                row = connection.execute(
                    "SELECT e.* FROM entries e JOIN forms f ON e.headword=f.headword WHERE f.form=? COLLATE NOCASE LIMIT 1", (text,)
                ).fetchone()
            return dict(row) if row else None

    def description(self) -> str:
        if not self.path.is_file():
            return "词库未安装"
        with closing(sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            exists = connection.execute("SELECT 1 FROM sqlite_master WHERE name='metadata'").fetchone()
            if exists:
                metadata = dict(connection.execute("SELECT key,value FROM metadata"))
                return f"{metadata.get('source', '本地词典')} · {int(metadata.get('entries', 0)):,} 词条"
            count = connection.execute("SELECT count(*) FROM entries").fetchone()[0]
            return f"演示词库 · {count} 词条"

    def suggest(self, text: str) -> list[str]:
        if len(text) < 3 or not text.isascii() or not text.isalnum():
            return []
        with closing(sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            for length in range(min(4, len(text) - 1), 1, -1):
                prefix = text[:length].casefold()
                rows = connection.execute("SELECT headword FROM entries WHERE headword >= ? COLLATE NOCASE AND headword < ? COLLATE NOCASE LIMIT 1500",
                                          (prefix, prefix + "\uffff")).fetchall()
                matches = difflib.get_close_matches(text.casefold(), [row[0] for row in rows], n=3, cutoff=0.78)
                if matches:
                    return matches
        return []


class EnglishDictionaryService(DictionaryService):
    pass


class JapaneseDictionaryService(DictionaryService):
    pass
