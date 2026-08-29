# Telegram Goose Bot Agent Guide

## Project Overview
`telegram-goose-bot` is a Python-based Telegram bot service that acts as a bridge to **Goose CLI**, maintaining persistent conversation contexts, multi-agent management, session persistence, voice message transcription via Whisper, file attachment processing, and real-time tool execution progress updates.

## Core Architecture & Components
- **`telegram_goose_bot.py`**: The main Telegram bot application. Handles Telegram updates, commands (`\agent`, `\cancel`, `\context`, `\compact`, `\model`, `\topic`, etc.), routing messages, and message chunking.
- **`acp_client.py` & `acp_session.py`**: Implementation of the Agent Client Protocol (ACP) JSON-RPC communication layer with Goose CLI, managing session creation, prompts, notifications, permissions, and session cancellation.
- **`goose_session_acp.py`**: Higher-level wrapper managing Goose sessions and agent processes.
- **`context_tracker.py`**: Tracks conversation context usage and warns users when thresholds (80%, 90%) are reached.
- **`acp_utils.py`, `text_utils.py`**: Utility functions for text formatting, splitting long messages, etc.
- **`test_goose_integration.py` & `tests/`**: Comprehensive integration and unit test suites.
- **`Makefile`**: Automation targets for setup, testing, running, and systemd service management.
- **`settings.ini` / `settings.ini.template`**: Configuration file for bot tokens, authorized users, and paths.

## Key Features
1. **Persistent ACP Sessions**: Communicates with Goose via structured JSON-RPC over ACP protocol.
2. **Multi-Agent Management**: Runs multiple Goose CLI processes simultaneously, allowing easy switching (`\agent swap <name>`), creation, and isolation across different project directories.
3. **Group Topics Support**: Maps Telegram forum topics to separate agents.
4. **Voice Message Transcription**: Automatically transcribes voice messages using `faster-whisper`.
5. **Attachments & File Sending**: Supports sending photos, documents, and receiving files from Goose via `SEND_FILE:` markers.
6. **Real-time Progress**: Displays tool execution notifications and status updates as Goose works.
7. **Robust Error Recovery**: Handles timeouts, usage limits, message length limits, and transient network errors gracefully.

## Common Development & Maintenance Commands
- Setup environment: `make setup`
- Run tests: `make test`
- Run bot locally: `make run`
- Manage systemd service: `make install`, `make service-start`, `make service-status`, `make service-logs`, `make service-stop`
