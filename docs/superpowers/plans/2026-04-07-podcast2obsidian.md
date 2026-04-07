# podcast2obsidian Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that downloads podcast audio, transcribes it locally, enriches with LLM-extracted theses and references, and saves structured Markdown to an Obsidian vault.

**Architecture:** Linear pipeline of 4 stages (download → transcribe → enrich → save), each implemented as a plain function. Typer CLI as the entry point, TOML config for persistence.

**Tech Stack:** Python 3.11+, Typer, yt-dlp, faster-whisper, OpenAI SDK, Jinja2, tomli/tomli-w

---

## File Map

| File | Responsibility |
|------|---------------|
| `podcast2obsidian/pyproject.toml` | Package metadata, dependencies, CLI entry point |
| `podcast2obsidian/podcast2obsidian/__init__.py` | Package init, version |
| `podcast2obsidian/podcast2obsidian/config.py` | Load, create, update TOML config |
| `podcast2obsidian/podcast2obsidian/downloader.py` | Download audio via yt-dlp, extract metadata |
| `podcast2obsidian/podcast2obsidian/transcriber.py` | Transcribe audio via faster-whisper |
| `podcast2obsidian/podcast2obsidian/enricher.py` | Load prompt template, call OpenAI, parse response |
| `podcast2obsidian/podcast2obsidian/formatter.py` | Assemble Markdown with frontmatter, save to vault |
| `podcast2obsidian/podcast2obsidian/cli.py` | Typer app, `process` and `config` commands |
| `podcast2obsidian/podcast2obsidian/prompts/enrich.md` | Jinja2 prompt template for enrichment |
| `podcast2obsidian/tests/test_config.py` | Config loading/creation tests |
| `podcast2obsidian/tests/test_downloader.py` | Downloader tests |
| `podcast2obsidian/tests/test_transcriber.py` | Transcriber tests |
| `podcast2obsidian/tests/test_enricher.py` | Enricher tests |
| `podcast2obsidian/tests/test_formatter.py` | Formatter tests |
| `podcast2obsidian/tests/test_cli.py` | CLI integration tests |

---

### Task 1: Project Scaffold

**Files:**
- Create: `podcast2obsidian/pyproject.toml`
- Create: `podcast2obsidian/podcast2obsidian/__init__.py`
- Create: `podcast2obsidian/tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "podcast2obsidian"
version = "0.1.0"
description = "Download podcasts, transcribe locally, enrich with LLM, save to Obsidian"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9",
    "yt-dlp>=2024.0",
    "faster-whisper>=1.0",
    "openai>=1.0",
    "jinja2>=3.0",
    "tomli-w>=1.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-tmp-files>=0.0.2",
]

[project.scripts]
podcast2obsidian = "podcast2obsidian.cli:app"
```

- [ ] **Step 2: Create __init__.py files**

`podcast2obsidian/podcast2obsidian/__init__.py`:
```python
__version__ = "0.1.0"
```

`podcast2obsidian/tests/__init__.py`: empty file.

- [ ] **Step 3: Create virtual environment and install**

```bash
cd podcast2obsidian
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: installs successfully, `podcast2obsidian --help` shows Typer default output (will error until cli.py exists — that's fine).

- [ ] **Step 4: Commit**

```bash
git add podcast2obsidian/
git commit -m "feat: scaffold podcast2obsidian project"
```

---

### Task 2: Config Module

**Files:**
- Create: `podcast2obsidian/podcast2obsidian/config.py`
- Create: `podcast2obsidian/tests/test_config.py`

- [ ] **Step 1: Write failing tests for config**

`podcast2obsidian/tests/test_config.py`:
```python
from pathlib import Path
from podcast2obsidian.config import load_config, save_config, DEFAULT_CONFIG


def test_default_config_has_required_keys():
    assert "vault_path" in DEFAULT_CONFIG
    assert "whisper_model" in DEFAULT_CONFIG
    assert "openai_api_key" in DEFAULT_CONFIG
    assert "openai_model" in DEFAULT_CONFIG
    assert "language" in DEFAULT_CONFIG


def test_load_config_returns_defaults_when_no_file(tmp_path):
    config_path = tmp_path / "config.toml"
    config = load_config(config_path)
    assert config == DEFAULT_CONFIG


def test_save_and_load_config_roundtrip(tmp_path):
    config_path = tmp_path / "config.toml"
    custom = {**DEFAULT_CONFIG, "vault_path": "/my/vault", "openai_api_key": "sk-test"}
    save_config(custom, config_path)
    loaded = load_config(config_path)
    assert loaded["vault_path"] == "/my/vault"
    assert loaded["openai_api_key"] == "sk-test"


def test_load_config_merges_with_defaults(tmp_path):
    config_path = tmp_path / "config.toml"
    # Write a partial config (missing some keys)
    import tomli_w
    config_path.write_bytes(tomli_w.dumps({"vault_path": "/partial"}))
    loaded = load_config(config_path)
    assert loaded["vault_path"] == "/partial"
    assert loaded["whisper_model"] == DEFAULT_CONFIG["whisper_model"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd podcast2obsidian
python -m pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'podcast2obsidian.config'`

- [ ] **Step 3: Implement config.py**

`podcast2obsidian/podcast2obsidian/config.py`:
```python
from pathlib import Path
import tomllib
import tomli_w


CONFIG_DIR = Path.home() / ".config" / "podcast2obsidian"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG: dict[str, str] = {
    "vault_path": "",
    "whisper_model": "large-v3",
    "openai_api_key": "",
    "openai_model": "gpt-5.4-mini-2026-03-17",
    "language": "ru",
}


def load_config(path: Path = CONFIG_PATH) -> dict[str, str]:
    """Load config from TOML file, merging with defaults for missing keys."""
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    with open(path, "rb") as f:
        saved = tomllib.load(f)
    return {**DEFAULT_CONFIG, **saved}


def save_config(config: dict[str, str], path: Path = CONFIG_PATH) -> None:
    """Save config to TOML file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_config.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add podcast2obsidian/podcast2obsidian/config.py podcast2obsidian/tests/test_config.py
git commit -m "feat: add config module with TOML load/save"
```

---

### Task 3: Downloader Module

**Files:**
- Create: `podcast2obsidian/podcast2obsidian/downloader.py`
- Create: `podcast2obsidian/tests/test_downloader.py`

- [ ] **Step 1: Write failing tests**

`podcast2obsidian/tests/test_downloader.py`:
```python
from unittest.mock import patch, MagicMock
from pathlib import Path
from podcast2obsidian.downloader import download, DownloadResult


def test_download_result_has_required_fields():
    result = DownloadResult(
        audio_path=Path("/tmp/test.mp3"),
        title="Episode 1",
        podcast_name="My Podcast",
        source_url="https://example.com/ep1",
    )
    assert result.audio_path == Path("/tmp/test.mp3")
    assert result.title == "Episode 1"
    assert result.podcast_name == "My Podcast"
    assert result.source_url == "https://example.com/ep1"


@patch("podcast2obsidian.downloader.yt_dlp.YoutubeDL")
def test_download_calls_ytdlp_and_returns_result(mock_ydl_class, tmp_path):
    # Simulate yt-dlp extracting info and downloading
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)

    mock_ydl.extract_info.return_value = {
        "title": "Episode Title",
        "album": "Podcast Name",
        "webpage_url": "https://example.com/ep",
        "requested_downloads": [{"filepath": str(tmp_path / "audio.mp3")}],
    }

    # Create the fake downloaded file
    (tmp_path / "audio.mp3").write_bytes(b"fake audio")

    result = download("https://example.com/ep", output_dir=tmp_path)

    assert result.title == "Episode Title"
    assert result.podcast_name == "Podcast Name"
    assert result.source_url == "https://example.com/ep"
    assert result.audio_path == tmp_path / "audio.mp3"
    mock_ydl.extract_info.assert_called_once_with("https://example.com/ep", download=True)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_downloader.py -v
```

Expected: `ModuleNotFoundError: No module named 'podcast2obsidian.downloader'`

- [ ] **Step 3: Implement downloader.py**

`podcast2obsidian/podcast2obsidian/downloader.py`:
```python
from dataclasses import dataclass
from pathlib import Path

import yt_dlp


@dataclass
class DownloadResult:
    audio_path: Path
    title: str
    podcast_name: str
    source_url: str


def download(url: str, output_dir: Path) -> DownloadResult:
    """Download audio from URL using yt-dlp, return path and metadata."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    filepath = info["requested_downloads"][0]["filepath"]

    return DownloadResult(
        audio_path=Path(filepath),
        title=info.get("title", "Unknown"),
        podcast_name=info.get("album") or info.get("playlist_title") or info.get("uploader", "Unknown"),
        source_url=info.get("webpage_url", url),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_downloader.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add podcast2obsidian/podcast2obsidian/downloader.py podcast2obsidian/tests/test_downloader.py
git commit -m "feat: add downloader module wrapping yt-dlp"
```

---

### Task 4: Transcriber Module

**Files:**
- Create: `podcast2obsidian/podcast2obsidian/transcriber.py`
- Create: `podcast2obsidian/tests/test_transcriber.py`

- [ ] **Step 1: Write failing tests**

`podcast2obsidian/tests/test_transcriber.py`:
```python
from unittest.mock import patch, MagicMock
from pathlib import Path
from podcast2obsidian.transcriber import transcribe


@patch("podcast2obsidian.transcriber.WhisperModel")
def test_transcribe_returns_joined_text(mock_model_class):
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model

    # Simulate segments as named tuples with .text
    segment1 = MagicMock()
    segment1.text = "Hello world."
    segment2 = MagicMock()
    segment2.text = " This is a test."

    mock_model.transcribe.return_value = ([segment1, segment2], MagicMock())

    result = transcribe(Path("/fake/audio.mp3"), model_name="tiny", language="en")

    assert result == "Hello world. This is a test."
    mock_model_class.assert_called_once_with("tiny")
    mock_model.transcribe.assert_called_once_with(str(Path("/fake/audio.mp3")), language="en")


@patch("podcast2obsidian.transcriber.WhisperModel")
def test_transcribe_uses_default_model(mock_model_class):
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    mock_model.transcribe.return_value = ([], MagicMock())

    transcribe(Path("/fake/audio.mp3"))

    mock_model_class.assert_called_once_with("large-v3")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_transcriber.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement transcriber.py**

`podcast2obsidian/podcast2obsidian/transcriber.py`:
```python
from pathlib import Path

from faster_whisper import WhisperModel


def transcribe(
    audio_path: Path,
    model_name: str = "large-v3",
    language: str = "ru",
) -> str:
    """Transcribe audio file using faster-whisper. Returns plain text."""
    model = WhisperModel(model_name)
    segments, _ = model.transcribe(str(audio_path), language=language)
    return "".join(segment.text for segment in segments).strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_transcriber.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add podcast2obsidian/podcast2obsidian/transcriber.py podcast2obsidian/tests/test_transcriber.py
git commit -m "feat: add transcriber module using faster-whisper"
```

---

### Task 5: Prompt Template & Enricher Module

**Files:**
- Create: `podcast2obsidian/podcast2obsidian/prompts/__init__.py`
- Create: `podcast2obsidian/podcast2obsidian/prompts/enrich.md`
- Create: `podcast2obsidian/podcast2obsidian/enricher.py`
- Create: `podcast2obsidian/tests/test_enricher.py`

- [ ] **Step 1: Create the prompt template**

`podcast2obsidian/podcast2obsidian/prompts/__init__.py`: empty file.

`podcast2obsidian/podcast2obsidian/prompts/enrich.md`:
```markdown
Ты — аналитик контента. Тебе дана транскрипция подкаста. Выполни две задачи:

## Задача 1: Основные тезисы
Выдели 5–10 ключевых тезисов из подкаста. Каждый тезис — одно-два предложения, передающих суть идеи. Пиши на том же языке, что и транскрипция.

## Задача 2: Референсы
Найди все упомянутые работы: книги, фильмы, статьи, тексты, авторов, исследования. Для каждого укажи тип и автора (если упомянут).

## Формат ответа

Ответь СТРОГО в следующем формате, без дополнительного текста:

## Основные тезисы

- Тезис 1
- Тезис 2
...

## Референсы

- **Книга:** "Название" — Автор
- **Фильм:** "Название" (год)
- **Статья:** "Название" — Автор
...

Если референсов нет, напиши "Референсы не обнаружены."

---

## Транскрипция

{{ transcript }}
```

- [ ] **Step 2: Write failing tests for enricher**

`podcast2obsidian/tests/test_enricher.py`:
```python
from unittest.mock import patch, MagicMock
from podcast2obsidian.enricher import enrich, load_prompt, EnrichResult


def test_load_prompt_renders_template():
    rendered = load_prompt("This is a test transcript.")
    assert "This is a test transcript." in rendered
    assert "Основные тезисы" in rendered


def test_enrich_result_fields():
    result = EnrichResult(theses="- Тезис 1", references="- **Книга:** Test")
    assert result.theses == "- Тезис 1"
    assert result.references == "- **Книга:** Test"


@patch("podcast2obsidian.enricher.OpenAI")
def test_enrich_calls_openai_and_parses_response(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    llm_response = """## Основные тезисы

- Тезис первый
- Тезис второй

## Референсы

- **Книга:** "Test Book" — Author"""

    mock_message = MagicMock()
    mock_message.content = llm_response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response

    result = enrich("transcript text", api_key="sk-test", model="gpt-5.4-mini-2026-03-17")

    assert "Тезис первый" in result.theses
    assert "Test Book" in result.references
    mock_client.chat.completions.create.assert_called_once()


@patch("podcast2obsidian.enricher.OpenAI")
def test_enrich_handles_no_references(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    llm_response = """## Основные тезисы

- Тезис единственный

## Референсы

Референсы не обнаружены."""

    mock_message = MagicMock()
    mock_message.content = llm_response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response

    result = enrich("text", api_key="sk-test", model="gpt-5.4-mini-2026-03-17")

    assert "Тезис единственный" in result.theses
    assert "не обнаружены" in result.references
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest tests/test_enricher.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: Implement enricher.py**

`podcast2obsidian/podcast2obsidian/enricher.py`:
```python
from dataclasses import dataclass
from importlib import resources

from jinja2 import Template
from openai import OpenAI


@dataclass
class EnrichResult:
    theses: str
    references: str


def load_prompt(transcript: str) -> str:
    """Load the enrich.md prompt template and render with transcript."""
    prompt_file = resources.files("podcast2obsidian.prompts").joinpath("enrich.md")
    template_text = prompt_file.read_text(encoding="utf-8")
    template = Template(template_text)
    return template.render(transcript=transcript)


def enrich(transcript: str, api_key: str, model: str) -> EnrichResult:
    """Send transcript to OpenAI and parse theses + references from response."""
    prompt = load_prompt(transcript)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.choices[0].message.content

    return _parse_response(content)


def _parse_response(content: str) -> EnrichResult:
    """Parse LLM response into theses and references sections."""
    theses = ""
    references = ""

    sections = content.split("## ")
    for section in sections:
        if section.startswith("Основные тезисы"):
            theses = section.removeprefix("Основные тезисы").strip()
        elif section.startswith("Референсы"):
            references = section.removeprefix("Референсы").strip()

    return EnrichResult(theses=theses, references=references)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_enricher.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add podcast2obsidian/podcast2obsidian/prompts/ podcast2obsidian/podcast2obsidian/enricher.py podcast2obsidian/tests/test_enricher.py
git commit -m "feat: add enricher module with prompt template and OpenAI integration"
```

---

### Task 6: Formatter Module

**Files:**
- Create: `podcast2obsidian/podcast2obsidian/formatter.py`
- Create: `podcast2obsidian/tests/test_formatter.py`

- [ ] **Step 1: Write failing tests**

`podcast2obsidian/tests/test_formatter.py`:
```python
from pathlib import Path
from podcast2obsidian.formatter import format_note, save_note, slugify_title


def test_slugify_title_cyrilllic():
    assert slugify_title("Эпизод 1: Как жить?") == "epizod-1-kak-zhit"


def test_slugify_title_english():
    assert slugify_title("Episode 1: How to live?") == "episode-1-how-to-live"


def test_format_note_contains_all_sections():
    note = format_note(
        title="Test Episode",
        podcast_name="Test Podcast",
        source_url="https://example.com",
        theses="- Thesis 1\n- Thesis 2",
        references='- **Книга:** "Test" — Author',
        transcript="Full transcript text here.",
    )
    assert "title: \"Test Episode\"" in note
    assert "podcast: \"Test Podcast\"" in note
    assert "source: \"https://example.com\"" in note
    assert "## Основные тезисы" in note
    assert "- Thesis 1" in note
    assert "## Референсы" in note
    assert "## Транскрипция" in note
    assert "Full transcript text here." in note


def test_save_note_creates_file(tmp_path):
    content = "---\ntitle: Test\n---\nBody"
    path = save_note(content, "test-episode", tmp_path)
    assert path == tmp_path / "test-episode.md"
    assert path.read_text() == content


def test_save_note_avoids_overwrite(tmp_path):
    (tmp_path / "test.md").write_text("existing")
    path = save_note("new content", "test", tmp_path)
    assert path == tmp_path / "test-1.md"
    assert (tmp_path / "test.md").read_text() == "existing"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_formatter.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement formatter.py**

`podcast2obsidian/podcast2obsidian/formatter.py`:
```python
import re
from datetime import date
from pathlib import Path

# Simple transliteration map for Cyrillic → Latin
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def slugify_title(title: str) -> str:
    """Convert title to a filesystem-safe slug with transliteration."""
    result = []
    for ch in title.lower():
        if ch in _TRANSLIT:
            result.append(_TRANSLIT[ch])
        elif ch.isascii() and ch.isalnum():
            result.append(ch)
        else:
            result.append(" ")
    slug = "-".join("".join(result).split())
    return re.sub(r"-+", "-", slug).strip("-")


def format_note(
    title: str,
    podcast_name: str,
    source_url: str,
    theses: str,
    references: str,
    transcript: str,
) -> str:
    """Assemble the full Markdown note with YAML frontmatter."""
    today = date.today().isoformat()
    return f"""---
title: "{title}"
source: "{source_url}"
date_processed: {today}
podcast: "{podcast_name}"
---

## Основные тезисы

{theses}

## Референсы

{references}

## Транскрипция

{transcript}
"""


def save_note(content: str, slug: str, vault_path: Path) -> Path:
    """Save note to vault, appending -N suffix if file exists."""
    vault_path.mkdir(parents=True, exist_ok=True)
    path = vault_path / f"{slug}.md"
    if not path.exists():
        path.write_text(content)
        return path

    n = 1
    while True:
        path = vault_path / f"{slug}-{n}.md"
        if not path.exists():
            path.write_text(content)
            return path
        n += 1
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_formatter.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add podcast2obsidian/podcast2obsidian/formatter.py podcast2obsidian/tests/test_formatter.py
git commit -m "feat: add formatter module with slugify and Markdown assembly"
```

---

### Task 7: CLI Module

**Files:**
- Create: `podcast2obsidian/podcast2obsidian/cli.py`
- Create: `podcast2obsidian/tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

`podcast2obsidian/tests/test_cli.py`:
```python
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from podcast2obsidian.cli import app

runner = CliRunner()


def test_config_show_displays_config():
    with patch("podcast2obsidian.cli.load_config") as mock_load:
        mock_load.return_value = {
            "vault_path": "/test/vault",
            "whisper_model": "large-v3",
            "openai_api_key": "sk-***",
            "openai_model": "gpt-5.4-mini-2026-03-17",
            "language": "ru",
        }
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "/test/vault" in result.stdout


def test_config_set_updates_value():
    with (
        patch("podcast2obsidian.cli.load_config") as mock_load,
        patch("podcast2obsidian.cli.save_config") as mock_save,
    ):
        mock_load.return_value = {"vault_path": "/old", "whisper_model": "large-v3"}
        result = runner.invoke(app, ["config", "set", "vault_path", "/new/path"])
        assert result.exit_code == 0
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        assert saved_config["vault_path"] == "/new/path"


@patch("podcast2obsidian.cli.save_note")
@patch("podcast2obsidian.cli.format_note")
@patch("podcast2obsidian.cli.enrich")
@patch("podcast2obsidian.cli.transcribe")
@patch("podcast2obsidian.cli.download")
@patch("podcast2obsidian.cli.load_config")
def test_process_runs_full_pipeline(
    mock_config, mock_download, mock_transcribe, mock_enrich, mock_format, mock_save, tmp_path
):
    mock_config.return_value = {
        "vault_path": str(tmp_path),
        "whisper_model": "tiny",
        "openai_api_key": "sk-test",
        "openai_model": "gpt-5.4-mini-2026-03-17",
        "language": "ru",
    }

    mock_download.return_value = MagicMock(
        audio_path=Path("/tmp/audio.mp3"),
        title="Test Episode",
        podcast_name="Test Podcast",
        source_url="https://example.com",
    )
    mock_transcribe.return_value = "Transcript text"
    mock_enrich.return_value = MagicMock(theses="- Thesis 1", references="- Ref 1")
    mock_format.return_value = "---\ntitle: Test\n---\nBody"
    mock_save.return_value = tmp_path / "test-episode.md"

    result = runner.invoke(app, ["process", "https://example.com/ep"])

    assert result.exit_code == 0
    mock_download.assert_called_once()
    mock_transcribe.assert_called_once()
    mock_enrich.assert_called_once()
    mock_format.assert_called_once()
    mock_save.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError` or import errors.

- [ ] **Step 3: Implement cli.py**

`podcast2obsidian/podcast2obsidian/cli.py`:
```python
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel

from podcast2obsidian.config import load_config, save_config
from podcast2obsidian.downloader import download
from podcast2obsidian.transcriber import transcribe
from podcast2obsidian.enricher import enrich
from podcast2obsidian.formatter import format_note, save_note, slugify_title

app = typer.Typer(help="Download podcasts, transcribe, enrich with AI, save to Obsidian.")
config_app = typer.Typer(help="Manage configuration.")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show() -> None:
    """Display current configuration."""
    config = load_config()
    for key, value in config.items():
        display_value = value if "api_key" not in key or not value else value[:8] + "..."
        rprint(f"  [bold]{key}[/bold] = {display_value}")


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    config = load_config()
    if key not in config:
        rprint(f"[red]Unknown key: {key}[/red]")
        raise typer.Exit(1)
    config[key] = value
    save_config(config)
    rprint(f"[green]Set {key} = {value}[/green]")


@app.command()
def process(
    url: str = typer.Argument(help="Podcast episode URL"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Transcription language"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Whisper model name"),
) -> None:
    """Download, transcribe, enrich, and save a podcast episode."""
    config = load_config()

    if not config["vault_path"]:
        config["vault_path"] = typer.prompt("Obsidian vault path")
        save_config(config)
    if not config["openai_api_key"]:
        config["openai_api_key"] = typer.prompt("OpenAI API key")
        save_config(config)

    lang = language or config["language"]
    whisper_model = model or config["whisper_model"]
    vault_path = Path(config["vault_path"]).expanduser()

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Step 1: Download
        rprint("[bold blue]Downloading...[/bold blue]")
        result = download(url, output_dir=Path(tmp_dir))
        rprint(f"  Downloaded: {result.title}")

        # Step 2: Transcribe
        rprint("[bold blue]Transcribing...[/bold blue]")
        transcript = transcribe(result.audio_path, model_name=whisper_model, language=lang)
        rprint(f"  Transcribed: {len(transcript)} characters")

    # Step 3: Enrich
    rprint("[bold blue]Enriching with AI...[/bold blue]")
    enrichment = enrich(transcript, api_key=config["openai_api_key"], model=config["openai_model"])

    # Step 4: Format and save
    slug = slugify_title(result.title)
    note = format_note(
        title=result.title,
        podcast_name=result.podcast_name,
        source_url=result.source_url,
        theses=enrichment.theses,
        references=enrichment.references,
        transcript=transcript,
    )
    saved_path = save_note(note, slug, vault_path)

    # Output
    rprint()
    rprint(Panel(enrichment.theses, title="Основные тезисы", border_style="green"))
    rprint()
    rprint(f"[bold green]Saved to:[/bold green] {saved_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Run all tests**

```bash
python -m pytest -v
```

Expected: all tests pass (16 total).

- [ ] **Step 6: Commit**

```bash
git add podcast2obsidian/podcast2obsidian/cli.py podcast2obsidian/tests/test_cli.py
git commit -m "feat: add CLI with process and config commands"
```

---

### Task 8: README and Final Polish

**Files:**
- Create: `podcast2obsidian/README.md`

- [ ] **Step 1: Create README**

`podcast2obsidian/README.md`:
````markdown
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
````

- [ ] **Step 2: Add .gitignore**

`podcast2obsidian/.gitignore`:
```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
```

- [ ] **Step 3: Run full test suite one more time**

```bash
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add podcast2obsidian/README.md podcast2obsidian/.gitignore
git commit -m "docs: add README and .gitignore"
```
