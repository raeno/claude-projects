# podcast2obsidian

CLI + Telegram bot that downloads podcast episodes, transcribes them locally, enriches with AI-extracted theses and references, and saves structured Markdown notes to your Obsidian vault.

## Features

- **Subtitle fast path** — checks for existing subtitles (YouTube auto-captions) before downloading audio
- **Dual transcription backend** — MLX (Apple Silicon GPU) or faster-whisper (CPU)
- **LLM enrichment** — extracts key theses and references (books, films, articles, authors)
- **Paragraph splitting** — breaks transcription by pauses (>1.5s gap)
- **Telegram bot** — send a URL, get back a .md file with status updates
- **Task queue** — SQLite-based persistent queue with history per user
- **Cookie management** — per-domain cookies, uploadable via Telegram
- **Audio caching** — skips re-download for same URL
- **Server profiles** — auto-detects hardware (Apple Silicon / CPU), configurable via `P2O_SERVER`

## Install

```bash
# With uv (recommended)
make install          # auto-detects: mlx on Apple Silicon, cpu on Linux
make install-dev      # + dev tools (pytest, ruff)
make install-bot      # cpu + bot + dev

# Manual
pip install -e ".[mlx]"      # Apple Silicon
pip install -e ".[cpu]"      # CPU server
pip install -e ".[cpu,bot]"  # CPU + Telegram bot
```

## CLI Usage

```bash
# Process a podcast episode
podcast2obsidian process "https://www.youtube.com/watch?v=..."

# Override language or whisper model
podcast2obsidian process "URL" --language en --model medium

# With cookies
podcast2obsidian process "URL" --cookies cookies.txt

# Config
podcast2obsidian config show
podcast2obsidian config set vault_path ~/Obsidian/Vault/Podcasts
```

## Telegram Bot

### Setup

```env
# .env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USERS=123456,789012
OPENAI_API_KEY=sk-...
P2O_SERVER=new_server
```

### Run

```bash
make bot                    # local
docker compose up -d        # Docker
```

### Commands

| Command | Description |
|---------|-------------|
| Send URL | Process podcast episode |
| `/cancel` | Cancel pending/active tasks |
| `/history` | Last 10 processed episodes |
| `/cookies` | List available cookies |
| Send file + caption | Upload cookies (caption = domain, e.g. `yandex`) |

### Status updates

Bot edits one message with progress: `⏳ В очереди` → `📥 Скачиваю...` → `🎙 Транскрибирую...` → `🤖 Обогащаю...` → `✅ Готово!` + sends .md file.

## Docker

Image auto-built via GitHub Actions on push to main.

```yaml
# docker-compose.yml
services:
  bot:
    image: ghcr.io/raeno/podcast2obsidian:latest
    env_file: .env
    volumes:
      - ./cookies:/app/cookies
      - bot-data:/root/.local/share/podcast2obsidian
      - bot-cache:/root/.cache/podcast2obsidian
    restart: unless-stopped
```

```bash
docker compose pull && docker compose up -d   # deploy/update
docker compose logs -f                         # logs
```

## Config

Stored at `~/.config/podcast2obsidian/config.toml`. All values can be set via `.env`:

| Config key | Env variable | Description |
|-----------|-------------|-------------|
| `vault_path` | `OBSIDIAN_VAULT_PATH` | Obsidian vault folder |
| `openai_api_key` | `OPENAI_API_KEY` | LLM API key |
| `openai_model` | — | Default: `gpt-5.4-mini-2026-03-17` |
| `language` | — | Transcription language (default: `ru`) |
| `hf_token` | `HF_TOKEN` | HuggingFace token for model download |
| `server` | `P2O_SERVER` | Server profile name |
| `telegram_bot_token` | `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `telegram_allowed_users` | `TELEGRAM_ALLOWED_USERS` | Comma-separated user IDs |

### Server Profiles

| Profile | Backend | Model | Details |
|---------|---------|-------|---------|
| `mac_m2_max` | mlx | large-v3 | Apple Silicon GPU |
| `new_server` | faster-whisper | large-v3 | CPU, int8, 6 threads |
| (auto) | — | — | Detects Apple Silicon → mlx, else CPU |

## Output Format

```markdown
---
title: "Episode Title"
source: "https://..."
date_processed: 2026-04-08
podcast: "Podcast Name"
---

## Основные тезисы
- ...

## Референсы
- **Книга:** "Title" — Author
- ...

## Транскрипция
Paragraphed text split by pauses...
```

## Known Issues

See [TODO.md](TODO.md) for details.

- **YouTube on VPS** — "Sign in to confirm you're not a bot" from datacenter IPs. Needs residential IP (home server) or proxy.
- **Yandex Music outside RU** — HTTP 451 geo-block. Needs RU IP or proxy.
- **yt-dlp Yandex Music patch** — protocol-relative URL bug (yt-dlp/yt-dlp#15087), applied locally in venv.

## Development

```bash
make test       # run tests
make lint       # ruff check
make format     # ruff format
```
