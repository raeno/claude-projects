import re
from datetime import date
from pathlib import Path


def slugify_title(title: str) -> str:
    """Convert title to a filesystem-safe name, preserving Cyrillic."""
    # Remove characters unsafe for filesystems
    slug = re.sub(r'[<>:"/\\|?*]', "", title)
    # Collapse whitespace
    slug = " ".join(slug.split())
    return slug.strip(". ")


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
    esc_title = title.replace('"', '\\"')
    esc_podcast = podcast_name.replace('"', '\\"')
    return f"""---
title: "{esc_title}"
source: "{source_url}"
date_processed: {today}
podcast: "{esc_podcast}"
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
