import importlib
from pathlib import Path

from epsin.models import Extractor, Source

_REGISTRY: dict[str, str] = {}

_bundled = Path(__file__).parent
for _py in sorted(_bundled.glob("*.py")):
    _mod = _py.stem
    if _mod.startswith("_") or _mod == "generic":
        continue
    _REGISTRY[_mod] = f"epsin.extractors.{_mod}"


def resolve(source: Source) -> Extractor:
    if source.extractor:
        return _load(source.extractor)

    snake = source.snake_name
    if snake in _REGISTRY:
        return _load(_REGISTRY[snake])

    return _load("epsin.extractors.generic")


def _load(dotted: str) -> Extractor:
    mod = importlib.import_module(dotted)
    return mod.EXTRACTOR
