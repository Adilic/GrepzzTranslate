from dataclasses import dataclass, field


@dataclass(frozen=True)
class Token:
    surface: str
    reading: str
    dictionary_form: str
    part_of_speech: str


@dataclass
class LookupResult:
    original_text: str
    normalized_text: str
    language: str
    headword: str | None = None
    reading: str | None = None
    phonetic: str | None = None
    part_of_speech: str | None = None
    meaning: str | None = None
    tokens: list[Token] = field(default_factory=list)
    message: str = ""
    source: str = ""
    components: list["LookupResult"] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    translated: bool = False
