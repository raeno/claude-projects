# podcast2obsidian

CLI tool that downloads podcast episodes, transcribes them locally, enriches with AI-extracted theses and references, and saves structured Markdown notes to your Obsidian vault.

## Install

```bash
git clone <repo>
cd podcast2obsidian
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Setup

On first run, you'll be prompted for:
- **Obsidian vault path** — folder where notes are saved
- **OpenAI API key** — for LLM enrichment

Or configure manually:

```bash
podcast2obsidian config set vault_path ~/Obsidian/Vault/Podcasts
podcast2obsidian config set openai_api_key sk-...
```

## Usage

```bash
# Process a podcast episode
podcast2obsidian process "https://music.yandex.ru/album/18954362/track/123"

# Override language or whisper model
podcast2obsidian process "URL" --language en --model medium

# View config
podcast2obsidian config show
```

## Output

Each episode becomes a Markdown file with:
- YAML frontmatter (title, source, date, podcast name)
- **Основные тезисы** — key takeaways extracted by AI
- **Референсы** — books, films, articles, authors mentioned
- **Транскрипция** — full transcript

Key theses are also printed to the terminal on completion.

## Config

Stored at `~/.config/podcast2obsidian/config.toml`:

```toml
vault_path = "~/Obsidian/Vault/Podcasts"
whisper_model = "large-v3"
openai_api_key = "sk-..."
openai_model = "gpt-5.4-mini-2026-03-17"
language = "ru"
```
