import sqlite3
from contextlib import closing
from pathlib import Path

from .models import LookupResult


class HistoryRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY, lookup_key TEXT NOT NULL,
                    original_text TEXT NOT NULL, normalized_text TEXT NOT NULL,
                    language TEXT NOT NULL, headword TEXT, reading TEXT, meaning TEXT,
                    lookup_time TEXT NOT NULL, lookup_count INTEGER NOT NULL DEFAULT 1,
                    context_sentence TEXT, book_name TEXT, source_app TEXT,
                    synced INTEGER NOT NULL DEFAULT 0, mastered INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(language, lookup_key)
                )
            """)

    def record(self, result: LookupResult) -> None:
        key = (result.headword or result.normalized_text).casefold()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("""
                INSERT INTO history (lookup_key,original_text,normalized_text,language,headword,reading,meaning,lookup_time)
                VALUES (?,?,?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                ON CONFLICT(language,lookup_key) DO UPDATE SET
                    original_text=excluded.original_text, normalized_text=excluded.normalized_text,
                    headword=excluded.headword, reading=excluded.reading, meaning=excluded.meaning,
                    lookup_time=excluded.lookup_time, lookup_count=history.lookup_count+1, synced=0
            """, (key, result.original_text, result.normalized_text, result.language,
                  result.headword, result.reading, result.meaning))
