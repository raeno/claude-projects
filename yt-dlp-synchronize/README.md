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

### Download with numbered filenames matching playlist order

```bash
yt-dlp --cookies-from-browser chrome \
  -o "%(playlist_index)s - %(title)s.%(ext)s" \
  "https://app.synchronize.ru/listener/educations/192/cohorts/431/plans/493"
```

## How it works

1. The plugin fetches the lecture page and extracts the Kinescope embed URL from the `data-kinescope-url-value` attribute.
2. It delegates actual download to yt-dlp's built-in `Kinescope` extractor.
3. For plans, it scrapes all lecture links from the plan page and returns them as a playlist.
