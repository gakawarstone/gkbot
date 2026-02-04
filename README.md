# GKBot

GKBot is an async Telegram bot with a modular feed system, media tooling, and optional AI integrations.

**Features**
- Telegram bot built on `aiogram` 3.
- Modular feed handlers for YouTube, TikTok, Twitch, Reddit, VK, Telegram, Rezka, Kinogo, Shiki, Spotify, Discours, Pornhub, Piokok, Stories, and generic video.
- Media downloading via `yt-dlp`, with async workers and `ffmpeg` support.
- LLM integrations via Gemini and OpenRouter.
- Notion database/page integration.
- Text-to-speech via Edge TTS.
- Wikipedia quote lookup.

**Tech Stack**
- Python 3.13
- `aiogram` 3
- `tortoise-orm` with `asyncpg` (Postgres) and SQLite support
- `yt-dlp` and `ffmpeg`
- `google-generativeai` and OpenAI SDK (OpenRouter)
- `notion-client`
- `edge-tts`
- `uv` and `ruff` for tooling

**Installation**
1. Copy the environment template and fill in required values.

```bash
cp .env.dist .env
```

2. Install dependencies (recommended with `uv`).

```bash
uv sync --all-extras
```

3. Run the bot.

```bash
python bot/main.py
```

**Docker**
1. Create `.env` and set required variables (see `.env.dist`).
2. Start the container.

```bash
docker compose up --build
```

**Configuration**
Required:
- `BOT_TOKEN`
- `ADMIN_IDS`
- Database config via `DB_URL` or `SQLDIALECT` plus `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

Optional integrations:
- `NOTION_API_TOKEN`
- `YOUTUBE_API_KEY`
- `TELEGRAPH_API_KEY`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `API_SERVER_URL`
