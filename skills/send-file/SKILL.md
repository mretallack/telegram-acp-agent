---
name: send-file
description: Send a file to the user via Telegram. Use when you need to deliver a generated file, export, or any file to the user.
---

# Send File to User

Send a file to the user via Telegram by outputting the special marker `SEND_FILE:<path>` in your response text.

## Format

```
SEND_FILE:/absolute/path/to/file
```

## Rules

- Path MUST be a raw full absolute path starting with `/` (e.g., `/home/username/...`) — never use relative paths (e.g., `tree-stand/file.png`), `~`, or environment variables like `$HOME`.
- File must exist and be under 50MB
- Output the `SEND_FILE:<path>` line directly in your assistant message text (do not use shell echo)

## Example

```
SEND_FILE:/tmp/report.pdf
```

## When to Use

- User asks you to send/share/deliver a file
- You've generated a file the user needs (PDF, image, export, archive)
- User says "send me", "give me the file", "share that file"

## Important Note on Images & Files

- When a user asks to **send** or **deliver** a file (such as an image render), you must use the `SEND_FILE:<path>` marker. 
- Do **not** rely solely on `read_image` or inline markdown display when the user explicitly asks you to send/deliver a file, as `read_image` only views the image internally in your context rather than delivering the actual file to the user via Telegram.
