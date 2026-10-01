from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
bundle = root / "dist" / "GrepzzTranslate"
if not (bundle / "GrepzzTranslate.exe").exists():
    raise SystemExit("请先运行 scripts/build.ps1")
target = root / "dist" / "GrepzzTranslate-v0.1.5-windows-x64.zip"
with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(bundle.rglob("*")):
        relative = path.relative_to(bundle)
        if relative.parts[0] in {"data", "logs"} or path.suffix == ".log":
            continue
        if path.is_file():
            if relative.as_posix() == "config.json":
                archive.write(root / "config.example.json", "GrepzzTranslate/config.json")
            else:
                archive.write(path, Path("GrepzzTranslate") / relative)
    archive.writestr("GrepzzTranslate/data/", "")
print(target)
