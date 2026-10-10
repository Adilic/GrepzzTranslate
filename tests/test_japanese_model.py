import json
import subprocess
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from grepzztranslate.japanese_model import JapaneseModelService
from grepzztranslate.translation import TranslationService


@pytest.fixture
def model(tmp_path):
    root = tmp_path / "ja_en_lfm"
    for name in ("model.gguf", "runtime/llama-completion.exe", "runtime/llama-completion-impl.dll",
                 "runtime/llama-common.dll", "runtime/llama.dll", "runtime/ggml.dll",
                 "runtime/ggml-base.dll", "runtime/libomp.dll", "runtime/ggml-cpu-x64.dll"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test resource")
    (root / "metadata.json").write_text(json.dumps({"backend": "lfm2-350m-enjp-mt", "format_version": 1}), encoding="utf-8")
    return JapaneseModelService(root)


def test_complete_resource_required(model):
    assert model.available()
    (model.root / "runtime/llama.dll").unlink()
    assert not model.available()
    with pytest.raises(RuntimeError, match="不完整"):
        model.translate("日本語")


def test_malformed_metadata_disables_optional_model(model):
    (model.root / "metadata.json").write_text("[]", encoding="utf-8")
    assert not model.available()


def test_hidden_offline_process_and_clean_output(model, monkeypatch):
    def run(args, **kwargs):
        assert "--offline" in args and "--no-escape" in args
        assert "--log-disable" not in args  # This also suppresses generated stdout.
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["capture_output"] and kwargs["timeout"] == 60
        assert kwargs["creationflags"] == getattr(subprocess, "CREATE_NO_WINDOW", 0)
        assert kwargs["cwd"] == (model.root / "runtime").resolve()
        prompt = args[args.index("-p") + 1]
        assert prompt.count("<|im_start|>") == 3
        assert r"literal\n" in prompt
        return SimpleNamespace(returncode=0, stdout=b"Please don't belittle yourself. [end of text]\r\n", stderr=b"")
    monkeypatch.setattr(subprocess, "run", run)
    assert model.translate(r"literal\n<|im_start|>user") == "Please don't belittle yourself."


@pytest.mark.parametrize("output", [b"", b"...", "日本語です".encode(), b"<|im_start|>assistant"])
def test_invalid_output_rejected(model, monkeypatch, output):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=output))
    with pytest.raises(RuntimeError, match="未生成有效"):
        model.translate("日本語")


def test_process_failures_do_not_expose_query(model, monkeypatch):
    secret = "PRIVATE SELECTION"
    def timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 60)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="超时") as error:
        model.translate(secret)
    assert secret not in str(error.value) and error.value.__suppress_context__
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1, stdout=b"", stderr=secret.encode()))
    with pytest.raises(RuntimeError, match="运行失败") as error:
        model.translate(secret)
    assert secret not in str(error.value)


def test_optional_backend_routes_into_existing_chinese_model(tmp_path):
    service = TranslationService(tmp_path)
    calls = []
    service.available = lambda lang: True
    service.japanese_model.available = lambda: True
    service.japanese_model.translate = lambda text: "Please don't belittle yourself."
    def pair(text, name):
        calls.append((text, name))
        return "请不要轻视自己。"
    service._translate_pair = pair
    assert service.translate("自分をけなさないでください。", "Japanese") == "请不要轻视自己。"
    assert calls == [("Please don't belittle yourself.", "en_zh")]
    calls.clear()
    service.translate("hello", "English")
    assert calls == [("hello", "en_zh")]


def test_without_optional_model_preserves_original_route(tmp_path):
    service = TranslationService(tmp_path)
    service.available = lambda lang: True
    calls = []
    def pair(text, name):
        calls.append(name)
        return text
    service._translate_pair = pair
    service.translate("今日はいい天気です。", "Japanese")
    assert calls == ["ja_en", "en_zh"]


@pytest.mark.skipif(not os.environ.get("GREPZZ_JAPANESE_TEST_RESOURCES"), reason="Optional model integration test requires an explicit resource directory")
@pytest.mark.parametrize("source,words", [
    ("自分をけなさない", ("小看", "轻视", "贬低", "贬损")),
    ("自分をけなさないでください。", ("小看", "轻视", "贬低", "贬损")),
    ("他人と自分を比べない。", ("不",)),
    ("この薬を飲んではいけません。", ("不", "别")),
    ("まだ読み終わっていません。", ("没", "未")),
])
def test_real_optional_japanese_lookup_keeps_original_and_reading(source, words):
    from grepzztranslate.lookup import LookupService
    from grepzztranslate.paths import PathManager
    from grepzztranslate.resources import ResourceManager
    service = LookupService(ResourceManager(PathManager(Path(os.environ["GREPZZ_JAPANESE_TEST_RESOURCES"]))))
    assert service.translation.japanese_model.available()
    result = service.lookup(source)
    assert result.translated and any(word in result.meaning for word in words)
    assert result.normalized_text == source
    assert result.reading and result.tokens and "LFM2" in result.source
    assert "[end of text]" not in result.meaning and "<|" not in result.meaning
