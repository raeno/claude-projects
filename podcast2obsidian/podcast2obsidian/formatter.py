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
