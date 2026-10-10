"""Optional local LFM2 Japanese-to-English model; no server or network calls."""
import json
import os
import re
import subprocess
from pathlib import Path


class JapaneseModelService:
    def __init__(self, root: Path):
        self.root = root

    def available(self) -> bool:
        required = ("model.gguf", "runtime/llama-completion.exe", "runtime/llama-completion-impl.dll",
                    "runtime/llama-common.dll", "runtime/llama.dll", "runtime/ggml.dll",
                    "runtime/ggml-base.dll", "runtime/libomp.dll", "runtime/ggml-cpu-x64.dll")
        if not all((self.root / name).is_file() and (self.root / name).stat().st_size for name in required):
            return False
        try:
            metadata = json.loads((self.root / "metadata.json").read_text(encoding="utf-8"))
            return (isinstance(metadata, dict) and metadata.get("backend") == "lfm2-350m-enjp-mt"
                    and metadata.get("format_version") == 1)
        except (OSError, ValueError):
            return False

    def translate(self, text: str) -> str:
        if len(text) > 1200:
            raise ValueError("选区文字超过 1200 字符，请分段选择，以保证翻译速度。")
        if not self.available():
            raise RuntimeError("日语模型资源不完整，请重新安装日语模型。")
        # A selected literal must not introduce chat control tokens.
        literal = text.replace("<|", "< |")
        prompt = ("<|im_start|>system\nTranslate to English.<|im_end|>\n"
                  "<|im_start|>user\n" + literal + "<|im_end|>\n<|im_start|>assistant\n")
        runtime = (self.root / "runtime").resolve()
        args = [str(runtime / "llama-completion.exe"), "-m", str((self.root / "model.gguf").resolve()),
                "-p", prompt, "-no-cnv", "--no-display-prompt", "--no-escape", "--simple-io",
                "--offline", "-c", "4096", "-n", "1024", "-t", "4", "--temp", "0", "--seed", "42"]
        env = os.environ.copy()
        env["GGML_BACKEND_DL_PATH"] = str(runtime)
        try:
            result = subprocess.run(args, cwd=runtime, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=60,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            # TimeoutExpired includes the prompt in its repr; do not leak it to logs.
            raise RuntimeError("本地日语翻译超时，请缩小选区后重试。") from None
        except OSError:
            raise RuntimeError("无法启动本地日语模型，请检查 runtime 文件是否完整。") from None
        if result.returncode:
            raise RuntimeError("本地日语模型运行失败，请重新安装模型运行文件。")
        output = result.stdout.decode("utf-8", errors="strict").strip().removesuffix("[end of text]").strip()
        if not re.search(r"[A-Za-z]", output) or re.search(r"[ぁ-ゖァ-ヺ]|<\|", output):
            raise RuntimeError("本地日语模型未生成有效中间译文，请缩小选区重试。")
        return output
