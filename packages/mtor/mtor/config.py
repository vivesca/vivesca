"""mtor config loader — reads mtor.toml for provider and runtime settings."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProviderConfig:
    """A single LLM provider endpoint."""

    name: str
    url: str
    model: str
    key_env: str
    concurrency: int = 4
    harness: str = "claude"

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.key_env)


@dataclass
class MtorConfig:
    """Top-level mtor configuration."""

    coaching_file: Path | None = None
    workdir: Path = field(default_factory=Path.cwd)
    log_file: Path = field(default_factory=lambda: Path("mtor.jsonl"))
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    default_provider: str = ""
    hooks: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> MtorConfig:
        if path and path.exists():
            return cls._from_file(path)
        for candidate in [Path("mtor.toml"), Path.home() / ".config/mtor/mtor.toml"]:
            if candidate.exists():
                return cls._from_file(candidate)
        return cls()

    @classmethod
    def _from_file(cls, path: Path) -> MtorConfig:
        with open(path, "rb") as fh:
            raw = tomllib.load(fh)
        mtor_section = raw.get("mtor", {})
        providers_raw = raw.get("providers", {})
        hooks_raw = raw.get("hooks", {})
        providers = {}
        for name, prov in providers_raw.items():
            providers[name] = ProviderConfig(
                name=name,
                url=prov["url"],
                model=prov["model"],
                key_env=prov.get("key_env", f"{name.upper()}_API_KEY"),
                concurrency=prov.get("concurrency", 4),
                harness=prov.get("harness", "claude"),
            )
        coaching_raw = mtor_section.get("coaching_file")
        return cls(
            coaching_file=Path(coaching_raw) if coaching_raw else None,
            workdir=Path(mtor_section.get("workdir", ".")),
            log_file=Path(mtor_section.get("log_file", "mtor.jsonl")),
            providers=providers,
            default_provider=mtor_section.get("default_provider", next(iter(providers), "")),
            hooks=hooks_raw,
        )
