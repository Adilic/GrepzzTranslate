"""Install the optional 229 MB LFM2 model and a pinned Windows CPU runtime.

The model uses the LFM Open License v1.0, not Apache/MIT. See
https://huggingface.co/LiquidAI/LFM2-350M-ENJP-MT-GGUF/blob/main/LICENSE
Only data files are downloaded from Hugging Face. Executables come from the
official llama.cpp release, whose archive SHA256 is verified before extraction.
"""
import argparse
import concurrent.futures
import hashlib
import json
import shutil
import time
import urllib.request
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build/model-downloads/lfm-small"
REPO = "LiquidAI/LFM2-350M-ENJP-MT-GGUF"
REVISION = "889c88c3d3681b4f342ae210a1d2a1369aba0e10"
MODEL = "LFM2-350M-ENJP-MT-Q4_K_M.gguf"
MODEL_SIZE = 229310240
MODEL_SHA256 = "574ef7980dd20d69b494bce82565db5f25124d404be02052bbca62277d33077b"
RUNTIME_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b11540/llama-b11540-bin-win-cpu-x64.zip"
RUNTIME_SHA256 = "85cae1b982145d1b315e56e7343524b301a11f0fdf2c7c9dd973c26daba4b3b5"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url, destination, size, expected, chunk_size=8 * 1024 * 1024):
    """Resume bounded HTTP ranges, then verify the complete file before use."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == size and sha256(destination) == expected:
        print(f"Verified cached {destination.name}", flush=True)
        return
    chunks = destination.parent / (destination.name + ".chunks")
    chunks.mkdir(exist_ok=True)

    def part(start):
        end = min(start + chunk_size, size) - 1
        target = chunks / str(start)
        if target.exists() and target.stat().st_size == end - start + 1:
            return target
        for attempt in range(3):
            try:
                separator = "&" if "?" in url else "?"
                request = urllib.request.Request(url + f"{separator}part={start}&verify={time.time_ns()}",
                                                 headers={"Range": f"bytes={start}-{end}"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{size}":
                        raise RuntimeError("Unexpected HTTP range response")
                    data = response.read(end - start + 2)
                if len(data) != end - start + 1:
                    raise RuntimeError("Truncated download")
                temporary = target.with_suffix(".part")
                temporary.write_bytes(data)
                temporary.replace(target)
                print(f"Downloaded {destination.name}: {end + 1:,}/{size:,}", flush=True)
                return target
            except Exception:
                if attempt == 2:
                    raise
        raise RuntimeError("Download failed")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        parts = list(pool.map(part, range(0, size, chunk_size)))
    temporary = destination.with_suffix(destination.suffix + ".part")
    with temporary.open("wb") as output:
        for path in parts:
            with path.open("rb") as source:
                shutil.copyfileobj(source, output)
    if sha256(temporary) != expected:
        raise RuntimeError(f"Checksum mismatch for {destination.name}; discard its .chunks cache before retrying")
    temporary.replace(destination)


def read_verified(url, expected, git_blob=False):
    with urllib.request.urlopen(url + ("&" if "?" in url else "?") + f"verify={time.time_ns()}", timeout=30) as response:
        data = response.read(200_001)
    if len(data) > 200_000:
        raise RuntimeError("Unexpected metadata size")
    actual = (hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
              if git_blob else hashlib.sha256(data).hexdigest())
    if actual != expected:
        raise RuntimeError("Metadata checksum mismatch")
    return data


def install(destination):
    model_url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{MODEL}"
    download(model_url, CACHE / MODEL, MODEL_SIZE, MODEL_SHA256)
    download(RUNTIME_URL, CACHE / "llama-b11540.zip", 19518979, RUNTIME_SHA256, chunk_size=1024 * 1024)
    base = f"https://huggingface.co/{REPO}/resolve/{REVISION}"
    license_data = read_verified(base + "/LICENSE", "7fb1127cc01c34199fa391322ea59a1d5c8c692e", git_blob=True)
    readme = read_verified(base + "/README.md", "88e10e9efd0c29cc9c3d3d5d749218e9efd98771", git_blob=True)
    runtime_license = read_verified("https://raw.githubusercontent.com/ggml-org/llama.cpp/b11540/LICENSE",
                                    "94f29bbed6a22c35b992c5c6ebf0e7c92f13b836b90f36f461c9cf2f0f1d010d")
    destination.mkdir(parents=True, exist_ok=True)
    metadata = destination / "metadata.json"
    # Disable selection of an existing model while its files are being updated.
    metadata.write_text('{"format_version": 0}', encoding="utf-8")
    runtime = destination / "runtime"
    runtime.mkdir(exist_ok=True)
    selected = {"llama-completion.exe", "llama-completion-impl.dll", "llama-common.dll", "llama.dll",
                "ggml.dll", "ggml-base.dll", "libomp.dll", "LICENSE-LLVM-OpenMP"}
    with ZipFile(CACHE / "llama-b11540.zip") as archive:
        for info in archive.infolist():
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
                raise RuntimeError("Unexpected runtime archive path")
            if path.name in selected or (path.name.startswith("ggml-cpu-") and path.suffix == ".dll"):
                target = runtime / path.name
                temporary = target.with_suffix(target.suffix + ".part")
                temporary.write_bytes(archive.read(info))
                temporary.replace(target)
    temporary = destination / "model.gguf.part"
    shutil.copyfile(CACHE / MODEL, temporary)
    if sha256(temporary) != MODEL_SHA256:
        raise RuntimeError("Installed model checksum mismatch")
    temporary.replace(destination / "model.gguf")
    (destination / "LICENSE").write_bytes(license_data)
    (destination / "LICENSE-llama.cpp").write_bytes(runtime_license)
    (destination / "README-upstream.md").write_bytes(readme)
    files = {str(p.relative_to(destination)).replace("\\", "/"): sha256(p)
             for p in destination.rglob("*") if p.is_file() and p.name not in {"metadata.json", "provenance.json"}}
    provenance = {"model_repository": REPO, "model_revision": REVISION, "model_url": model_url,
                  "model_sha256": MODEL_SHA256, "runtime_url": RUNTIME_URL,
                  "runtime_sha256": RUNTIME_SHA256, "installed_files_sha256": files}
    (destination / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    metadata.write_text(json.dumps({"format_version": 1, "backend": "lfm2-350m-enjp-mt",
                                   "model": "LFM2-350M-ENJP-MT", "quantization": "Q4_K_M",
                                   "license": "LFM Open License v1.0"}, indent=2), encoding="utf-8")
    print(f"Installed optional Japanese model: {destination}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "resources/translation/ja_en_lfm")
    args = parser.parse_args()
    install(args.destination.resolve())
