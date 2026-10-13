"""Text utilities for formatting command output for Telegram."""

import re


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def truncate_message(text: str, max_length: int = 4000) -> str:
    """Truncate message to fit Telegram limits."""
    if len(text) <= max_length:
        return text

    return text[: max_length - 4] + "\n..."


def split_message(text: str, max_length: int = 4000) -> list:
    """Split text into chunks that fit Telegram's message limit.

    Splits on newline boundaries where possible so lines aren't broken mid-way.
    Returns a list with a single element if no split is needed.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        # A single line longer than the limit must be hard-split.
        while len(line) > max_length:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:max_length])
            line = line[max_length:]

        candidate = line if not current else current + "\n" + line
        if len(candidate) > max_length:
            chunks.append(current)
            current = line
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks
