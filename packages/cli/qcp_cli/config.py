"""Configuration management for the QCP CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG_DIR = Path.home() / ".qcp"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def _load_config() -> dict[str, str]:
    if _CONFIG_FILE.exists():
        return json.loads(_CONFIG_FILE.read_text())  # type: ignore[no-any-return]
    return {}


def save_config(*, api_key: str, base_url: str) -> None:
    """Persist CLI configuration to disk."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = _load_config()
    cfg["api_key"] = api_key
    cfg["base_url"] = base_url
    _CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def get_api_key() -> str:
    """Resolve the API key from env or config file."""
    key = os.environ.get("QCP_API_KEY") or _load_config().get("api_key")
    if not key:
        raise SystemExit("No API key found. Run `qcp login` or set QCP_API_KEY.")
    return key


def get_base_url() -> str:
    """Resolve the API base URL from env or config file."""
    return os.environ.get("QCP_BASE_URL") or _load_config().get("base_url", "http://localhost:8000")
