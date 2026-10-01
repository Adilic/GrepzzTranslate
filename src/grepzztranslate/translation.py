"""ネットワークを使わない CPU 翻訳。モデルは初回のみ読み込む。"""
import json
import re
from pathlib import Path


class TranslationService:
    def __init__(self, root: Path):
        self.root = root
        self.models = {}

    def available(self, language: str) -> bool:
        pairs = ["en_zh"] if language == "English" else ["ja_en", "en_zh"]
        return all((self.root / pair / "model" / "model.bin").is_file()
                   and (self.root / pair / "sentencepiece.model").is_file() for pair in pairs)

    def translate(self, text: str, language: str) -> str:
        if len(text) > 1200:
            raise ValueError("选区文字超过 1200 字符，请分段框选，以保证翻译速度。")
        if not self.available(language):
            raise RuntimeError("未安装离线翻译模型，请使用包含 resources/translation 的完整发行版。")
        if language == "Japanese":
            text = self._translate_pair(text, "ja_en")
        return self._translate_pair(text, "en_zh")

    def _translate_pair(self, text: str, pair: str) -> str:
        if pair not in self.models:
            import ctranslate2
            import sentencepiece

            path = self.root / pair
            tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(path / "sentencepiece.model"))
            translator = ctranslate2.Translator(str(path / "model"), device="cpu", compute_type="int8", intra_threads=4)
            metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
            self.models[pair] = (tokenizer, translator, metadata.get("target_prefix", ""))
        tokenizer, translator, prefix = self.models[pair]
        sentences = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s*|\n+", text) if part.strip()]
        tokens = [tokenizer.encode(sentence, out_type=str) for sentence in sentences]
        if any(len(sentence) > 256 for sentence in tokens):
            raise ValueError("单句过长，请缩小选区后重试。")
        results = translator.translate_batch(tokens, target_prefix=[[prefix]] * len(tokens) if prefix else None,
                                             beam_size=4, max_input_length=0, max_decoding_length=512,
                                             replace_unknowns=True, length_penalty=0.2)
        decoded = [tokenizer.decode(result.hypotheses[0]).replace("▁", " ").removeprefix(prefix).strip() for result in results]
        if not all(decoded):
            raise RuntimeError("本次离线翻译未生成结果，请检查识别原文。")
        return " ".join(decoded)
