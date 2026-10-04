def summarize(text: str) -> dict[str, int]:
    """Count Unicode code points, logical lines, and whitespace-separated words.

    A final newline does not create an extra line. Words are not linguistic
    tokens: Chinese and Japanese require a different segmentation algorithm.
    """
    return {
        "characters": len(text),
        "lines": len(text.splitlines()),
        "words": len(text.split()),
    }
