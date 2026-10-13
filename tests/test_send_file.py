"""Regression tests for SEND_FILE delivery (Issue: silent false success).

Covers:
  - marker parsing: placeholders/fenced examples ignored (Issue B)
  - a valid marker produces exactly one send_document call
  - success is logged only when Telegram returns a message_id
  - missing / non-running loop fails loudly instead of silently succeeding
"""

import asyncio
import logging
from unittest.mock import MagicMock, Mock

import pytest

from goose_session_acp import GooseSessionACP, find_send_file_paths


def _make_session():
    """A GooseSessionACP with Telegram plumbing stubbed out."""
    goose = GooseSessionACP.__new__(GooseSessionACP)
    goose.application = MagicMock()
    goose.send_to_telegram = None
    goose.event_loop = None
    goose._send_to_telegram_sync = Mock()
    return goose


class TestFindSendFilePaths:
    """Issue B: the marker parser must ignore examples/placeholders."""

    def test_plain_marker(self):
        assert find_send_file_paths("SEND_FILE:/tmp/report.pdf") == ["/tmp/report.pdf"]

    def test_marker_embedded_in_prose(self):
        msg = "Here you go!\nSEND_FILE:/tmp/report.pdf\nEnjoy."
        assert find_send_file_paths(msg) == ["/tmp/report.pdf"]

    def test_fenced_example_is_ignored(self):
        msg = "Use the marker like this:\n```\nSEND_FILE:/tmp/example.pdf\n```\n"
        assert find_send_file_paths(msg) == []

    def test_documented_placeholder_is_ignored(self):
        msg = "Format is:\nSEND_FILE:/absolute/path/to/file\n"
        assert find_send_file_paths(msg) == []

    def test_relative_path_is_ignored(self):
        assert find_send_file_paths("SEND_FILE:relative/file.png") == []

    def test_multiple_real_markers_all_returned(self):
        msg = "SEND_FILE:/tmp/a.png\nSEND_FILE:/tmp/b.png"
        assert find_send_file_paths(msg) == ["/tmp/a.png", "/tmp/b.png"]

    def test_empty_and_none_safe(self):
        assert find_send_file_paths("") == []
        assert find_send_file_paths(None) == []


class TestSendFileDelivery:
    """Primary bug: never log success without a confirmed upload."""

    def test_valid_file_calls_send_document_once(self, tmp_path, caplog):
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 test")

        goose = _make_session()
        message = Mock(message_id=12345)
        goose.application.bot.send_document = Mock(
            side_effect=lambda **kw: _awaitable(message)
        )

        loop = asyncio.new_event_loop()
        goose.event_loop = loop
        # Drive the loop in a background thread so run_coroutine_threadsafe runs.
        import threading

        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        try:
            with caplog.at_level(logging.INFO):
                goose._send_file_to_telegram_sync(1, str(f))
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)
            loop.close()

        assert goose.application.bot.send_document.call_count == 1
        assert any(
            "Sent file report.pdf to Telegram" in r.message for r in caplog.records
        )
        # No failure notification was sent to the user.
        goose._send_to_telegram_sync.assert_not_called()

    def test_no_message_id_logs_error_and_notifies_user(self, tmp_path, caplog):
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 test")

        goose = _make_session()
        # send_document returns an object without a message_id -> unconfirmed.
        goose.application.bot.send_document = Mock(
            side_effect=lambda **kw: _awaitable(Mock(spec=[]))
        )

        loop = asyncio.new_event_loop()
        goose.event_loop = loop
        import threading

        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        try:
            with caplog.at_level(logging.INFO):
                goose._send_file_to_telegram_sync(1, str(f))
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)
            loop.close()

        assert not any(
            "Sent file report.pdf to Telegram" in r.message for r in caplog.records
        )
        assert any("without a confirmed upload" in r.message for r in caplog.records)
        goose._send_to_telegram_sync.assert_called_once()
        assert "not confirmed" in goose._send_to_telegram_sync.call_args[0][1]

    def test_missing_loop_fails_loudly(self, tmp_path, caplog):
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 test")

        goose = _make_session()
        goose.event_loop = None  # no loop wired at all

        with caplog.at_level(logging.INFO):
            goose._send_file_to_telegram_sync(1, str(f))

        goose.application.bot.send_document.assert_not_called()
        assert not any(
            "Sent file report.pdf to Telegram" in r.message for r in caplog.records
        )
        goose._send_to_telegram_sync.assert_called_once()
        assert (
            "event loop not available" in goose._send_to_telegram_sync.call_args[0][1]
        )

    def test_non_running_loop_fails_loudly(self, tmp_path, caplog):
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 test")

        goose = _make_session()
        loop = asyncio.new_event_loop()  # created but never running
        goose.event_loop = loop
        try:
            with caplog.at_level(logging.INFO):
                goose._send_file_to_telegram_sync(1, str(f))
        finally:
            loop.close()

        goose.application.bot.send_document.assert_not_called()
        assert not any(
            "Sent file report.pdf to Telegram" in r.message for r in caplog.records
        )
        goose._send_to_telegram_sync.assert_called_once()

    def test_upload_exception_notifies_user(self, tmp_path, caplog):
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 test")

        goose = _make_session()

        async def boom(**kwargs):
            raise RuntimeError("network down")

        goose.application.bot.send_document = Mock(side_effect=boom)

        loop = asyncio.new_event_loop()
        goose.event_loop = loop
        import threading

        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        try:
            with caplog.at_level(logging.INFO):
                goose._send_file_to_telegram_sync(1, str(f))
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)
            loop.close()

        assert not any(
            "Sent file report.pdf to Telegram" in r.message for r in caplog.records
        )
        goose._send_to_telegram_sync.assert_called_once()
        assert "Failed to send file" in goose._send_to_telegram_sync.call_args[0][1]

    def test_missing_file_notifies_user(self, tmp_path):
        goose = _make_session()
        goose._send_file_to_telegram_sync(1, str(tmp_path / "nope.pdf"))

        goose._send_to_telegram_sync.assert_called_once()
        assert "File not found" in goose._send_to_telegram_sync.call_args[0][1]


async def _awaitable(value):
    return value


class TestTokenRedaction:
    """Hygiene: bot tokens must never reach log output in cleartext."""

    def test_token_is_redacted_in_log_records(self):
        import logging

        from telegram_goose_bot import _RedactTokenFilter

        token = "8222736625:AAFakeTokenValue1234567890abcdef"
        record = logging.LogRecord(
            name="httpx",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=f"HTTP Request: POST https://api.telegram.org/bot{token}/sendDocument",
            args=(),
            exc_info=None,
        )
        _RedactTokenFilter().filter(record)
        assert token not in record.getMessage()
        assert "<redacted>" in record.getMessage()

    def test_token_redacted_in_lazy_args(self):
        import logging

        from telegram_goose_bot import _RedactTokenFilter

        token = "8222736625:AAFakeTokenValue1234567890abcdef"
        record = logging.LogRecord(
            name="httpx",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="URL: %s",
            args=(f"https://api.telegram.org/bot{token}/getMe",),
            exc_info=None,
        )
        _RedactTokenFilter().filter(record)
        assert token not in record.getMessage()

    def test_lazy_formatting_still_works(self):
        """Redaction must not break %d/%s lazy formatting."""
        import logging

        from telegram_goose_bot import _RedactTokenFilter

        record = logging.LogRecord(
            name="t",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Sent file %s (message_id=%d)",
            args=("x.png", 42),
            exc_info=None,
        )
        _RedactTokenFilter().filter(record)
        assert record.getMessage() == "Sent file x.png (message_id=42)"

    def test_redacts_token_embedded_in_msg(self):
        import logging

        from telegram_goose_bot import _RedactTokenFilter

        token = "8222736625:AAFakeTokenValue1234567890abcdef"
        record = logging.LogRecord(
            name="httpx",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=f"POST https://api.telegram.org/bot{token}/sendDocument",
            args=(),
            exc_info=None,
        )
        _RedactTokenFilter().filter(record)
        assert token not in record.getMessage()
