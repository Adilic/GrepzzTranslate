import argparse
import json
from importlib.resources import files
from pathlib import Path

from .core import summarize


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Count UTF-8 text without external dependencies.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="UTF-8 input file; relative to the working directory")
    source.add_argument("--demo", action="store_true", help="Read the example bundled inside this package")
    args = parser.parse_args(argv)
    try:
        text = (
            files("textstats_kit").joinpath("data", "example.txt").read_text(encoding="utf-8")
            if args.demo else args.input.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(summarize(text), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
