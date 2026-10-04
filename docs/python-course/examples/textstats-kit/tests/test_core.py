import json
import subprocess
import sys
from importlib.resources import files

from textstats_kit import summarize


def test_empty_text():
    assert summarize("") == {"characters": 0, "lines": 0, "words": 0}


def test_whitespace_and_final_newline():
    assert summarize("one two\nthree\n") == {"characters": 14, "lines": 2, "words": 3}


def test_unicode_and_word_definition():
    assert summarize("你好 世界") == {"characters": 5, "lines": 1, "words": 2}


def test_cli_reads_external_utf8_file(tmp_path):
    path = tmp_path / "输入 文本.txt"
    path.write_text("one two\nthree\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "textstats_kit", "--input", str(path)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == summarize("one two\nthree\n")


def test_cli_demo_from_unrelated_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "textstats_kit", "--demo"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    expected = files("textstats_kit").joinpath("data", "example.txt").read_text(encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == summarize(expected)


def test_missing_file_has_error_exit(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "textstats_kit", "--input", "missing.txt"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert not result.stdout
    assert result.stderr
