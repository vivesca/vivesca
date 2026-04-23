from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class Source:
    name: str
    url: str
    rss: str = ""
    tags: list[str] = field(default_factory=list)
    extractor: str = ""

    @property
    def snake_name(self) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "_", self.name.lower()).strip("_")


@dataclass(slots=True)
class Item:
    source: str
    title: str
    url: str
    date: str
    summary: str
    tags: list[str] = field(default_factory=list)
    content_md: str = ""


class Extractor(Protocol):
    def fetch(self, source: Source, full: bool = False) -> list[Item]: ...
