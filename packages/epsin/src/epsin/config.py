import os
from pathlib import Path

import yaml

from epsin.models import Source


def _xdg_path(env_name: str, fallback: str) -> Path:
    default = Path.home() / fallback
    value = os.getenv(env_name, str(default))
    return Path(value).expanduser().resolve()


def default_config_path() -> Path:
    return _xdg_path("XDG_CONFIG_HOME", ".config") / "epsin" / "sources.yaml"


def default_sources_path() -> Path:
    return Path(__file__).with_name("sources") / "default.yaml"


def load_sources(config_path: Path | None = None) -> list[Source]:
    if config_path is None:
        config_path = default_config_path()

    if config_path.exists():
        data = _load_yaml(config_path)
        if data and "sources" in data:
            return [_parse_source(s) for s in data["sources"] if isinstance(s, dict)]

    data = _load_yaml(default_sources_path())
    if not data or "sources" not in data:
        return []

    return [_parse_source(s) for s in data["sources"] if isinstance(s, dict)]


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = os.path.expandvars(path.read_text(encoding="utf-8"))
    data = yaml.safe_load(text) or {}
    return data if isinstance(data, dict) else {}


def _parse_source(raw: dict) -> Source:
    return Source(
        name=str(raw.get("name", "")),
        url=str(raw.get("url", "")),
        rss=str(raw.get("rss", "") or ""),
        tags=list(raw.get("tags", [])),
        extractor=str(raw.get("extractor", "") or ""),
    )
