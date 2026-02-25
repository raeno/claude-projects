# yt-dlp plugin for synchronize.ru

A [yt-dlp](https://github.com/yt-dlp/yt-dlp) extractor plugin for [synchronize.ru](https://app.synchronize.ru) — a Rails/Turbo LMS platform. Videos are hosted on [Kinescope](https://kinescope.io).

## Supported URLs

| Type | URL pattern |
|------|-------------|
| Single lecture | `https://app.synchronize.ru/listener/educations/{ed}/cohorts/{co}/plans/{pl}/lectures/{id}` |
| Full plan (playlist) | `https://app.synchronize.ru/listener/educations/{ed}/cohorts/{co}/plans/{id}` |

## Installation

Copy (or symlink) the plugin into yt-dlp's plugin directory:

```bash
mkdir -p ~/.config/yt-dlp/plugins/yt_dlp_plugins/extractor
cp yt_dlp_plugins/extractor/synchronize.py \
   ~/.config/yt-dlp/plugins/yt_dlp_plugins/extractor/synchronize.py
```

Verify it loaded:

```bash
yt-dlp --list-extractors | grep -i synchronize
```

You should see `synchronize:lecture` and `synchronize:plan`.

## Authentication

synchronize.ru requires a valid session. Pass your browser cookies with:

```bash
# From Chrome (recommended)
yt-dlp --cookies-from-browser chrome "URL"

# Or export cookies to a file first
yt-dlp --cookies cookies.txt "URL"
```

If you are not authenticated, yt-dlp will print an error message with a hint.

## Usage examples

### Download a single lecture

```bash
yt-dlp --cookies-from-browser chrome \
  "https://app.synchronize.ru/listener/educations/192/cohorts/431/plans/493/lectures/166"
```

### Download a full plan (all lectures as a playlist)

```bash
yt-dlp --cookies-from-browser chrome \
  "https://app.synchronize.ru/listener/educations/192/cohorts/431/plans/493"
```

### Download with section prefix in filename

Plans are divided into numbered chapters (e.g. "1. Перед началом курса"). Use `%(chapter)s` to include the section name in the filename:

```bash
yt-dlp --cookies-from-browser chrome \
  -o "%(playlist_index)02d %(chapter)s - %(title)s.%(ext)s" \
  "https://app.synchronize.ru/listener/educations/192/cohorts/431/plans/493"
```

Example output:
```
01 1. Перед началом курса - Перед началом курса.mp4
02 2. Конструкция: почему здания не падают - 1. Конструкция.mp4
03 2. Конструкция: почему здания не падают - 2. ГУМ vs Дом Наркомфина.mp4
...
```

## How it works

1. The plugin fetches the lecture page and extracts the Kinescope embed URL from the `data-kinescope-url-value` attribute.
2. It fetches the kinescope.io player page and extracts the HLS stream from the embedded `playerOptions` JSON.
3. For plans, it parses `<section id="chapter-N">` blocks to extract chapters in order, attaching `chapter` and `chapter_number` metadata to each lecture entry.
