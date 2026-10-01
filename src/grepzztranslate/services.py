from typing import Protocol


class TranslationService(Protocol):
    def translate(self, text: str, language: str) -> str: ...


class ContextExplanationService(Protocol):
    def explain(self, text: str, context: str) -> str: ...
