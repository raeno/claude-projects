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
@patch("podcast2obsidian.cli.fetch_subtitles", return_value=None)
@patch(
    "podcast2obsidian.cli.get_server_config",
    return_value={"backend": "mlx", "whisper_model": "tiny"},
)
@patch("podcast2obsidian.cli.load_config")
def test_process_runs_full_pipeline(
    mock_config,
    mock_server_cfg,
    mock_fetch_subs,
    mock_download,
    mock_transcribe,
    mock_enrich,
    mock_format,
    mock_save,
    tmp_path,
):
    mock_config.return_value = {
        "vault_path": str(tmp_path),
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
