"""Tests for text_utils module."""

import pytest

from text_utils import split_message, strip_ansi, truncate_message


def test_strip_ansi_removes_color_codes():
    text = "\x1b[31mRed text\x1b[0m"
    assert strip_ansi(text) == "Red text"


def test_strip_ansi_removes_multiple_codes():
    text = "\x1b[1m\x1b[32mBold green\x1b[0m\x1b[0m"
    assert strip_ansi(text) == "Bold green"


def test_strip_ansi_handles_plain_text():
    text = "Plain text"
    assert strip_ansi(text) == "Plain text"


def test_truncate_message_under_limit():
    text = "Short message"
    assert truncate_message(text, 100) == "Short message"


def test_truncate_message_over_limit():
    text = "A" * 5000
    result = truncate_message(text, 4000)
    assert len(result) == 4000
    assert result.endswith("\n...")


def test_truncate_message_exact_limit():
    text = "A" * 4000
    assert truncate_message(text, 4000) == text


def test_split_message_short_returns_single_chunk():
    assert split_message("hello", 4000) == ["hello"]


def test_split_message_splits_on_lines():
    text = "\n".join(f"line-{i:04d}" for i in range(1000))
    chunks = split_message(text, 4000)
    assert len(chunks) > 1
    assert all(len(c) <= 4000 for c in chunks)
    # No line should be broken across chunks.
    assert "".join(c.replace("\n", "") for c in chunks) == text.replace("\n", "")


def test_split_message_hard_splits_oversized_line():
    chunks = split_message("x" * 9000, 4000)
    assert len(chunks) == 3
    assert all(len(c) <= 4000 for c in chunks)
    assert "".join(chunks) == "x" * 9000
