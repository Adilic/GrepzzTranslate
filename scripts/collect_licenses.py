import importlib.metadata
import argparse
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--destination", type=Path, default=root / "dist" / "GrepzzTranslate" / "licenses")
target = parser.parse_args().destination
target.mkdir(parents=True, exist_ok=True)
for distribution in importlib.metadata.distributions():
    for file in distribution.files or []:
        if any(part.lower().startswith(("license", "copying", "notice")) for part in file.parts):
            source = Path(distribution.locate_file(file))
            if source.is_file():
                destination = target / distribution.metadata["Name"] / file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
