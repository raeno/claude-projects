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
