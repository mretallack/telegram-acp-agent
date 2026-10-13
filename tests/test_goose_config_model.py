#!/usr/bin/env python3
"""Unit tests for config-driven model handling.

Covers the bot's model-switching helpers that defer to Goose's own config
(~/.config/goose/config.yaml) instead of injecting GOOSE_PROVIDER/GOOSE_MODEL
environment variables.
"""

import os
import tempfile

import yaml

import goose_session_acp as g
from goose_session_acp import GooseSessionACP


def _bare_session():
    """Construct GooseSessionACP without running __init__ side effects."""
    return GooseSessionACP.__new__(GooseSessionACP)


def test_parse_config_options_extracts_models_and_modes():
    config_options = [
        {
            "id": "provider",
            "currentValue": "openrouter",
            "options": [{"value": "openrouter", "name": "OpenRouter"}],
        },
        {
            "id": "model",
            "currentValue": "deepseek/deepseek-v4.1-flash",
            "options": [
                {"value": "deepseek/deepseek-v4.1-flash", "name": "DeepSeek V4.1 Flash"},
                {"value": "openai/gpt-5", "name": "GPT-5", "description": "flagship"},
            ],
        },
        {
            "id": "mode",
            "currentValue": "auto",
            "options": [
                {"value": "auto", "name": "auto", "description": "auto approve"},
                {"value": "chat", "name": "chat", "description": "no tools"},
            ],
        },
    ]

    parsed = GooseSessionACP._parse_config_options(config_options)

    assert parsed["models"]["currentModelId"] == "deepseek/deepseek-v4.1-flash"
    assert len(parsed["models"]["availableModels"]) == 2
    assert parsed["models"]["availableModels"][1]["description"] == "flagship"
    assert parsed["modes"]["currentModeId"] == "auto"
    assert [m["id"] for m in parsed["modes"]["availableModes"]] == ["auto", "chat"]


def test_parse_config_options_empty():
    parsed = GooseSessionACP._parse_config_options([])
    assert parsed == {"models": {}, "modes": {}}


def test_apply_config_options_result_updates_agent_data():
    session = _bare_session()
    agent_data = {"models": {"currentModelId": "old"}, "modes": {}}

    session._apply_config_options_result(
        agent_data,
        {
            "configOptions": [
                {
                    "id": "model",
                    "currentValue": "new-model",
                    "options": [{"value": "new-model", "name": "New"}],
                }
            ]
        },
    )

    assert agent_data["models"]["currentModelId"] == "new-model"
    assert agent_data["models"]["availableModels"][0]["modelId"] == "new-model"


def test_set_model_in_goose_config_preserves_other_keys(monkeypatch):
    session = _bare_session()

    original = {
        "GOOSE_TELEMETRY_ENABLED": False,
        "active_provider": "openrouter",
        "providers": {
            "openrouter": {
                "enabled": True,
                "model": "old-model",
                "configured": True,
            }
        },
        "extensions": {"developer": {"enabled": True}},
    }

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "config.yaml")
        with open(path, "w") as f:
            yaml.safe_dump(original, f)

        monkeypatch.setattr(g, "GOOSE_CONFIG_PATH", g.Path(path))

        assert session._set_model_in_goose_config("new-model") is True

        with open(path) as f:
            written = yaml.safe_load(f)

        assert written["active_provider"] == "openrouter"
        assert written["providers"]["openrouter"]["model"] == "new-model"
        # Unrelated config must be preserved.
        assert written["providers"]["openrouter"]["configured"] is True
        assert written["extensions"] == {"developer": {"enabled": True}}


def test_set_model_in_goose_config_without_active_provider(monkeypatch):
    session = _bare_session()

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "config.yaml")
        with open(path, "w") as f:
            yaml.safe_dump({"providers": {}}, f)

        monkeypatch.setattr(g, "GOOSE_CONFIG_PATH", g.Path(path))

        assert session._set_model_in_goose_config("some-model") is False


def test_set_model_in_goose_config_missing_file(monkeypatch):
    session = _bare_session()
    monkeypatch.setattr(
        g, "GOOSE_CONFIG_PATH", g.Path("/nonexistent/goose/config.yaml")
    )
    assert session._set_model_in_goose_config("some-model") is False
