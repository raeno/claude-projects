# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal collection of Claude Code projects and tools. Each subdirectory is an independent project with its own README and structure.

## Commit Convention

All commit messages MUST be prefixed with the project name in square brackets:

```
[podcast2obsidian] feat: add paragraph splitting by pause detection
[yt-dlp-synchronize] fix: handle expired session token
[zarianka.ru] chore: update dependencies
```

For changes outside any project (root CLAUDE.md, README, etc.):

```
[repo] docs: update project list
```

## Projects

- **`podcast2obsidian/`** — CLI tool: download podcasts, transcribe locally (mlx/faster-whisper), enrich with LLM (theses + references), save to Obsidian vault
- **`yt-dlp-synchronize/`** — yt-dlp extractor plugin for synchronize.ru (Rails/Turbo LMS, videos hosted on Kinescope)
- **`zarianka.ru/`** — Pottery studio website (Astro)
- **`crossover-patch/`** — Crossover patching utilities
- **`iphotos-cleanup/`** — CLI: find photos imported by junk apps (carsharing etc.) in macOS Photos via Photos.sqlite, collect into an album for manual deletion
