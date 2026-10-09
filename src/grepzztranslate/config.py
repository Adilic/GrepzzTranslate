import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    capture_hotkey: str = "alt+q"
    popup_position: str = "capture"
    ocr_languages: list[str] = field(default_factory=lambda: ["en", "ja"])
    ocr_scale: float = 2.0
    theme: str = "light"
    log_ocr_text: bool = False

    def validate(self) -> None:
        from .hotkey import parse_hotkey

        parse_hotkey(self.capture_hotkey)
        if parse_hotkey(self.capture_hotkey) == parse_hotkey("alt+1"):
            raise ValueError("Alt+1 已用于划词翻译，请为截图选择其他快捷键。")
        if self.popup_position not in {"capture", "cursor"}:
            raise ValueError("popup_position 必须为 capture 或 cursor")
        if not isinstance(self.ocr_languages, list) or not self.ocr_languages or any(x not in ("en", "ja") for x in self.ocr_languages):
            raise ValueError("ocr_languages 必须包含 en 或 ja")
        if isinstance(self.ocr_scale, bool) or not isinstance(self.ocr_scale, (int, float)) or not 1 <= self.ocr_scale <= 4:
            raise ValueError("ocr_scale 必须在 1 到 4 之间")
        if self.theme not in {"dark", "light"} or not isinstance(self.log_ocr_text, bool):
            raise ValueError("theme 或 log_ocr_text 无效")


class ConfigManager:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Config:
        if not self.path.exists():
            config = Config()
            self.save(config)
            return config
        config = Config(**json.loads(self.path.read_text(encoding="utf-8")))
        config.validate()
        return config

    def save(self, config: Config) -> None:
        config.validate()
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.path)
