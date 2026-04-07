from pathlib import Path
import tomllib
import tomli_w


CONFIG_DIR = Path.home() / ".config" / "podcast2obsidian"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG: dict[str, str] = {
    "vault_path": "",
    "whisper_model": "large-v3",
    "openai_api_key": "",
    "openai_model": "gpt-5.4-mini-2026-03-17",
    "language": "ru",
}


def load_config(path: Path = CONFIG_PATH) -> dict[str, str]:
    """Load config from TOML file, merging with defaults for missing keys."""
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    with open(path, "rb") as f:
        saved = tomllib.load(f)
    return {**DEFAULT_CONFIG, **saved}


def save_config(config: dict[str, str], path: Path = CONFIG_PATH) -> None:
    """Save config to TOML file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
