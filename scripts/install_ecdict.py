import argparse
import csv
import hashlib
import json
import sqlite3
import urllib.request
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/"


def import_dictionary(source: Path, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".building")
    temporary.unlink(missing_ok=True)
    with closing(sqlite3.connect(temporary)) as connection, connection:
        connection.executescript("""
            CREATE TABLE entries (headword TEXT PRIMARY KEY COLLATE NOCASE, reading TEXT,
                phonetic TEXT, part_of_speech TEXT, meaning TEXT);
            CREATE TABLE forms (form TEXT PRIMARY KEY COLLATE NOCASE, headword TEXT NOT NULL);
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        with source.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"word", "translation", "exchange"}.issubset(reader.fieldnames or []):
                raise ValueError("不是有效的 ECDICT CSV 文件")
            for row in reader:
                word = row["word"].strip()
                translation = (row.get("translation") or "").replace("\\n", "\n").strip()
                definition = (row.get("definition") or "").replace("\\n", "\n").strip()
                meaning = translation or ("英文释义：\n" + definition if definition else "")
                if not word or not meaning:
                    continue
                phonetic = (row.get("phonetic") or "").strip()
                pos = " / ".join(part.split(":")[0] + "." for part in (row.get("pos") or "").split("/") if part)
                connection.execute("INSERT OR IGNORE INTO entries VALUES (?,NULL,?,?,?)",
                                   (word, f"/{phonetic}/" if phonetic else None, pos or None, meaning))
                for exchange in (row.get("exchange") or "").split("/"):
                    kind, _, value = exchange.partition(":")
                    if not value or kind == "1":
                        continue
                    if kind == "0":
                        connection.execute("INSERT OR REPLACE INTO forms VALUES (?,?)", (word, value))
                    elif kind in {"p", "d", "i", "3", "r", "t", "s"}:
                        connection.execute("INSERT OR IGNORE INTO forms VALUES (?,?)", (value, word))
        count = connection.execute("SELECT count(*) FROM entries").fetchone()[0]
        if count < 1:
            raise ValueError("词典没有可导入的词条")
        metadata = {"source": "ECDICT", "entries": str(count), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "url": SOURCE + "ecdict.csv"}
        connection.executemany("INSERT INTO metadata VALUES (?,?)", metadata.items())
    temporary.replace(target)
    return metadata


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 ECDICT 并构建本地英语词库；应用运行不联网")
    parser.add_argument("--csv", type=Path, help="使用已下载的 CSV，不联网")
    args = parser.parse_args()
    source = args.csv or ROOT / "data" / "downloads" / "ecdict.csv"
    if not args.csv:
        if not source.exists():
            print("Downloading ECDICT...", flush=True)
            download(SOURCE + "ecdict.csv", source)
        download(SOURCE + "LICENSE", ROOT / "resources" / "licenses" / "ECDICT-LICENSE.txt")
    metadata = import_dictionary(source, ROOT / "resources" / "dictionaries" / "english.db")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
