# podcast2obsidian — Design Spec

## Purpose

CLI tool that takes a podcast URL, downloads the audio, transcribes it locally, enriches the transcript with key theses and references via OpenAI, and saves a structured Markdown note into an Obsidian vault.

## Architecture

Linear pipeline with 4 stages:

```
URL → [download] → audio → [transcribe] → text → [enrich] → theses + refs → [save] → .md in vault
```

Each stage is a plain function. Data flows sequentially through the pipeline. No plugin system, no parallelism — simple and debuggable.

## Project Structure

```
podcast2obsidian/
├── pyproject.toml
├── README.md
└── podcast2obsidian/
    ├── __init__.py
    ├── cli.py              # Typer app, entry point
    ├── config.py           # Load/create TOML config
    ├── downloader.py       # yt-dlp wrapper
    ├── transcriber.py      # faster-whisper local transcription
    ├── enricher.py         # OpenAI API call, loads prompt template
    ├── formatter.py        # Assemble .md with YAML frontmatter
    └── prompts/
        └── enrich.md       # Jinja2-templated prompt for thesis/reference extraction
```

## Tech Stack

- **Language:** Python 3.11+
- **CLI framework:** Typer
- **Audio download:** yt-dlp (supports Yandex Music, Apple Podcasts, YouTube, etc.)
- **Transcription:** faster-whisper (local, model `large-v3` by default)
- **LLM enrichment:** OpenAI API (model `gpt-5.4-mini-2026-03-17` by default)
- **Config format:** TOML
- **Prompt templating:** Jinja2 variables in Markdown files, loaded via `importlib.resources`

## Config

Location: `~/.config/podcast2obsidian/config.toml`

```toml
vault_path = "~/Obsidian/MyVault/Podcasts"
whisper_model = "large-v3"
openai_api_key = "sk-..."
openai_model = "gpt-5.4-mini-2026-03-17"
language = "ru"
```

On first run without config, the CLI interactively asks for `vault_path` and `openai_api_key`, then creates the file with defaults for the rest.

## CLI Interface

```bash
# Main command — process a single podcast episode
podcast2obsidian process "https://music.yandex.ru/album/18954362/track/123"

# Override defaults
podcast2obsidian process "URL" --language ru --model large-v3

# Config management
podcast2obsidian config show
podcast2obsidian config set vault_path ~/Notes/Podcasts
```

## Output Format

### Terminal output

On completion, prints the "Key Theses" block and the path to the saved file.

### Saved .md file

```markdown
---
title: "Episode Title"
source: "https://..."
date_processed: 2026-04-07
podcast: "Podcast Name"
---

## Основные тезисы

- Thesis 1
- Thesis 2
- ...

## Референсы

- **Книга:** "Title" — Author
- **Статья:** "Title" — Author
- **Фильм:** "Title" (year)
- ...

## Транскрипция

Full transcription text...
```

## Prompt Template

`prompts/enrich.md` — Markdown file with Jinja2 variables:

- `{{ transcript }}` — full transcription text
- Prompt instructs the LLM to extract key theses and references (books, films, articles, authors)
- Response format is structured so `enricher.py` can parse it into sections

## Pipeline Details

### 1. Download (`downloader.py`)

- Uses yt-dlp Python API to download audio
- Extracts metadata: title, podcast name, URL
- Saves to a temp directory (cleaned up after pipeline completes)
- Returns: audio file path + metadata dict

### 2. Transcribe (`transcriber.py`)

- Loads faster-whisper model (configurable, default `large-v3`)
- Transcribes with `language` from config
- Returns: plain text transcription (no timestamps in output)

### 3. Enrich (`enricher.py`)

- Loads `prompts/enrich.md` via `importlib.resources`
- Renders Jinja2 template with transcript
- Sends to OpenAI API (model from config)
- Parses response into: theses list, references list
- Returns: structured enrichment data

### 4. Format & Save (`formatter.py`)

- Assembles YAML frontmatter from metadata
- Combines theses, references, and transcription into Markdown
- Sanitizes title for filename (transliteration or slug)
- Saves to `{vault_path}/{filename}.md`
- Returns: file path

## Error Handling

- **yt-dlp fails:** Clear error message with the URL, suggest checking cookies
- **Whisper model not downloaded:** Auto-downloads on first use (faster-whisper handles this)
- **OpenAI API error:** Show error, save the note without enrichment (transcription is still valuable)
- **Config missing:** Interactive setup on first run

## Dependencies

```
typer >= 0.9
yt-dlp >= 2024.0
faster-whisper >= 1.0
openai >= 1.0
jinja2 >= 3.0
tomli >= 2.0        # for Python < 3.11 TOML reading
tomli-w >= 1.0      # for TOML writing
rich >= 13.0        # Typer's pretty printing
```
