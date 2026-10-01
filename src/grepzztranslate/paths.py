import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathManager:
    root: Path

    @classmethod
    def discover(cls) -> "PathManager":
        root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
        return cls(root)

    @property
    def resources(self) -> Path:
        return self.root / "resources"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def config(self) -> Path:
        return self.root / "config.json"

    def prepare(self) -> None:
        self.data.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
