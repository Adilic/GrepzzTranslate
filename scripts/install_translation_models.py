"""公式 Argos モデルをローカル配布用に準備する。"""
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
for pair, version in [("en_zh", "1_9"), ("ja_en", "1_1")]:
    url = f"https://argos-net.com/v1/translate-{pair}-{version}.argosmodel"
    archive = root / "build" / "model-downloads" / f"{pair}.argosmodel"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        temporary = archive.with_suffix(".part")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        temporary.replace(archive)
    destination = root / "resources" / "translation" / pair
    with ZipFile(archive) as package:
        for name in package.namelist():
            relative = Path(*Path(name).parts[1:])
            if not relative.parts or ".." in relative.parts or name.endswith("/"):
                continue
            if relative.parts[0] not in {"model", "sentencepiece.model", "metadata.json", "LICENSE", "LICENSE.txt", "README.md"}:
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package.read(name))
    (destination / "provenance.json").write_text(json.dumps({"url": url, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2), encoding="utf-8")
    print(f"Installed {pair}: {archive.stat().st_size:,} bytes", flush=True)
