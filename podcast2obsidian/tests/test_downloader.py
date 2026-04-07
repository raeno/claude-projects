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
