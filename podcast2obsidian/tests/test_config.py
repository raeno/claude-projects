from pathlib import Path
from podcast2obsidian.config import load_config, save_config, DEFAULT_CONFIG


def test_default_config_has_required_keys():
    assert "vault_path" in DEFAULT_CONFIG
    assert "whisper_model" in DEFAULT_CONFIG
    assert "openai_api_key" in DEFAULT_CONFIG
    assert "openai_model" in DEFAULT_CONFIG
    assert "language" in DEFAULT_CONFIG


def test_load_config_returns_defaults_when_no_file(tmp_path):
    config_path = tmp_path / "config.toml"
    config = load_config(config_path)
    assert config == DEFAULT_CONFIG


def test_save_and_load_config_roundtrip(tmp_path):
    config_path = tmp_path / "config.toml"
    custom = {**DEFAULT_CONFIG, "vault_path": "/my/vault", "openai_api_key": "sk-test"}
    save_config(custom, config_path)
    loaded = load_config(config_path)
    assert loaded["vault_path"] == "/my/vault"
    assert loaded["openai_api_key"] == "sk-test"


def test_load_config_merges_with_defaults(tmp_path):
    config_path = tmp_path / "config.toml"
    # Write a partial config (missing some keys)
    import tomli_w
    config_path.write_bytes(tomli_w.dumps({"vault_path": "/partial"}).encode("utf-8"))
    loaded = load_config(config_path)
    assert loaded["vault_path"] == "/partial"
    assert loaded["whisper_model"] == DEFAULT_CONFIG["whisper_model"]
