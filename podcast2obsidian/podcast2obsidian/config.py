import os
from pathlib import Path
import tomllib
import tomli_w
from dotenv import load_dotenv


CONFIG_DIR = Path.home() / ".config" / "podcast2obsidian"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "vault_path": "",
    "openai_api_key": "",
    "openai_model": "gpt-5.4-mini-2026-03-17",
    "language": "ru",
    "hf_token": "",
    "server": "",
    "telegram_bot_token": "",
    "telegram_allowed_users": "",
}

DEFAULT_SERVERS = {
    "mac_m2_max": {
        "backend": "mlx",
        "whisper_model": "large-v3",
    },
    "new_server": {
        "backend": "faster-whisper",
        "whisper_model": "large-v3",
        "compute_type": "int8",
        "cpu_threads": 6,
    },
}

# Map .env variable names to config keys
_ENV_MAP = {
    "OPENAI_API_KEY": "openai_api_key",
    "HF_TOKEN": "hf_token",
    "OBSIDIAN_VAULT_PATH": "vault_path",
    "P2O_SERVER": "server",
    "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
    "TELEGRAM_ALLOWED_USERS": "telegram_allowed_users",
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load config from TOML file, merging with defaults. .env overrides empty values."""
    load_dotenv()

    if not path.exists():
        config = dict(DEFAULT_CONFIG)
    else:
        with open(path, "rb") as f:
            saved = tomllib.load(f)
        config = {**DEFAULT_CONFIG, **saved}

    for env_var, config_key in _ENV_MAP.items():
        if not config.get(config_key) and os.environ.get(env_var):
            config[config_key] = os.environ[env_var]

    return config


def get_server_config(config: dict) -> dict:
    """Get transcription config for the active server profile."""
    server_name = config.get("server", "")

    # Check user-defined servers in config, then built-in defaults
    user_servers = config.get("servers", {})
    if server_name and server_name in user_servers:
        return user_servers[server_name]
    if server_name and server_name in DEFAULT_SERVERS:
        return DEFAULT_SERVERS[server_name]

    # No server specified — auto-detect
    import platform

    if platform.machine() == "arm64" and platform.system() == "Darwin":
        return DEFAULT_SERVERS["mac_m2_max"]

    # Default CPU fallback
    return {
        "backend": "faster-whisper",
        "whisper_model": "large-v3",
        "compute_type": "int8",
        "cpu_threads": 4,
    }


def save_config(config: dict, path: Path = CONFIG_PATH) -> None:
    """Save config to TOML file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(config, f)
