import re
import unicodedata

from .models import Token

JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


class LanguageDetector:
    def detect(self, text: str) -> str:
        japanese = len(JAPANESE.findall(text))
        latin = len(re.findall(r"[A-Za-z]", text))
        if japanese and japanese >= latin:
            return "Japanese"
        if latin:
            return "English"
        return "Japanese" if japanese else "Unknown"


def hiragana(text: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


class JapaneseLanguageService:
    def __init__(self, dictionary_path=None) -> None:
        from sudachipy import dictionary, tokenizer

        self.dictionary = dictionary.Dictionary(dict=str(dictionary_path)) if dictionary_path else dictionary.Dictionary()
        self.tokenizer = self.dictionary.create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

    def analyze(self, text: str) -> list[Token]:
        return [Token(m.surface(), hiragana(m.reading_form()), m.dictionary_form(), ", ".join(p for p in m.part_of_speech() if p != "*"))
                for m in self.tokenizer.tokenize(text, self.mode)]


class EnglishLanguageService:
    def candidates(self, text: str) -> list[str]:
        word = text.casefold().strip(" \"“”‘’.,!?;:()[]")
        candidates = [word]
        if word.endswith("ies"):
            candidates.append(word[:-3] + "y")
        if word.endswith("ied"):
            candidates.append(word[:-3] + "y")
        for suffix in ("ing", "ed"):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[:-len(suffix)]
                candidates.extend([stem + "e", stem])
                if len(stem) > 2 and stem[-1] == stem[-2]:
                    candidates.append(stem[:-1])
        if word.endswith("es"):
            candidates.append(word[:-2])
        if word.endswith("s") and not word.endswith("ss"):
            candidates.append(word[:-1])
        return list(dict.fromkeys(candidates))
