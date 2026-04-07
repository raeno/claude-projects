import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel

from podcast2obsidian.config import load_config, save_config
from podcast2obsidian.downloader import download
from podcast2obsidian.transcriber import transcribe
from podcast2obsidian.enricher import enrich
from podcast2obsidian.formatter import format_note, save_note, slugify_title

app = typer.Typer(help="Download podcasts, transcribe, enrich with AI, save to Obsidian.")
config_app = typer.Typer(help="Manage configuration.")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show() -> None:
    """Display current configuration."""
    config = load_config()
    for key, value in config.items():
        display_value = value if "api_key" not in key or not value else value[:8] + "..."
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
    rprint(f"[green]Set {key} = {value}[/green]")


@app.command()
def process(
    url: str = typer.Argument(help="Podcast episode URL"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Transcription language"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Whisper model name"),
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
    whisper_model = model or config["whisper_model"]
    vault_path = Path(config["vault_path"]).expanduser()

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Step 1: Download
        rprint("[bold blue]Downloading...[/bold blue]")
        result = download(url, output_dir=Path(tmp_dir))
        rprint(f"  Downloaded: {result.title}")

        # Step 2: Transcribe
        rprint("[bold blue]Transcribing...[/bold blue]")
        transcript = transcribe(result.audio_path, model_name=whisper_model, language=lang)
        rprint(f"  Transcribed: {len(transcript)} characters")

    # Step 3: Enrich
    rprint("[bold blue]Enriching with AI...[/bold blue]")
    enrichment = enrich(transcript, api_key=config["openai_api_key"], model=config["openai_model"])

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
