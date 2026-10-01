import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.unlink(missing_ok=True)
    with closing(sqlite3.connect(temp)) as connection, connection:
        connection.execute("CREATE TABLE entries (headword TEXT PRIMARY KEY COLLATE NOCASE, reading TEXT, phonetic TEXT, part_of_speech TEXT, meaning TEXT)")
        connection.execute("CREATE TABLE forms (form TEXT PRIMARY KEY COLLATE NOCASE, headword TEXT NOT NULL)")
        for item in json.loads(source.read_text(encoding="utf-8")):
            connection.execute("INSERT INTO entries VALUES (?,?,?,?,?)", tuple(item.get(key) for key in ("headword", "reading", "phonetic", "part_of_speech", "meaning")))
            connection.executemany("INSERT INTO forms VALUES (?,?)", [(form, item["headword"]) for form in item.get("forms", [])])
    temp.replace(target)


def main() -> None:
    parser = argparse.ArgumentParser(description="创建小型测试词典，不覆盖已有词库")
    parser.add_argument("--force", action="store_true", help="覆盖已有数据库")
    args = parser.parse_args()
    for language in ("english", "japanese"):
        target = ROOT / "resources" / "dictionaries" / f"{language}.db"
        if target.exists() and not args.force:
            print(f"保持已有词典: {target}")
            continue
        build(ROOT / "resources" / "dictionaries" / f"{language}.demo.json", target)
        print(f"已生成: {target}")


if __name__ == "__main__":
    main()
