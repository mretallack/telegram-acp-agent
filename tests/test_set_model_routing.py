#!/usr/bin/env python3
"""Tests for model-switch confirmation routing (group topic vs DM).

Regression test: the confirmation for `\\model <id>` must be sent back to the
same topic/thread it was issued from, not the group's General topic.
"""

from goose_session_acp import GooseSessionACP


class _FakeSession:
    """Minimal session stub supporting set_config_option."""

    def __init__(self):
        self.session_id = "sid"

    def set_config_option(self, config_id, value):
        return {
            "configOptions": [
                {
                    "id": "model",
                    "currentValue": value,
                    "options": [{"value": value, "name": value}],
                }
            ]
        }


class _FakeClient:
    def set_model(self, session_id, model):
        raise AssertionError("should not be called when set_config_option works")


def _bare_session():
    return GooseSessionACP.__new__(GooseSessionACP)


def _with_agent(session, agent_name, thread_id, models):
    session.agents = {
        agent_name: {
            "session": _FakeSession(),
            "client": _FakeClient(),
            "models": models,
            "thread_id": thread_id,
            "pending_output": [],
        }
    }
    session.active_agent = agent_name
    session.suppress_output = False
    session.send_to_telegram = None  # we capture via _send_to_telegram_sync patch
    return session


def test_set_model_confirms_in_same_thread(monkeypatch):
    session = _bare_session()
    _with_agent(
        session,
        "AndroidAuto",
        thread_id=48,
        models={
            "currentModelId": "old",
            "availableModels": [{"modelId": "new-model", "name": "New"}],
        },
    )

    sent = []

    def fake_send(chat_id, text, agent_name=None, thread_id=None):
        sent.append((chat_id, text, agent_name, thread_id))

    monkeypatch.setattr(session, "_send_to_telegram_sync", fake_send)

    session._handle_set_model(
        {"model_id": "new-model", "chat_id": -100, "agent_name": "AndroidAuto"}
    )

    assert sent, "a confirmation should have been sent"
    chat_id, text, agent_name, thread_id = sent[-1]
    assert thread_id == 48, f"expected thread 48, got {thread_id}"
    assert agent_name == "AndroidAuto"
    assert "new-model" in text


def test_set_model_uses_explicit_msg_thread(monkeypatch):
    session = _bare_session()
    _with_agent(
        session,
        "A",
        thread_id=48,
        models={"availableModels": [{"modelId": "m", "name": "m"}]},
    )
    sent = []
    monkeypatch.setattr(
        session,
        "_send_to_telegram_sync",
        lambda chat_id, text, agent_name=None, thread_id=None: sent.append(
            (thread_id, text)
        ),
    )

    session._handle_set_model(
        {"model_id": "m", "chat_id": -100, "agent_name": "A", "thread_id": 99}
    )

    assert sent[-1][0] == 99


def test_set_model_rejects_unknown_model_in_thread(monkeypatch):
    session = _bare_session()
    _with_agent(
        session,
        "A",
        thread_id=7,
        models={"availableModels": [{"modelId": "known", "name": "Known"}]},
    )
    errors = []
    monkeypatch.setattr(
        session,
        "_send_error",
        lambda chat_id, error, agent_name=None, thread_id=None: errors.append(
            (thread_id, error)
        ),
    )

    session._handle_set_model(
        {"model_id": "bogus", "chat_id": -100, "agent_name": "A", "thread_id": 7}
    )

    assert errors and errors[-1][0] == 7
    assert "bogus" in errors[-1][1]
