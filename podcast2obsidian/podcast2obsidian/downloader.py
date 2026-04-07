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
