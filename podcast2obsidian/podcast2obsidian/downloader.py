from dataclasses import dataclass
from pathlib import Path

import yt_dlp


@dataclass
class DownloadResult:
    audio_path: Path
    title: str
    podcast_name: str
    source_url: str
    subtitles: str | None = None


def fetch_subtitles(
    url: str, cookies: Path | None = None, language: str = "ru"
) -> tuple[dict, str] | None:
    """Try to fetch subtitles: first from the original URL, then search YouTube.

    Returns (info_dict, subtitle_text) or None.
    """
    from rich import print as rprint

    # 1. Try original URL
    result = _fetch_subtitles_from_url(url, cookies=cookies, language=language)
    if result:
        return result

    # 2. Get title from original URL to search elsewhere
    opts = {"quiet": True, "no_warnings": True}
    if cookies:
        opts["cookiefile"] = str(cookies)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    title = info.get("title", "")
    if not title:
        return None

    # 3. Search YouTube for the same episode
    rprint(f"  Searching YouTube for: [dim]{title[:60]}...[/dim]")
    yt_result = _search_youtube_subtitles(title, language=language)
    if yt_result:
        # Merge metadata: keep original info but use YouTube subtitles
        yt_info, sub_text = yt_result
        return info, sub_text

    return None


def _fetch_subtitles_from_url(
    url: str, cookies: Path | None = None, language: str = "ru"
) -> tuple[dict, str] | None:
    """Try to fetch subtitles from a specific URL."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [language, "en"],
        "noplaylist": True,
        "skip_download": True,
    }

    # Try with cookies first, then without
    for use_cookies in [cookies, None] if cookies else [None]:
        attempt_opts = dict(opts)
        if use_cookies:
            attempt_opts["cookiefile"] = str(use_cookies)
        try:
            with yt_dlp.YoutubeDL(attempt_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            result = _extract_subtitle_text(info, language)
            if result:
                return result
        except Exception:
            continue

    return None


def _search_youtube_subtitles(
    query: str, language: str = "ru"
) -> tuple[dict, str] | None:
    """Search YouTube for a video matching query and check for subtitles."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [language, "en"],
        "default_search": "ytsearch3",  # top 3 results
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
    except Exception:
        return None

    entries = info.get("entries", [])
    for entry in entries:
        if not entry:
            continue
        result = _extract_subtitle_text(entry, language)
        if result:
            return result
    return None


def _extract_subtitle_text(info: dict, language: str) -> tuple[dict, str] | None:
    """Extract subtitle text from yt-dlp info dict if available."""
    for subs_dict in [info.get("subtitles", {}), info.get("automatic_captions", {})]:
        for lang in [language, "en"]:
            if lang not in subs_dict:
                continue
            formats = subs_dict[lang]
            sub_url = None
            for fmt in formats:
                if fmt.get("ext") in ("vtt", "srt", "json3"):
                    sub_url = fmt["url"]
                    break
            if not sub_url and formats:
                sub_url = formats[0]["url"]
            if sub_url:
                try:
                    with yt_dlp.YoutubeDL({"quiet": True}) as dl:
                        subtitle_text = dl.urlopen(sub_url).read().decode("utf-8")
                    return info, _clean_subtitles(subtitle_text)
                except Exception:
                    continue
    return None


def _clean_subtitles(raw: str) -> str:
    """Strip VTT/SRT timestamps and metadata, return plain text."""
    import re

    # Remove VTT header
    raw = re.sub(r"WEBVTT.*?\n\n", "", raw, flags=re.DOTALL)
    # Remove timestamps (00:00:00.000 --> 00:00:00.000)
    raw = re.sub(r"\d{2}:\d{2}[:\.][\d.,]+\s*-->.*\n", "", raw)
    # Remove SRT sequence numbers
    raw = re.sub(r"^\d+\s*$", "", raw, flags=re.MULTILINE)
    # Remove VTT positioning tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Collapse whitespace
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    # Deduplicate consecutive identical lines (common in VTT)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


def download(
    url: str, output_dir: Path, cookies: Path | None = None, skip_download: bool = False
) -> DownloadResult:
    """Download audio from URL using yt-dlp, return path and metadata."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "quiet": skip_download,
        "no_warnings": True,
        "noprogress": skip_download,
        "noplaylist": True,
    }

    # Try with cookies first, then without
    last_error = None
    for use_cookies in ([cookies, None] if cookies else [None]):
        attempt_opts = dict(opts)
        if use_cookies:
            attempt_opts["cookiefile"] = str(use_cookies)
        try:
            with yt_dlp.YoutubeDL(attempt_opts) as ydl:
                info = ydl.extract_info(url, download=not skip_download)
            last_error = None
            break
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error

    if skip_download:
        # Use cached file from output_dir
        audio_path = next(output_dir.glob("*.*"))
    else:
        audio_path = Path(info["requested_downloads"][0]["filepath"])

    return DownloadResult(
        audio_path=audio_path,
        title=info.get("title", "Unknown"),
        podcast_name=info.get("album")
        or info.get("playlist_title")
        or info.get("uploader", "Unknown"),
        source_url=info.get("webpage_url", url),
    )
