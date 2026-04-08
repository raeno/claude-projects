import hashlib
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel

from podcast2obsidian.config import load_config, save_config, get_server_config
from podcast2obsidian.downloader import download, fetch_subtitles
from podcast2obsidian.transcriber import transcribe
from podcast2obsidian.enricher import enrich
from podcast2obsidian.formatter import format_note, save_note, slugify_title

app = typer.Typer(
    help="Download podcasts, transcribe, enrich with AI, save to Obsidian."
)
config_app = typer.Typer(help="Manage configuration.")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show() -> None:
    """Display current configuration."""
    config = load_config()
    for key, value in config.items():
        display_value = (
            value if "api_key" not in key or not value else value[:8] + "..."
        )
        rprint(f"  [bold]{key}[/bold] = {display_value}")


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    config = load_config()
    if key not in config:
        rprint(f"[red]Unknown key: {key}[/red]")
        raise typer.Exit(1)
    config[key] = value
    save_config(config)
    display = value if "key" not in key and "token" not in key else value[:8] + "..."
    rprint(f"[green]Set {key} = {display}[/green]")


@app.command()
def process(
    url: str = typer.Argument(help="Podcast episode URL"),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Transcription language"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Whisper model name"
    ),
    cookies: Optional[Path] = typer.Option(
        None, "--cookies", "-c", help="Path to cookies.txt file"
    ),
) -> None:
    """Download, transcribe, enrich, and save a podcast episode."""
    config = load_config()

    if not config["vault_path"]:
        config["vault_path"] = typer.prompt("Obsidian vault path")
        save_config(config)
    if not config["openai_api_key"]:
        config["openai_api_key"] = typer.prompt("OpenAI API key")
        save_config(config)

    lang = language or config["language"]
    server_cfg = get_server_config(config)
    if model:
        server_cfg["whisper_model"] = model
    vault_path = Path(config["vault_path"]).expanduser()
    rprint(
        f"[dim]Server: {config.get('server') or 'auto-detected'} ({server_cfg.get('backend')})[/dim]"
    )

    if cookies is None:
        default_cookies = Path("cookies.txt")
        if default_cookies.exists():
            cookies = default_cookies

    # Step 1: Try subtitles first (fast path)
    transcript = None
    rprint("[bold blue]Checking for subtitles...[/bold blue]")
    sub_result = fetch_subtitles(url, cookies=cookies, language=lang)
    if sub_result:
        info, transcript = sub_result
        from podcast2obsidian.downloader import DownloadResult

        result = DownloadResult(
            audio_path=Path(),
            title=info.get("title", "Unknown"),
            podcast_name=info.get("album")
            or info.get("playlist_title")
            or info.get("uploader", "Unknown"),
            source_url=info.get("webpage_url", url),
            subtitles=transcript,
        )
        rprint(f"  [green]Found subtitles![/green] {len(transcript)} chars")
    else:
        rprint("  No subtitles, falling back to audio + whisper")

        cache_dir = (
            Path.home()
            / ".cache"
            / "podcast2obsidian"
            / hashlib.sha256(url.encode()).hexdigest()[:16]
        )
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: Download (skip if cached)
        cached_files = list(cache_dir.glob("*.*"))
        if cached_files:
            rprint(f"[bold blue]Using cached:[/bold blue] {cached_files[0].name}")
            result = download(
                url, output_dir=cache_dir, cookies=cookies, skip_download=True
            )
        else:
            rprint("[bold blue]Downloading...[/bold blue]")
            result = download(url, output_dir=cache_dir, cookies=cookies)
            rprint(f"  Downloaded: {result.title}")

        # Step 3: Transcribe
        transcript = transcribe(
            result.audio_path,
            server_config=server_cfg,
            language=lang,
            hf_token=config.get("hf_token", ""),
        )
        rprint(f"  Transcribed: {len(transcript)} chars")

    # Step 3: Enrich
    rprint("[bold blue]Enriching with AI...[/bold blue]")
    enrichment = enrich(
        transcript, api_key=config["openai_api_key"], model=config["openai_model"]
    )

    # Step 4: Format and save
    slug = slugify_title(result.title)
    note = format_note(
        title=result.title,
        podcast_name=result.podcast_name,
        source_url=result.source_url,
        theses=enrichment.theses,
        references=enrichment.references,
        transcript=transcript,
    )
    saved_path = save_note(note, slug, vault_path)

    # Output
    rprint()
    rprint(Panel(enrichment.theses, title="Основные тезисы", border_style="green"))
    rprint()
    rprint(f"[bold green]Saved to:[/bold green] {saved_path}")
