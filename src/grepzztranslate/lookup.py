import logging
import re
import sys

from .dictionary import EnglishDictionaryService, JapaneseDictionaryService
from .language import EnglishLanguageService, JapaneseLanguageService, LanguageDetector, normalize
from .models import LookupResult
from .resources import ResourceManager
from .translation import TranslationService

log = logging.getLogger(__name__)


class LookupService:
    def __init__(self, resources: ResourceManager) -> None:
        self.english = EnglishDictionaryService(resources.dictionary_path("english"))
        self.japanese = JapaneseDictionaryService(resources.dictionary_path("japanese"))
        self.english_language = EnglishLanguageService()
        self.translation = TranslationService(resources.paths.resources / "translation")
        self.japanese_language = None
        self.japanese_error = ""
        try:
            custom = resources.paths.resources / "sudachi" / "system.dic"
            if getattr(sys, "frozen", False) and not custom.is_file():
                raise FileNotFoundError("缺少 resources/sudachi/system.dic，请完整解压发行包。")
            self.japanese_language = JapaneseLanguageService(custom if custom.exists() else None)
        except Exception:
            log.exception("Sudachi initialization failed")
            self.japanese_error = "Sudachi 读音资源不可用，请安装依赖或重新加载资源。"

    def lookup(self, text: str) -> LookupResult:
        normalized = normalize(text)
        language = LanguageDetector().detect(normalized)
        log.info("Detected language: %s; Dictionary lookup", language)
        result = LookupResult(text, normalized, language)
        if not normalized:
            result.message = "No text recognized.\n没有识别到文字，请重新框选完整单词并留少量边距。"
            return result
        if language == "Unknown":
            result.message = "Unsupported language.\n当前支持英语和日语，请检查识别原文。"
            return result
        entry = None
        try:
            if language == "English":
                result.source = self.english.description()
                for candidate in self.english_language.candidates(normalized):
                    entry = self.english.lookup(candidate)
                    if entry:
                        break
            else:
                result.source = self.japanese.description()
                if self.japanese_language:
                    result.tokens = self.japanese_language.analyze(normalized)
                    result.reading = "".join(t.reading if t.reading != "*" else t.surface for t in result.tokens)
                entry = self.japanese.lookup(normalized)
                if not entry and len(result.tokens) == 1:
                    entry = self.japanese.lookup(result.tokens[0].dictionary_form)
        except Exception as exc:
            log.exception("Dictionary lookup failed")
            result.message = str(exc)
            return result
        if entry:
            for field in ("headword", "phonetic", "part_of_speech", "meaning"):
                setattr(result, field, entry.get(field))
            result.reading = result.reading or entry.get("reading")
            log.info("Lookup success")
        elif self.translation.available(language):
            try:
                result.meaning = self.translation.translate(normalized, language)
                result.translated = True
                result.source = "本地离线翻译" + (" · 日→英→中" if language == "Japanese" else " · 英→中")
                log.info("Offline translation complete: %s", language)
            except Exception as exc:
                log.exception("Offline translation failed")
                result.message = str(exc)
        elif language == "English" and len(normalized.split()) > 1:
            words = list(dict.fromkeys(re.findall(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*", normalized)))
            for word in words[:12]:
                component = self.lookup(word)
                if component.meaning:
                    result.components.append(component)
            result.message = "本地词库未收录整个短语/句子。\n以下为逐词释义，不是整句翻译。"
            if not result.components:
                result.message += "\n其中也没有匹配的单词，请检查 OCR 原文或专有名称。"
            if len(words) > 12:
                result.message += "\n本次仅查询前 12 个不同单词。"
            log.info("Phrase lookup: %d component matches", len(result.components))
        else:
            result.message = "No definition found.\n文字已识别，但当前词库未收录。可修正 OCR 文字后重查。"
            if language == "English":
                result.suggestions = self.english.suggest(normalized)
            elif "演示词库" in result.source:
                result.message += "\n日语目前仍是演示词库，读音由 Sudachi 提供。"
            log.info("Lookup failed: no definition")
        if language == "Japanese" and self.japanese_error:
            result.message = "\n".join(filter(None, [result.message, self.japanese_error]))
        return result
