from pathlib import Path
from urllib.parse import urlparse

COOKIES_DIR = Path("cookies")

# Map common subdomains to their main domain cookie file
_DOMAIN_ALIASES = {
    "music.yandex.ru": "yandex",
    "www.youtube.com": "youtube",
    "m.youtube.com": "youtube",
    "youtu.be": "youtube",
    "podcasts.apple.com": "apple",
}


def get_cookies_for_url(url: str, cookies_dir: Path = COOKIES_DIR) -> Path | None:
    """Find a cookies file matching the URL's domain. Returns path or None."""
    hostname = urlparse(url).hostname or ""

    # Check aliases first
    domain = _DOMAIN_ALIASES.get(hostname)
    if not domain:
        # Strip subdomains: music.yandex.ru → yandex.ru → yandex
        parts = hostname.split(".")
        domain = parts[-2] if len(parts) >= 2 else parts[0]

    cookie_path = cookies_dir / f"{domain}.txt"
    return cookie_path if cookie_path.exists() else None


def save_cookies(domain: str, content: bytes, cookies_dir: Path = COOKIES_DIR) -> Path:
    """Save cookie file for a domain. Returns the saved path."""
    cookies_dir.mkdir(parents=True, exist_ok=True)
    # Normalize domain name
    domain = domain.lower().strip().replace(" ", "_")
    path = cookies_dir / f"{domain}.txt"
    path.write_bytes(content)
    return path


def list_cookies(cookies_dir: Path = COOKIES_DIR) -> list[str]:
    """List available cookie domains."""
    if not cookies_dir.exists():
        return []
    return sorted(p.stem for p in cookies_dir.glob("*.txt"))
