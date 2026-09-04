# Nonni 2.2

Nonni is a bilingual Arabic/English Telegram chat bot using Groq's
OpenAI-compatible API and `openai/gpt-oss-120b` by default.

## Current capabilities

- Text chat in Arabic and English
- Per-user conversation history
- User-controlled saved memory
- Topic routing for coding, business, cooking, crypto, and Islamic knowledge
- Per-user rate limiting, request serialization, and temporary-error retries
- Optional Telegram user allowlist
- Commands to clear chat, clear memory, or delete all locally stored user data
- Live web search through Tavily and weather through Open-Meteo
- Image analysis through `qwen/qwen3.6-27b`
- Local text extraction from PDF, DOCX, TXT, CSV, Markdown, and JSON files

Web search requires a Tavily API key. The AI response and vision features use Groq.

## Local setup

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Run `pip install -r requirements.txt`.
4. Copy `app/env.example` to `.env`.
5. Add `TELEGRAM_BOT_TOKEN` and `GROQ_API_KEY` to `.env`.
6. Run `python main.py`.

Do not commit `.env` or the `data/` directory. They are excluded by the root
`.gitignore`.

## Useful settings

- `GROQ_MODEL`: model identifier
- `TAVILY_API_KEY`: key used for live web search
- `GROQ_VISION_MODEL`: image model (`qwen/qwen3.6-27b`)
- `MAX_HISTORY`: maximum stored chat messages per user
- `MAX_MEMORY_ITEMS`: maximum saved memories per user
- `REQUESTS_PER_MINUTE`: per-user AI request limit
- `ALLOWED_USER_IDS`: optional comma-separated Telegram IDs; blank means public

## Commands

- `/start` — help
- `/clear` — delete conversation history
- `/remember <note>` — save a memory
- `/memory` — display saved memories
- `/forget` — delete saved memories
- `/delete_me` — delete all local data for the requesting user
- `/model` — display the configured model and provider without AI guessing
- `/web <question>` — force a live web search
- `/weather <city>` — get current weather and forecast

You can also attach an image or a supported document with an optional caption
explaining what you want Nonni to do with it.

## Data note

Messages and memories are stored in a local SQLite database. The program
restricts its file permissions where the operating system supports it, but the
database contents are not encrypted. Protect the PC account and disk, and avoid
storing highly sensitive information.
