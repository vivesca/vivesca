"""pondus — AI model benchmark aggregator (unchanged name: pondus = weight/measure)."""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "PyYAML",
# ]
# ///

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIVEBENCH_FROZEN_SINCE = (2025, 4)  # April 2025

BUNDLED_MODELS_TOML_PATH = Path(__file__).parent.parent.parent.parent / "code" / "pondus" / "models.toml"

HTTP_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# Models / data structures
# ---------------------------------------------------------------------------

MetricValue = float | int | str


@dataclass
class ModelScore:
    model: str
    source_model_name: str
    metrics: dict[str, MetricValue] = field(default_factory=dict)
    rank: Optional[int] = None


@dataclass
class SourceResult:
    source: str
    fetched_at: Optional[datetime] = None
    status: str = "ok"  # "ok" | "cached" | "unavailable" | "error:<msg>"
    scores: list[ModelScore] = field(default_factory=list)


@dataclass
class QueryInfo:
    query_type: str
    model: Optional[str] = None
    models: Optional[list[str]] = None
    top: Optional[int] = None


@dataclass
class PondusOutput:
    timestamp: datetime
    query: QueryInfo
    sources: list[SourceResult]
    source_tags: Optional[dict[str, list[str]]] = None


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Caches"
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "pondus"


class Cache:
    def __init__(self, ttl_hours: int = 24):
        self.dir = _cache_dir()
        self.ttl_hours = ttl_hours

    def get(self, source: str) -> Optional[tuple[datetime, Any]]:
        path = self.dir / f"{source}.json"
        if not path.exists():
            return None
        try:
            entry = json.loads(path.read_text())
            fetched_at = datetime.fromisoformat(entry["fetched_at"])
            age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
            if age_hours < entry.get("ttl_hours", self.ttl_hours):
                return fetched_at, entry["data"]
        except Exception:
            pass
        return None

    def set(self, source: str, data: Any) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": self.ttl_hours,
            "data": data,
        }
        path = self.dir / f"{source}.json"
        tmp = self.dir / f"{source}.json.tmp"
        tmp.write_text(json.dumps(entry, indent=2))
        tmp.rename(path)

    def clear(self) -> None:
        if self.dir.exists():
            for f in self.dir.glob("*.json"):
                f.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _config_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "pondus"
    elif system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "pondus"
    else:
        return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pondus"


@dataclass
class Config:
    ttl_hours: int = 24
    alias_path: Optional[str] = None
    aa_api_key: Optional[str] = None
    agent_browser_path: str = "agent-browser"
    source_tags: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        config_path = _config_dir() / "config.toml"
        if config_path.exists():
            try:
                import tomllib  # type: ignore
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore
                except ImportError:
                    tomllib = None  # type: ignore

            if tomllib:
                try:
                    raw = tomllib.loads(config_path.read_text())
                    cache_cfg = raw.get("cache", {})
                    cfg.ttl_hours = int(cache_cfg.get("ttl_hours", 24))
                    alias_cfg = raw.get("alias", {})
                    cfg.alias_path = alias_cfg.get("path")
                    # AA api key
                    aa_section = raw.get("artificial-analysis") or raw.get("artificial_analysis", {})
                    if isinstance(aa_section, dict):
                        cfg.aa_api_key = aa_section.get("api_key")
                    # agent browser path
                    for section_name in ("seal", "swe-rebench"):
                        section = raw.get(section_name, {})
                        if isinstance(section, dict) and "agent_browser_path" in section:
                            cfg.agent_browser_path = section["agent_browser_path"]
                            break
                except Exception:
                    pass

        # Env var override for AA key
        env_key = os.environ.get("AA_API_KEY", "").strip()
        if env_key:
            cfg.aa_api_key = env_key

        # Load source tags from sources.toml
        sources_path = _config_dir() / "sources.toml"
        if sources_path.exists() and tomllib:  # type: ignore
            try:
                raw_sources = tomllib.loads(sources_path.read_text())
                cfg.source_tags = {k: v.get("tags", []) for k, v in raw_sources.items()}
            except Exception:
                pass

        return cfg


# ---------------------------------------------------------------------------
# Alias map
# ---------------------------------------------------------------------------

class AliasMap:
    def __init__(self, to_canonical: dict[str, str]):
        self._map = to_canonical  # lower_name -> canonical

    @classmethod
    def load(cls, override_path: Optional[str] = None) -> "AliasMap":
        to_canonical: dict[str, str] = {}

        # Load bundled aliases from pondus repo
        if BUNDLED_MODELS_TOML_PATH.exists():
            cls._parse_into(BUNDLED_MODELS_TOML_PATH.read_text(), to_canonical)

        # User override
        if override_path:
            p = Path(override_path)
            if p.exists():
                cls._parse_into(p.read_text(), to_canonical)
        else:
            default_override = _config_dir() / "models.toml"
            if default_override.exists():
                cls._parse_into(default_override.read_text(), to_canonical)

        return cls(to_canonical)

    @staticmethod
    def _parse_into(toml_str: str, to_canonical: dict[str, str]) -> None:
        try:
            try:
                import tomllib  # type: ignore
            except ImportError:
                import tomli as tomllib  # type: ignore
            entries = tomllib.loads(toml_str)
            for entry in entries.values():
                if not isinstance(entry, dict):
                    continue
                canonical = entry.get("canonical", "").lower()
                if not canonical:
                    continue
                to_canonical[canonical] = canonical
                for alias in entry.get("aliases", []):
                    to_canonical[alias.lower()] = canonical
        except Exception:
            pass

    def resolve(self, name: str) -> str:
        lower = name.lower()
        # Exact match
        if lower in self._map:
            return self._map[lower]
        # Prefix match
        best = self._prefix_match(lower)
        return best if best is not None else lower

    def matches(self, source_name: str, canonical: str) -> bool:
        return self.resolve(source_name) == canonical.lower()

    def _prefix_match(self, lower_name: str) -> Optional[str]:
        best: Optional[tuple[int, str]] = None
        for alias, canonical in self._map.items():
            if len(lower_name) > len(alias) and lower_name.startswith(alias):
                next_char = lower_name[len(alias)]
                allowed = False
                if next_char in ("(", " "):
                    allowed = True
                elif next_char == "-":
                    after = lower_name[len(alias) + 1:len(alias) + 2]
                    allowed = after.isdigit() or after == "("
                if allowed:
                    if best is None or len(alias) > best[0]:
                        best = (len(alias), canonical)
        return best[1] if best is not None else None


# ---------------------------------------------------------------------------
# Agent-browser helper
# ---------------------------------------------------------------------------

def _run_agent_browser(agent_browser_path: str, args: list[str]) -> str:
    binary = shutil.which(agent_browser_path) or agent_browser_path
    try:
        result = subprocess.run(
            [binary] + args,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"agent-browser not found: {agent_browser_path}") from exc
    if result.returncode != 0:
        details = (result.stderr or result.stdout or f"exit {result.returncode}").strip()
        raise RuntimeError(f"agent-browser {' '.join(args)} failed: {details}")
    return result.stdout


def _map_command_error(source: str, step: str, exc: Exception) -> SourceResult:
    if isinstance(exc, FileNotFoundError):
        return SourceResult(source=source, status="unavailable")
    return SourceResult(
        source=source,
        status=f"error:{source} scrape failed at {step}: {exc}",
    )


def _extract_cell_value(line: str) -> Optional[str]:
    start = line.find('"')
    if start == -1:
        return None
    start += 1
    end = line.find('"', start)
    if end == -1:
        return None
    return line[start:end]


# ---------------------------------------------------------------------------
# AA effort classification
# ---------------------------------------------------------------------------

def classify_effort_level(model_name: str) -> str:
    """Returns 'max', 'low', or 'standard'."""
    n = model_name.lower()
    if "(max)" in n or "adaptive" in n:
        return "max"
    if "low-effort" in n or "low effort" in n or "(low)" in n:
        return "low"
    return "standard"


def effort_matches(effort_filter: str, effort: str) -> bool:
    if effort_filter == "all":
        return True
    return effort_filter == effort


def apply_aa_effort_filter(results: list[SourceResult], effort: str) -> None:
    if effort == "all":
        return
    for result in results:
        if result.source != "artificial-analysis":
            continue
        result.scores = [
            s for s in result.scores
            if effort_matches(effort, classify_effort_level(s.source_model_name))
        ]


# ---------------------------------------------------------------------------
# Source: Artificial Analysis
# ---------------------------------------------------------------------------

def _fetch_aa(config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("artificial-analysis")
    if cached:
        fetched_at, data = cached
        return _parse_aa_cached(data, fetched_at, "cached")

    if config.aa_api_key:
        try:
            result = _fetch_aa_api(config.aa_api_key, cache)
            return result
        except Exception as api_err:
            try:
                fallback = _fetch_aa_scrape(config, cache)
                if fallback.status == "ok":
                    return fallback
            except Exception:
                pass
            return SourceResult(
                source="artificial-analysis",
                status=f"error:AA API failed and scrape fallback failed: {api_err}",
            )

    return _fetch_aa_scrape(config, cache)


def _fetch_aa_api(api_key: str, cache: Cache) -> SourceResult:
    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        resp = client.get(
            "https://artificialanalysis.ai/api/v2/data/llms/models",
            headers={"x-api-key": api_key},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"AA API returned HTTP {resp.status_code}")

    payload = resp.json()
    ranked: list[tuple[str, float]] = []
    for model in payload.get("data", []):
        score = (model.get("evaluations") or {}).get("artificial_analysis_intelligence_index")
        if score is not None:
            ranked.append((model["name"], float(score)))

    if not ranked:
        raise RuntimeError("AA API returned no models with intelligence index")

    ranked.sort(key=lambda x: x[1], reverse=True)
    cached_rows = [{"source_model_name": n, "intelligence_index": s} for n, s in ranked]
    cache_value = {"scores": cached_rows}
    cache.set("artificial-analysis", cache_value)
    return _parse_aa_cached(cache_value, datetime.now(timezone.utc), "ok")


def _fetch_aa_scrape(config: Config, cache: Cache) -> SourceResult:
    agent_browser = config.agent_browser_path
    try:
        _run_agent_browser(agent_browser, ["open", "https://artificialanalysis.ai/leaderboards/models"])
    except Exception as exc:
        return _map_command_error("artificial-analysis", "open", exc)

    try:
        _run_agent_browser(agent_browser, ["wait", "3000"])
    except Exception:
        pass

    try:
        page_text = _run_agent_browser(agent_browser, ["snapshot"])
    except Exception as exc:
        return _map_command_error("artificial-analysis", "snapshot", exc)

    parsed = _parse_aa_scores_from_text(page_text)
    if not parsed:
        return SourceResult(
            source="artificial-analysis",
            fetched_at=datetime.now(timezone.utc),
            status="error:Failed to parse any model scores from AA leaderboard page",
        )

    parsed.sort(key=lambda x: x[1], reverse=True)
    cached_rows = [{"source_model_name": n, "intelligence_index": s} for n, s in parsed]
    cache_value = {"scores": cached_rows}
    cache.set("artificial-analysis", cache_value)
    return _parse_aa_cached(cache_value, datetime.now(timezone.utc), "ok")


def _parse_aa_cached(data: Any, fetched_at: Optional[datetime], status: str) -> SourceResult:
    rows: list[tuple[str, float]] = []
    for entry in (data.get("scores") or []):
        name = entry.get("source_model_name")
        score = entry.get("intelligence_index") or entry.get("score")
        if name and score is not None:
            try:
                rows.append((name, float(score)))
            except (ValueError, TypeError):
                pass

    rows.sort(key=lambda x: x[1], reverse=True)
    scores = []
    for idx, (source_model_name, score) in enumerate(rows):
        rank = idx + 1
        scores.append(ModelScore(
            model=source_model_name.lower().replace(" ", "-").replace("_", "-"),
            source_model_name=source_model_name,
            metrics={"intelligence_index": score, "rank": rank},
            rank=rank,
        ))
    return SourceResult(source="artificial-analysis", fetched_at=fetched_at, status=status, scores=scores)


def _parse_aa_scores_from_text(text: str) -> list[tuple[str, float]]:
    results: dict[str, float] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        trimmed = lines[i].strip()
        if trimmed.startswith('- row "') and "Model Providers" in trimmed:
            cells: list[str] = []
            j = i + 1
            while j < len(lines):
                cell_line = lines[j].strip()
                if cell_line.startswith('- cell "'):
                    val = _extract_cell_value(cell_line)
                    if val is not None:
                        cells.append(val)
                elif cell_line.startswith("- row "):
                    break
                j += 1

            if len(cells) >= 4:
                model_name = cells[0]
                try:
                    score = float(cells[3])
                    if model_name and 1.0 <= score <= 100.0:
                        if model_name not in results or score > results[model_name]:
                            results[model_name] = score
                except (ValueError, TypeError):
                    pass
            i = j
        else:
            i += 1

    return list(results.items())


# ---------------------------------------------------------------------------
# Source: Arena
# ---------------------------------------------------------------------------

def _fetch_arena(config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("arena")
    if cached:
        fetched_at, data = cached
        return _parse_arena_cached(data, fetched_at, "cached")

    try:
        result = _fetch_arena_scrape(config, cache)
        if result.scores:
            return result
    except Exception:
        pass

    return _fetch_arena_json(cache)


def _fetch_arena_scrape(config: Config, cache: Cache) -> SourceResult:
    agent_browser = config.agent_browser_path
    try:
        _run_agent_browser(agent_browser, ["open", "https://lmarena.ai/leaderboard/text"])
    except Exception as exc:
        return _map_command_error("arena", "open", exc)

    try:
        _run_agent_browser(agent_browser, ["wait", "4000"])
    except Exception:
        pass

    try:
        page_text = _run_agent_browser(agent_browser, ["snapshot"])
    except Exception as exc:
        return _map_command_error("arena", "snapshot", exc)

    parsed = _parse_arena_from_snapshot(page_text)
    if not parsed:
        return SourceResult(
            source="arena",
            fetched_at=datetime.now(timezone.utc),
            status="error:Failed to parse any scores from Arena leaderboard",
        )

    cached_rows = [{"source_model_name": n, "elo_score": e} for n, e in parsed]
    cache_value = {"scores": cached_rows}
    cache.set("arena", cache_value)
    return _parse_arena_cached(cache_value, datetime.now(timezone.utc), "ok")


def _fetch_arena_json(cache: Cache) -> SourceResult:
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.get(
                "https://raw.githubusercontent.com/nakasyou/lmarena-history/main/output/scores.json"
            )
        if resp.status_code != 200:
            return SourceResult(source="arena", status=f"error:HTTP {resp.status_code}")
        data = resp.json()
    except Exception as exc:
        return SourceResult(source="arena", status=f"error:{exc}")

    scores = _parse_arena_json_response(data)
    if not scores:
        return SourceResult(
            source="arena",
            fetched_at=datetime.now(timezone.utc),
            status="error:Failed to parse Arena JSON",
        )

    cached_rows = [{"source_model_name": n, "elo_score": e} for n, e in scores]
    cache_value = {"scores": cached_rows}
    cache.set("arena", cache_value)
    return _parse_arena_cached(cache_value, datetime.now(timezone.utc), "ok")


def _parse_arena_cached(data: Any, fetched_at: Optional[datetime], status: str) -> SourceResult:
    rows: list[tuple[str, float]] = []
    for entry in (data.get("scores") or []):
        name = entry.get("source_model_name")
        elo = entry.get("elo_score")
        if name and elo is not None:
            try:
                rows.append((name, float(elo)))
            except (ValueError, TypeError):
                pass
    rows.sort(key=lambda x: x[1], reverse=True)
    scores = []
    for idx, (source_model_name, elo) in enumerate(rows):
        rank = idx + 1
        scores.append(ModelScore(
            model=source_model_name.lower().replace(" ", "-").replace("_", "-"),
            source_model_name=source_model_name,
            metrics={"elo_score": elo, "rank": rank},
            rank=rank,
        ))
    return SourceResult(source="arena", fetched_at=fetched_at, status=status, scores=scores)


def _is_image_or_video_model(name: str) -> bool:
    lower = name.lower()
    keywords = ["flux-", "image", "imagine", "dall-e", "midjourney", "stable-diff", "ideogram", "recraft", "video"]
    return any(kw in lower for kw in keywords)


def _parse_arena_from_snapshot(text: str) -> list[tuple[str, float]]:
    results: dict[str, float] = {}
    lines = text.splitlines()
    i = 0
    found_first_table = False

    while i < len(lines):
        trimmed = lines[i].strip()

        if (trimmed.startswith('- row "') and "1503" in trimmed) or trimmed.startswith('- row "1 '):
            found_first_table = True

        if found_first_table and trimmed.startswith('- row "'):
            cells: list[str] = []
            model_link_name: Optional[str] = None
            j = i + 1

            while j < len(lines):
                cell_line = lines[j].strip()
                if cell_line.startswith('- cell "'):
                    val = _extract_cell_value(cell_line)
                    if val is not None:
                        cells.append(val)
                elif cell_line.startswith('- link "') and model_link_name is None:
                    val = _extract_cell_value(cell_line)
                    if val and not val.startswith("http") and val:
                        model_link_name = val
                elif cell_line.startswith("- row "):
                    break
                j += 1

            if len(cells) >= 4:
                elo_str = cells[3].split()[0] if cells[3].split() else ""
                model_name = model_link_name
                if model_name is None:
                    # Strip provider prefix words from cell text
                    tokens = cells[2].split()
                    model_name = " ".join(
                        t for t in tokens
                        if not (t[0].isupper() and "-" not in t and "." not in t)
                    ) if tokens else cells[2]

                try:
                    elo = float(elo_str)
                    if elo > 500.0 and model_name and not _is_image_or_video_model(model_name):
                        results.setdefault(model_name, elo)
                except (ValueError, TypeError):
                    pass

            i = j
        else:
            i += 1

    return [(n, e) for n, e in results.items() if not _is_image_or_video_model(n)]


def _parse_arena_json_response(data: Any) -> list[tuple[str, float]]:
    if not isinstance(data, dict):
        return []
    latest_key = max(data.keys(), default=None)
    if not latest_key:
        return []
    text_data = data[latest_key].get("text") if isinstance(data[latest_key], dict) else None
    if not text_data or not isinstance(text_data, dict):
        return []
    category = "overall" if "overall" in text_data else (
        "full_old" if "full_old" in text_data else (next(iter(text_data), None))
    )
    if not category:
        return []
    cat_data = text_data[category]
    if not isinstance(cat_data, dict):
        return []
    return [
        (name, float(score))
        for name, score in cat_data.items()
        if isinstance(score, (int, float)) and not _is_image_or_video_model(name)
    ]


# ---------------------------------------------------------------------------
# Source: SWE-bench
# ---------------------------------------------------------------------------

def _fetch_swebench(_config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("swebench")
    if cached:
        fetched_at, data = cached
        return SourceResult(
            source="swebench",
            fetched_at=fetched_at,
            status="cached",
            scores=_parse_swebench_scores(data),
        )

    url = "https://raw.githubusercontent.com/SWE-bench/swe-bench.github.io/master/data/leaderboards.json"
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.get(url)
    except Exception as exc:
        return SourceResult(source="swebench", status=f"error:{exc}")

    if resp.status_code != 200:
        return SourceResult(source="swebench", status=f"error:HTTP {resp.status_code}")

    try:
        data = resp.json()
    except Exception as exc:
        return SourceResult(source="swebench", status=f"error:Failed to parse JSON: {exc}")

    cache.set("swebench", data)
    return SourceResult(
        source="swebench",
        fetched_at=datetime.now(timezone.utc),
        status="ok",
        scores=_parse_swebench_scores(data),
    )


def _parse_swebench_scores(data: Any) -> list[ModelScore]:
    scores: list[ModelScore] = []
    entries = (
        data.get("leaderboards") or data.get("results") or
        (data if isinstance(data, list) else None)
    )
    if entries is None:
        return scores

    for entry in entries:
        results_list = entry.get("results") if isinstance(entry, dict) else None
        if results_list:
            for result in results_list:
                ms = _extract_swebench_model_score(result)
                if ms:
                    scores.append(ms)
        else:
            ms = _extract_swebench_model_score(entry)
            if ms:
                scores.append(ms)

    # Deduplicate: keep highest resolved_rate per model
    best: dict[str, ModelScore] = {}
    for score in scores:
        key = score.source_model_name
        existing = best.get(key)
        new_rate = _get_float(score.metrics, "resolved_rate")
        if existing is None or new_rate > _get_float(existing.metrics, "resolved_rate"):
            best[key] = score

    deduped = sorted(best.values(), key=lambda s: _get_float(s.metrics, "resolved_rate"), reverse=True)
    for i, score in enumerate(deduped):
        score.rank = i + 1
    return deduped


def _extract_swebench_model_score(result: Any) -> Optional[ModelScore]:
    if not isinstance(result, dict):
        return None
    name = result.get("name")
    if not name:
        return None
    metrics: dict[str, MetricValue] = {}
    if (rate := result.get("resolved")) is not None:
        try:
            metrics["resolved_rate"] = float(rate)
        except (ValueError, TypeError):
            pass
    if (count := result.get("resolved_count")) is not None:
        try:
            metrics["resolved_count"] = int(count)
        except (ValueError, TypeError):
            pass
    if (date := result.get("date")) is not None:
        metrics["date"] = str(date)
    return ModelScore(
        model=name.lower().replace(" ", "-").replace("_", "-"),
        source_model_name=name,
        metrics=metrics,
    )


# ---------------------------------------------------------------------------
# Source: Aider
# ---------------------------------------------------------------------------

AIDER_URL = "https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/_data/polyglot_leaderboard.yml"


def _fetch_aider(_config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("aider")
    if cached:
        fetched_at, data = cached
        return SourceResult(
            source="aider",
            fetched_at=fetched_at,
            status="cached",
            scores=_parse_aider_scores(data),
        )

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.get(AIDER_URL)
    except Exception as exc:
        return SourceResult(source="aider", status=f"error:{exc}")

    if resp.status_code != 200:
        return SourceResult(source="aider", status=f"error:HTTP {resp.status_code}")

    try:
        entries = yaml.safe_load(resp.text)
    except Exception as exc:
        return SourceResult(source="aider", status=f"error:Failed to parse YAML: {exc}")

    cache.set("aider", entries)
    return SourceResult(
        source="aider",
        fetched_at=datetime.now(timezone.utc),
        status="ok",
        scores=_parse_aider_scores(entries),
    )


def _parse_aider_scores(data: Any) -> list[ModelScore]:
    if not isinstance(data, list):
        return []
    scores: list[ModelScore] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        model_name = entry.get("model")
        if not model_name:
            continue
        metrics: dict[str, MetricValue] = {}
        if (rate := entry.get("pass_rate_1")) is not None:
            try:
                metrics["pass_rate_1"] = float(rate)
            except (ValueError, TypeError):
                pass
        if (cost := entry.get("total_cost")) is not None:
            try:
                metrics["cost"] = float(cost)
            except (ValueError, TypeError):
                pass
        if (wf := entry.get("percent_cases_well_formed")) is not None:
            try:
                metrics["percent_cases_well_formed"] = float(wf)
            except (ValueError, TypeError):
                pass
        scores.append(ModelScore(
            model=model_name.lower().replace(" ", "-").replace("_", "-"),
            source_model_name=model_name,
            metrics=metrics,
        ))

    scores.sort(key=lambda s: _get_float(s.metrics, "pass_rate_1"), reverse=True)
    for i, s in enumerate(scores):
        s.rank = i + 1
    return scores


# ---------------------------------------------------------------------------
# Source: LiveBench
# ---------------------------------------------------------------------------

HF_ROWS_URL = "https://datasets-server.huggingface.co/rows"
LIVEBENCH_BATCH = 100


def _fetch_livebench(_config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("livebench")
    if cached:
        fetched_at, data = cached
        return _parse_livebench_cached(data, fetched_at, "cached")

    all_scores: dict[str, list[float]] = {}
    offset = 0
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            while True:
                url = (
                    f"{HF_ROWS_URL}?dataset=livebench/model_judgment"
                    f"&config=default&split=leaderboard&offset={offset}&length={LIVEBENCH_BATCH}"
                )
                try:
                    resp = client.get(url)
                    data = resp.json()
                except Exception:
                    break

                rows = data.get("rows") or []
                if not rows:
                    break

                for row_wrapper in rows:
                    row = row_wrapper.get("row") or {}
                    model = row.get("model")
                    score = row.get("score")
                    if model and score is not None:
                        try:
                            all_scores.setdefault(model, []).append(float(score))
                        except (ValueError, TypeError):
                            pass

                total = int(data.get("num_rows_total") or 0)
                offset += LIVEBENCH_BATCH
                if offset >= total:
                    break
    except Exception:
        pass

    if not all_scores:
        return SourceResult(
            source="livebench",
            fetched_at=datetime.now(timezone.utc),
            status="error:Failed to fetch LiveBench data from HuggingFace datasets API",
        )

    model_avgs = [
        (model, sum(scores) / len(scores) * 100.0)
        for model, scores in all_scores.items()
    ]
    model_avgs.sort(key=lambda x: x[1], reverse=True)

    cached_rows = [{"source_model_name": m, "global_average": s} for m, s in model_avgs]
    cache_value = {"scores": cached_rows}
    cache.set("livebench", cache_value)
    return _parse_livebench_cached(cache_value, datetime.now(timezone.utc), "ok")


def _parse_livebench_cached(data: Any, fetched_at: Optional[datetime], status: str) -> SourceResult:
    rows: list[tuple[str, float]] = []
    for entry in (data.get("scores") or []):
        name = entry.get("source_model_name")
        score = entry.get("global_average")
        if name and score is not None:
            try:
                rows.append((name, float(score)))
            except (ValueError, TypeError):
                pass
    rows.sort(key=lambda x: x[1], reverse=True)
    scores = []
    for idx, (source_model_name, score) in enumerate(rows):
        rank = idx + 1
        scores.append(ModelScore(
            model=source_model_name.lower().replace(" ", "-").replace("_", "-"),
            source_model_name=source_model_name,
            metrics={"global_average": score, "rank": rank},
            rank=rank,
        ))
    return SourceResult(source="livebench", fetched_at=fetched_at, status=status, scores=scores)


# ---------------------------------------------------------------------------
# Source: Terminal-Bench
# ---------------------------------------------------------------------------

HF_API_URL = "https://huggingface.co/api/datasets/sabhay/terminal-bench-2-leaderboard"


def _fetch_tbench(_config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("terminal-bench")
    if cached:
        fetched_at, data = cached
        return SourceResult(
            source="terminal-bench",
            fetched_at=fetched_at,
            status="cached",
            scores=_extract_tbench_from_siblings(data),
        )

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.get(HF_API_URL)
    except Exception as exc:
        return SourceResult(source="terminal-bench", status=f"error:{exc}")

    if resp.status_code != 200:
        return SourceResult(source="terminal-bench", status=f"error:HTTP {resp.status_code}")

    try:
        data = resp.json()
    except Exception as exc:
        return SourceResult(source="terminal-bench", status=f"error:{exc}")

    scores = _extract_tbench_from_siblings(data)
    if not scores:
        return SourceResult(source="terminal-bench", status="unavailable")

    cache.set("terminal-bench", data)
    return SourceResult(
        source="terminal-bench",
        fetched_at=datetime.now(timezone.utc),
        status="ok",
        scores=scores,
    )


def _extract_tbench_from_siblings(data: Any) -> list[ModelScore]:
    siblings = data.get("siblings") if isinstance(data, dict) else None
    if not siblings:
        return []

    model_counts: dict[str, int] = {}
    for sibling in siblings:
        filename = sibling.get("rfilename") if isinstance(sibling, dict) else None
        if not filename or not filename.endswith("result.json"):
            continue
        parts = filename.split("/")
        if len(parts) >= 4:
            agent_model = parts[3]
            model_counts[agent_model] = model_counts.get(agent_model, 0) + 1

    scores: list[ModelScore] = []
    for agent_model, count in model_counts.items():
        display_name = agent_model.replace("__", " / ")
        model_part = agent_model.split("__")[1] if "__" in agent_model else agent_model
        canonical = model_part.lower()
        scores.append(ModelScore(
            model=canonical,
            source_model_name=display_name,
            metrics={"tasks_completed": count},
        ))

    scores.sort(key=lambda s: _get_int(s.metrics, "tasks_completed"), reverse=True)
    for i, s in enumerate(scores):
        s.rank = i + 1
    return scores


# ---------------------------------------------------------------------------
# Source: SEAL
# ---------------------------------------------------------------------------

def _fetch_seal(config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("seal")
    if cached:
        fetched_at, data = cached
        return _parse_seal_cached(data, fetched_at, "cached")

    agent_browser = config.agent_browser_path
    try:
        _run_agent_browser(agent_browser, ["open", "https://scale.com/leaderboard"])
    except Exception as exc:
        return _map_command_error("seal", "open", exc)

    try:
        _run_agent_browser(agent_browser, ["wait", "2000"])
    except Exception:
        pass

    try:
        page_text = _run_agent_browser(agent_browser, ["snapshot"])
    except Exception as exc:
        return _map_command_error("seal", "snapshot", exc)

    parsed = _parse_seal_from_text(page_text)
    if not parsed:
        return SourceResult(
            source="seal",
            fetched_at=datetime.now(timezone.utc),
            status="error:Failed to parse any model scores from SEAL page output",
        )

    parsed.sort(key=lambda x: x[1], reverse=True)
    cached_rows = [{"source_model_name": n, "score": s} for n, s in parsed]
    cache_value = {"scores": cached_rows}
    cache.set("seal", cache_value)
    return _parse_seal_cached(cache_value, datetime.now(timezone.utc), "ok")


def _parse_seal_cached(data: Any, fetched_at: Optional[datetime], status: str) -> SourceResult:
    rows: list[tuple[str, float]] = []
    for entry in (data.get("scores") or []):
        name = entry.get("source_model_name")
        score = entry.get("score")
        if name and score is not None:
            try:
                rows.append((name, float(score)))
            except (ValueError, TypeError):
                pass
    rows.sort(key=lambda x: x[1], reverse=True)
    scores = []
    for idx, (source_model_name, score) in enumerate(rows):
        rank = idx + 1
        scores.append(ModelScore(
            model=source_model_name.lower().replace(" ", "-").replace("_", "-"),
            source_model_name=source_model_name,
            metrics={"overall_score": score, "rank": rank},
            rank=rank,
        ))
    return SourceResult(source="seal", fetched_at=fetched_at, status=status, scores=scores)


def _parse_seal_from_text(text: str) -> list[tuple[str, float]]:
    model_scores: dict[str, list[float]] = {}
    for line in text.splitlines():
        trimmed = line.strip()
        if "View Full Ranking" not in trimmed:
            continue
        start = trimmed.find('"')
        if start == -1:
            continue
        rest = trimmed[start + 1:]
        end = rest.rfind("View Full Ranking")
        if end == -1:
            continue
        link_text = rest[:end]
        for model, score in _seal_extract_model_scores(link_text):
            model_scores.setdefault(model, []).append(score)

    return [
        (model, sum(scores) / len(scores))
        for model, scores in model_scores.items()
    ]


def _seal_extract_model_scores(text: str) -> list[tuple[str, float]]:
    tokens = text.split()
    results: list[tuple[str, float]] = []
    score_positions = [i for i, t in enumerate(tokens) if "±" in t]

    if not score_positions:
        return results

    for si, score_pos in enumerate(score_positions):
        score_str = tokens[score_pos].split("±")[0]
        try:
            score = float(score_str)
        except ValueError:
            continue

        search_start = score_positions[si - 1] + 1 if si > 0 else 0
        rank_pos = next(
            (j for j in range(search_start, score_pos)
             if tokens[j].isdigit() and int(tokens[j]) <= 500),
            None,
        )
        name_start = (rank_pos + 1) if rank_pos is not None else search_start
        name = " ".join(t for t in tokens[name_start:score_pos] if t != "NEW")
        name = name.rstrip("*").strip()
        if len(name) >= 2 and any(c.isalpha() for c in name):
            results.append((name, score))

    return results


# ---------------------------------------------------------------------------
# Source: SWE-rebench
# ---------------------------------------------------------------------------

def _fetch_swe_rebench(config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("swe-rebench")
    if cached:
        fetched_at, data = cached
        return _parse_swe_rebench_cached(data, fetched_at, "cached")

    agent_browser = config.agent_browser_path
    try:
        _run_agent_browser(agent_browser, ["open", "https://swe-rebench.com/"])
    except Exception as exc:
        return _map_command_error("swe-rebench", "open", exc)

    try:
        _run_agent_browser(agent_browser, ["wait", "2000"])
    except Exception:
        pass

    try:
        page_text = _run_agent_browser(agent_browser, ["snapshot"])
    except Exception as exc:
        return _map_command_error("swe-rebench", "snapshot", exc)

    parsed = _parse_swe_rebench_from_text(page_text)
    if not parsed:
        return SourceResult(
            source="swe-rebench",
            fetched_at=datetime.now(timezone.utc),
            status="error:Failed to parse any model scores from SWE-rebench page output",
        )

    parsed.sort(key=lambda x: x[1], reverse=True)
    cached_rows = [{"source_model_name": n, "score": s} for n, s in parsed]
    cache_value = {"scores": cached_rows}
    cache.set("swe-rebench", cache_value)
    return _parse_swe_rebench_cached(cache_value, datetime.now(timezone.utc), "ok")


def _parse_swe_rebench_cached(data: Any, fetched_at: Optional[datetime], status: str) -> SourceResult:
    rows: list[tuple[str, float]] = []
    for entry in (data.get("scores") or []):
        name = entry.get("source_model_name")
        score = entry.get("score")
        if name and score is not None:
            try:
                rows.append((name, float(score)))
            except (ValueError, TypeError):
                pass
    rows.sort(key=lambda x: x[1], reverse=True)
    scores = []
    for idx, (source_model_name, score) in enumerate(rows):
        rank = idx + 1
        scores.append(ModelScore(
            model=source_model_name.lower().replace(" ", "-").replace("_", "-"),
            source_model_name=source_model_name,
            metrics={"resolve_rate": score, "rank": rank},
            rank=rank,
        ))
    return SourceResult(source="swe-rebench", fetched_at=fetched_at, status=status, scores=scores)


def _parse_swe_rebench_from_text(text: str) -> list[tuple[str, float]]:
    results: dict[str, float] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        trimmed = lines[i].strip()
        if trimmed.startswith('- row "') and "%" in trimmed:
            cells: list[str] = []
            j = i + 1
            while j < len(lines):
                cell_line = lines[j].strip()
                if cell_line.startswith('- cell "'):
                    val = _extract_cell_value(cell_line)
                    if val is not None:
                        cells.append(val)
                elif cell_line.startswith("- row "):
                    break
                j += 1

            if len(cells) >= 3:
                model_name = cells[1]
                score_str = cells[2].rstrip("%")
                try:
                    score = float(score_str)
                    if model_name and any(c.isalpha() for c in model_name) and model_name != "Model":
                        results.setdefault(model_name, score)
                except (ValueError, TypeError):
                    pass
            i = j
        else:
            i += 1

    return list(results.items())


# ---------------------------------------------------------------------------
# Source: OpenRouter
# ---------------------------------------------------------------------------

def _fetch_openrouter(_config: Config, cache: Cache) -> SourceResult:
    cached = cache.get("openrouter")
    if cached:
        fetched_at, data = cached
        return _parse_openrouter_cached(data, fetched_at, "cached")

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.get("https://openrouter.ai/api/v1/models")
    except Exception as exc:
        return SourceResult(source="openrouter", status=f"error:{exc}")

    if resp.status_code != 200:
        return SourceResult(
            source="openrouter",
            status=f"error:OpenRouter API returned HTTP {resp.status_code}",
        )

    try:
        payload = resp.json()
    except Exception as exc:
        return SourceResult(source="openrouter", status=f"error:{exc}")

    cached_rows: list[dict] = []
    for model in payload.get("data", []):
        pricing = model.get("pricing") or {}
        prompt_str = pricing.get("prompt")
        completion_str = pricing.get("completion")
        if prompt_str is None or completion_str is None:
            continue
        try:
            prompt_per_token = float(prompt_str)
            completion_per_token = float(completion_str)
        except (ValueError, TypeError):
            continue
        if prompt_per_token == 0.0 and completion_per_token == 0.0:
            continue
        cached_rows.append({
            "source_model_name": model["id"],
            "prompt_per_1m": prompt_per_token * 1_000_000,
            "completion_per_1m": completion_per_token * 1_000_000,
        })

    if not cached_rows:
        return SourceResult(
            source="openrouter",
            fetched_at=datetime.now(timezone.utc),
            status="error:OpenRouter API returned no models with pricing data",
        )

    cache_value = {"scores": cached_rows}
    cache.set("openrouter", cache_value)
    return _parse_openrouter_cached(cache_value, datetime.now(timezone.utc), "ok")


def _parse_openrouter_cached(data: Any, fetched_at: Optional[datetime], status: str) -> SourceResult:
    scores: list[ModelScore] = []
    for entry in (data.get("scores") or []):
        name = entry.get("source_model_name")
        prompt = entry.get("prompt_per_1m")
        completion = entry.get("completion_per_1m")
        if name is None or prompt is None or completion is None:
            continue
        try:
            model = name.lower().replace(" ", "-").replace("_", "-")
            scores.append(ModelScore(
                model=model,
                source_model_name=name,
                metrics={"prompt_per_1m": float(prompt), "completion_per_1m": float(completion)},
            ))
        except (ValueError, TypeError):
            pass
    return SourceResult(source="openrouter", fetched_at=fetched_at, status=status, scores=scores)


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

SOURCE_TAGS: dict[str, list[str]] = {
    "artificial-analysis": ["reasoning", "general"],
    "arena": ["reasoning", "general"],
    "swebench": ["coding"],
    "aider": ["coding"],
    "livebench": ["reasoning"],
    "terminal-bench": ["coding", "agentic"],
    "seal": ["reasoning"],
    "swe-rebench": ["coding"],
    "openrouter": ["general"],
}

SOURCE_FETCHERS = {
    "artificial-analysis": _fetch_aa,
    "arena": _fetch_arena,
    "swebench": _fetch_swebench,
    "aider": _fetch_aider,
    "livebench": _fetch_livebench,
    "terminal-bench": _fetch_tbench,
    "seal": _fetch_seal,
    "swe-rebench": _fetch_swe_rebench,
    "openrouter": _fetch_openrouter,
}

SOURCE_ORDER = [
    "artificial-analysis", "arena", "swebench", "aider",
    "livebench", "terminal-bench", "seal", "swe-rebench", "openrouter",
]


def fetch_all(config: Config, cache: Cache) -> list[SourceResult]:
    results = []
    for source_name in SOURCE_ORDER:
        fetcher = SOURCE_FETCHERS[source_name]
        try:
            result = fetcher(config, cache)
        except Exception as exc:
            result = SourceResult(source=source_name, status=f"error:{exc}")
        results.append(result)
    return results


def _source_tags_for_output(config: Config) -> dict[str, list[str]]:
    tags = dict(SOURCE_TAGS)
    for source, override in config.source_tags.items():
        tags[source.lower()] = override
    return tags


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------

def _get_float(metrics: dict, key: str) -> float:
    v = metrics.get(key)
    if isinstance(v, (int, float)):
        return float(v)
    return 0.0


def _get_int(metrics: dict, key: str) -> int:
    v = metrics.get(key)
    if isinstance(v, (int, float)):
        return int(v)
    return 0


def _percentile(rank: int, total: int) -> float:
    if total <= 1:
        return 1.0
    return (total - rank) / (total - 1)


def _std_dev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

def aggregate_results(
    results: list[SourceResult],
    min_sources: int,
    show_excluded: bool,
) -> tuple[SourceResult, list[tuple[str, int]]]:
    totals: dict[str, list[float]] = {}

    for source in results:
        total_in_source = len(source.scores)
        if total_in_source == 0:
            continue
        for score in source.scores:
            if score.rank is None:
                continue
            totals.setdefault(score.model, []).append(_percentile(score.rank, total_in_source))

    excluded: list[tuple[str, int]] = []
    rows: list[tuple[str, float, float, int]] = []
    for model, percentiles in totals.items():
        count = len(percentiles)
        if count < min_sources:
            if show_excluded:
                excluded.append((model, count))
        else:
            avg = sum(percentiles) / count
            spread = _std_dev(percentiles)
            rows.append((model, avg, spread, count))

    rows.sort(key=lambda x: (-x[1], x[0]))
    excluded.sort(key=lambda x: (-x[1], x[0]))

    scores: list[ModelScore] = []
    for i, (model, avg_percentile, spread, sources_count) in enumerate(rows):
        scores.append(ModelScore(
            model=model,
            source_model_name=model,
            metrics={
                "avg_percentile": avg_percentile,
                "spread": spread,
                "sources_count": sources_count,
            },
            rank=i + 1,
        ))

    agg_result = SourceResult(source="aggregate", status="ok", scores=scores)
    return agg_result, excluded if show_excluded else []


def _excluded_models(results: list[SourceResult], min_sources: int) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for source in results:
        for score in source.scores:
            if score.rank is not None:
                counts[score.model] = counts.get(score.model, 0) + 1
    excluded = [(m, c) for m, c in counts.items() if c < min_sources]
    excluded.sort(key=lambda x: (-x[1], x[0]))
    return excluded


# ---------------------------------------------------------------------------
# Recommend
# ---------------------------------------------------------------------------

TASK_SPECS = {
    "coding": {
        "description": "Use coding benchmarks with SWE-bench as the primary signal.",
        "sources": [
            {"source": "swebench", "label": "SWE-bench", "metric": "resolved_rate", "sort": "desc"},
            {"source": "terminal-bench", "label": "Terminal-Bench", "metric": "tasks_completed", "sort": "desc"},
            {"source": "aider", "label": "Aider", "metric": "pass_rate_1", "sort": "desc"},
            {"source": "swe-rebench", "label": "SWE-rebench", "metric": "resolve_rate", "sort": "desc"},
        ],
    },
    "agentic": {
        "description": "Use agentic execution benchmarks with Terminal-Bench weighted first.",
        "sources": [
            {"source": "terminal-bench", "label": "Terminal-Bench", "metric": "tasks_completed", "sort": "desc"},
            {"source": "seal", "label": "SEAL", "metric": "overall_score", "sort": "desc"},
        ],
    },
    "intelligence": {
        "description": "Use Artificial Analysis intelligence index; max-effort variants are best.",
        "sources": [
            {"source": "artificial-analysis", "label": "Artificial Analysis", "metric": "intelligence_index", "sort": "desc"},
        ],
    },
    "general": {
        "description": "Use Arena human preference ELO for general-purpose model choice.",
        "sources": [
            {"source": "arena", "label": "Arena", "metric": "elo_score", "sort": "desc"},
        ],
    },
    "cost": {
        "description": "Use OpenRouter pricing and rank the cheapest models first.",
        "sources": [
            {"source": "openrouter", "label": "OpenRouter", "metric": "total_cost", "sort": "asc"},
        ],
    },
    "value": {
        "description": "Intelligence per dollar — AA intelligence index divided by OpenRouter cost per 1M tokens.",
        "sources": [
            {"source": "value", "label": "Value (intel/$)", "metric": "value_score", "sort": "desc"},
            {"source": "artificial-analysis", "label": "Intelligence", "metric": "intelligence_index", "sort": "desc"},
            {"source": "openrouter", "label": "Cost", "metric": "total_cost", "sort": "asc"},
        ],
    },
}

VALID_TASKS = list(TASK_SPECS.keys())


def _extract_metric(score: ModelScore, metric_name: str) -> Optional[float]:
    if metric_name == "total_cost":
        p = _get_float(score.metrics, "prompt_per_1m")
        c = _get_float(score.metrics, "completion_per_1m")
        if "prompt_per_1m" in score.metrics and "completion_per_1m" in score.metrics:
            return p + c
        return None
    v = score.metrics.get(metric_name)
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _canonical_model_name(aliases: AliasMap, score: ModelScore) -> str:
    by_model = aliases.resolve(score.model)
    if by_model != score.model.lower():
        return by_model
    by_source = aliases.resolve(score.source_model_name)
    if by_source != score.source_model_name.lower():
        return by_source
    return score.model.lower()


def _inject_value_scores(results: list[SourceResult], aliases: AliasMap) -> None:
    aa_scores: dict[str, float] = {}
    for r in results:
        if r.source == "artificial-analysis":
            for score in r.scores:
                v = score.metrics.get("intelligence_index")
                if isinstance(v, (int, float)):
                    aa_scores[_canonical_model_name(aliases, score)] = float(v)

    or_costs: dict[str, float] = {}
    for r in results:
        if r.source == "openrouter":
            for score in r.scores:
                p = score.metrics.get("prompt_per_1m")
                c = score.metrics.get("completion_per_1m")
                if isinstance(p, (int, float)) and isinstance(c, (int, float)):
                    total = float(p) + float(c)
                    if total > 0:
                        or_costs[_canonical_model_name(aliases, score)] = total

    value_scores: list[ModelScore] = []
    for model, intel in aa_scores.items():
        cost = or_costs.get(model)
        if cost is not None:
            value = intel / cost
            value_scores.append(ModelScore(
                model=model,
                source_model_name=model,
                metrics={"value_score": value},
            ))

    value_scores.sort(key=lambda s: _get_float(s.metrics, "value_score"), reverse=True)
    for i, s in enumerate(value_scores):
        s.rank = i + 1

    results.append(SourceResult(source="value", status="ok", scores=value_scores))


def _rank_models(
    spec: dict,
    results: list[SourceResult],
    aliases: AliasMap,
    top: int,
) -> list[dict]:
    models: dict[str, dict[str, float]] = {}

    for source_spec in spec["sources"]:
        result = next((r for r in results if r.source == source_spec["source"]), None)
        if result is None:
            continue
        best_for_source: dict[str, float] = {}
        for score in result.scores:
            metric = _extract_metric(score, source_spec["metric"])
            if metric is None:
                continue
            model = _canonical_model_name(aliases, score)
            existing = best_for_source.get(model)
            if existing is None:
                best_for_source[model] = metric
            else:
                is_better = (metric > existing) if source_spec["sort"] == "desc" else (metric < existing)
                if is_better:
                    best_for_source[model] = metric

        for model, metric in best_for_source.items():
            models.setdefault(model, {})[source_spec["source"]] = metric

    primary = spec["sources"][0]

    def sort_key(model_entry: tuple[str, dict]) -> tuple:
        model_name, metrics = model_entry
        primary_val = metrics.get(primary["source"])
        if primary_val is None:
            return (1, 0.0, model_name)
        if primary["sort"] == "desc":
            return (0, -primary_val, model_name)
        else:
            return (0, primary_val, model_name)

    ranked_models = sorted(models.items(), key=sort_key)[:top]

    rows = []
    for i, (model, metrics) in enumerate(ranked_models):
        row = {"rank": i + 1, "model": model, "metrics": {}}
        for source_spec in spec["sources"]:
            row["metrics"][source_spec["source"]] = metrics.get(source_spec["source"])
        rows.append(row)
    return rows


def cmd_recommend(
    config: Config,
    cache: Cache,
    aliases: AliasMap,
    task: str,
    top: int,
    effort: str,
    output_format: str,
    list_tasks: bool = False,
) -> None:
    if list_tasks:
        print(render_recommend_task_list(output_format))
        return

    if task not in TASK_SPECS:
        print(f"[error] Unknown task '{task}'. Use one of: {', '.join(VALID_TASKS)}", file=sys.stderr)
        sys.exit(1)

    spec = TASK_SPECS[task]
    wanted_sources = {s["source"] for s in spec["sources"] if s["source"] != "value"}
    results: list[SourceResult] = []
    for source_name in wanted_sources:
        fetcher = SOURCE_FETCHERS.get(source_name)
        if fetcher is None:
            continue
        try:
            result = fetcher(config, cache)
        except Exception as exc:
            result = SourceResult(source=source_name, status=f"error:{exc}")
        results.append(result)

    if any(s["source"] == "artificial-analysis" for s in spec["sources"]):
        apply_aa_effort_filter(results, effort)

    for r in results:
        print(f"[{r.source}] {_status_label(r.status)}", file=sys.stderr)

    if task == "value":
        _inject_value_scores(results, aliases)

    rows = _rank_models(spec, results, aliases, top)

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "description": spec["description"],
        "effort": effort,
        "top": top,
        "sources": [
            {
                "source": r.source,
                "label": next((s["label"] for s in spec["sources"] if s["source"] == r.source), r.source),
                "status": _status_label(r.status),
                "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None,
            }
            for r in results
        ],
        "rows": rows,
    }

    if output_format == "json":
        print(json.dumps(output, indent=2))
    elif output_format in ("table", "markdown"):
        print(_render_recommend_table(spec, output) if output_format == "table" else _render_recommend_markdown(spec, output))


def render_recommend_task_list(output_format: str) -> str:
    if output_format == "json":
        return json.dumps([
            {"task": task, "description": spec["description"], "sources": [s["source"] for s in spec["sources"]]}
            for task, spec in TASK_SPECS.items()
        ], indent=2)
    lines = [
        "Task          Description",
        "------------  --------------------------------------------------------------",
    ]
    for task, spec in TASK_SPECS.items():
        lines.append(f"{task:<12}  {spec['description']}")
    return "\n".join(lines)


def _render_recommend_table(spec: dict, output: dict) -> str:
    lines = ["", f"Task: {output['task']}  (sources: {', '.join(s['source'] for s in spec['sources'])})", ""]
    headers = ["Rank", "Model"] + [s["label"] for s in spec["sources"]]
    widths = [len(h) for h in headers]
    rows_data: list[list[str]] = []
    for row in output["rows"]:
        values = [str(row["rank"]), row["model"]]
        for s in spec["sources"]:
            v = row["metrics"].get(s["source"])
            values.append(_format_recommend_metric(s["metric"], v) if v is not None else "-")
        for i, val in enumerate(values):
            widths[i] = max(widths[i], len(val))
        rows_data.append(values)

    lines.append("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    lines.append("  ".join("-" * w for w in widths))
    for row in rows_data:
        lines.append("  ".join(v.ljust(widths[i]) for i, v in enumerate(row)))
    return "\n".join(lines)


def _render_recommend_markdown(spec: dict, output: dict) -> str:
    lines = [
        f"**Task:** `{output['task']}`  \n**Sources:** {', '.join(s['source'] for s in spec['sources'])}",
        "",
    ]
    headers = ["Rank", "Model"] + [s["label"] for s in spec["sources"]]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in output["rows"]:
        values = [str(row["rank"]), row["model"]]
        for s in spec["sources"]:
            v = row["metrics"].get(s["source"])
            values.append(_format_recommend_metric(s["metric"], v) if v is not None else "-")
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _format_recommend_metric(metric_name: str, value: Optional[float]) -> str:
    if value is None:
        return "-"
    if metric_name in ("resolved_rate", "resolve_rate", "pass_rate_1"):
        return f"{value:.1f}%"
    if metric_name in ("elo_score", "intelligence_index", "overall_score"):
        return f"{value:.1f}"
    if metric_name in ("total_cost", "prompt_per_1m", "completion_per_1m"):
        return f"${value:.2f}"
    if metric_name == "value_score":
        return f"{value:.1f}"
    if metric_name == "tasks_completed":
        return str(int(value))
    return f"{value:.2f}"


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

def _monitor_state_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "pondus" / "monitors.json"
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        return base / "pondus" / "monitors.json"
    else:
        return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "pondus" / "monitors.json"


def _load_monitor_state() -> dict:
    path = _monitor_state_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"watched": []}


def _save_monitor_state(state: dict) -> None:
    path = _monitor_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def cmd_monitor_add(model: str, aliases: AliasMap) -> None:
    canonical = aliases.resolve(model)
    state = _load_monitor_state()
    if any(w["model"] == canonical for w in state["watched"]):
        print(f"Already watching {canonical}.")
        return
    state["watched"].append({
        "model": canonical,
        "added_at": datetime.now().strftime("%Y-%m-%d"),
        "last_seen": {},
    })
    _save_monitor_state(state)
    print(f"Watching {canonical}. Run 'pondus monitor check' to poll now.")


def cmd_monitor_list() -> None:
    state = _load_monitor_state()
    if not state["watched"]:
        print("No models on the watchlist.")
        return
    print(f"{'MODEL':<25} {'ADDED':<15} SOURCES WITH DATA")
    for w in state["watched"]:
        sources = ", ".join(sorted(w.get("last_seen", {}).keys())) or "no data yet"
        print(f"{w['model']:<25} {w.get('added_at', ''):<15} {sources}")


def cmd_monitor_remove(model: str, aliases: AliasMap) -> None:
    canonical = aliases.resolve(model)
    state = _load_monitor_state()
    initial_len = len(state["watched"])
    state["watched"] = [w for w in state["watched"] if w["model"] != canonical]
    if len(state["watched"]) == initial_len:
        print(f"Model '{model}' was not on the watchlist.")
    else:
        _save_monitor_state(state)
        print(f"Removed '{canonical}' from watchlist.")


def cmd_monitor_check(config: Config, cache: Cache, aliases: AliasMap) -> None:
    state = _load_monitor_state()
    if not state["watched"]:
        print("No models on the watchlist.")
        return

    results = fetch_all(config, cache)
    today = datetime.now().strftime("%Y-%m-%d")
    state_changed = False

    for w in state["watched"]:
        new_data: list[tuple[str, str]] = []
        canonical = w["model"]

        for r in results:
            match = next(
                (s for s in r.scores
                 if s.model.lower() == canonical or aliases.matches(s.source_model_name, canonical)),
                None,
            )
            if match and r.source not in w.get("last_seen", {}):
                w.setdefault("last_seen", {})[r.source] = today
                state_changed = True
                if match.rank is not None:
                    info = f"rank {match.rank}/{len(r.scores)}"
                else:
                    first_metric = next(iter(match.metrics.items()), None)
                    info = f"{first_metric[0]} = {_format_metric_value(first_metric[1])}" if first_metric else "no metrics"
                new_data.append((r.source, info))

        if not new_data:
            print(f"No new benchmark data for {w['model']}.")
        else:
            print(f"Found new data for {w['model']}!")
            for source, info in new_data:
                msg = f"pondus: new benchmark data for {w['model']}\n{source}: {info}"
                print(f"  {source}: {info}")
                token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
                notified = False
                if token:
                    try:
                        with httpx.Client(timeout=10) as client:
                            resp = client.post(
                                f"https://api.telegram.org/bot{token}/sendMessage",
                                json={"chat_id": 6201770409, "text": msg},
                            )
                        notified = resp.status_code == 200
                    except Exception:
                        pass
                if not notified:
                    try:
                        subprocess.run(["deltos", msg], check=False)
                    except Exception:
                        print(f"  [notify] {msg}")

    if state_changed:
        _save_monitor_state(state)


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------

def _status_label(status: str) -> str:
    if status == "ok":
        return "OK"
    if status == "cached":
        return "Cached"
    if status == "unavailable":
        return "Unavailable"
    if status.startswith("error:"):
        return f"Error: {status[6:]}"
    return status


def _format_metric_value(v: MetricValue) -> str:
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _format_metric(metric_name: str, value: MetricValue) -> str:
    if isinstance(value, float):
        if metric_name in ("avg_percentile", "spread"):
            return f"{value:.3f}"
        return f"{value:.2f}"
    return str(value)


def _format_age(fetched_at: Optional[datetime], now: datetime) -> str:
    if fetched_at is None:
        return "unknown"
    delta = now - fetched_at
    total_hours = max(0, int(delta.total_seconds() // 3600))
    days = total_hours // 24
    hours = total_hours % 24
    return f"{days}d {hours}h"


def _aa_has_mixed_effort_variants(source: SourceResult) -> bool:
    efforts = {classify_effort_level(s.source_model_name) for s in source.scores}
    return len(efforts) > 1


def render_output(output: PondusOutput, output_format: str) -> str:
    if output_format == "json":
        return _render_json(output)
    elif output_format in ("table", "markdown"):
        if output.query.query_type == "sources":
            return _render_sources_table(output) if output_format == "table" else _render_sources_markdown(output)
        return _render_table(output) if output_format == "table" else _render_markdown(output)
    raise ValueError(f"Unknown format: {output_format}")


def _render_json(output: PondusOutput) -> str:
    def _serialize(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, PondusOutput):
            d: dict = {
                "timestamp": obj.timestamp,
                "query": _serialize(obj.query),
                "sources": [_serialize(s) for s in obj.sources],
            }
            if obj.source_tags is not None:
                d["source_tags"] = obj.source_tags
            return d
        if isinstance(obj, QueryInfo):
            d = {"type": obj.query_type}
            if obj.model is not None:
                d["model"] = obj.model
            if obj.models is not None:
                d["models"] = obj.models
            if obj.top is not None:
                d["top"] = obj.top
            return d
        if isinstance(obj, SourceResult):
            return {
                "source": obj.source,
                "fetched_at": obj.fetched_at,
                "status": obj.status,
                "scores": [_serialize(s) for s in obj.scores],
            }
        if isinstance(obj, ModelScore):
            return {
                "model": obj.model,
                "source_model_name": obj.source_model_name,
                "metrics": obj.metrics,
                "rank": obj.rank,
            }
        return obj

    return json.dumps(_serialize(output), indent=2, default=str)


def _render_table(output: PondusOutput) -> str:
    parts: list[str] = []
    for source in output.sources:
        status_str = _status_label(source.status)
        parts.append(f"{source.source} [{status_str}]")

        if not source.scores:
            parts.append("  No results\n")
            continue

        all_metrics = sorted({k for s in source.scores for k in s.metrics})
        columns = ["Rank", "Model"] + all_metrics
        widths = [len(c) for c in columns]

        rows_data: list[list[str]] = []
        for score in source.scores:
            rank = str(score.rank) if score.rank is not None else "-"
            row = [rank, score.model]
            for metric in all_metrics:
                val = score.metrics.get(metric)
                row.append(_format_metric(metric, val) if val is not None else "-")
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))
            rows_data.append(row)

        parts.append("  ".join(c.ljust(widths[i]) for i, c in enumerate(columns)))
        parts.append("  ".join("-" * w for w in widths))
        for row in rows_data:
            parts.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))

        if source.source == "artificial-analysis" and _aa_has_mixed_effort_variants(source):
            parts.append("")
            parts.append("  AA effort: (max) = Adaptive Reasoning Max Effort · standard = Non-reasoning High Effort · (low) = Non-reasoning Low Effort")

        parts.append("")

    return "\n".join(parts).rstrip()


def _render_sources_table(output: PondusOutput) -> str:
    now = datetime.now(timezone.utc)
    columns = ["Source", "Status", "Age", "Tags"]
    widths = [len(c) for c in columns]
    rows_data: list[list[str]] = []

    for source in output.sources:
        tags_list = (output.source_tags or {}).get(source.source.lower(), [])
        tags = ", ".join(tags_list) if tags_list else "-"
        status = _status_label(source.status)
        age = _format_age(source.fetched_at, now)
        row = [source.source, status, age, tags]
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
        rows_data.append(row)

    lines = ["  ".join(c.ljust(widths[i]) for i, c in enumerate(columns))]
    lines.append("  ".join("-" * w for w in widths))
    for row in rows_data:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def _render_markdown(output: PondusOutput) -> str:
    parts: list[str] = []
    for source in output.sources:
        parts.append(f"## {source.source}\n")
        status_str = _status_label(source.status)
        parts.append(f"Status: {status_str}\n")
        if not source.scores:
            parts.append("No results.\n")
            continue
        all_metrics = sorted({k for s in source.scores for k in s.metrics})
        columns = ["Rank", "Model"] + all_metrics
        parts.append("| " + " | ".join(columns) + " |")
        parts.append("| " + " | ".join("---" for _ in columns) + " |")
        for score in source.scores:
            rank = str(score.rank) if score.rank is not None else "-"
            row = [rank, score.model]
            for metric in all_metrics:
                val = score.metrics.get(metric)
                row.append(_format_metric(metric, val) if val is not None else "-")
            parts.append("| " + " | ".join(row) + " |")
        parts.append("")
    return "\n".join(parts).rstrip()


def _render_sources_markdown(output: PondusOutput) -> str:
    lines = ["| Source | Status | Tags |", "| --- | --- | --- |"]
    for source in output.sources:
        tags_list = (output.source_tags or {}).get(source.source.lower(), [])
        tags = ", ".join(tags_list) if tags_list else "-"
        status = _status_label(source.status)
        lines.append(f"| {source.source} | {status} | {tags} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_rank(
    config: Config,
    cache: Cache,
    aliases: AliasMap,
    output_format: str,
    top: Optional[int],
    source_filter: Optional[str],
    tag: Optional[str],
    sources_filter: Optional[str],
    aggregate: bool,
    min_sources: Optional[int],
    show_excluded: bool,
    max_age: Optional[int],
    show_freshness: bool,
    effort: str,
) -> None:
    results = fetch_all(config, cache)
    now = datetime.now(timezone.utc)

    if max_age is not None:
        filtered_results = []
        for result in results:
            if result.fetched_at is None:
                print(f"[{result.source}] excluded: data is unknown days old (--max-age {max_age})", file=sys.stderr)
                continue
            age_days = (now - result.fetched_at).total_seconds() / 86400
            if age_days > max_age:
                print(f"[{result.source}] excluded: data is {int(age_days)} days old (--max-age {max_age})", file=sys.stderr)
                continue
            filtered_results.append(result)
        results = filtered_results

    if tag is not None:
        tag_lower = tag.strip().lower()
        if tag_lower not in ("reasoning", "coding", "agentic", "general"):
            print(f"[error] Unknown tag: '{tag}'. Expected one of: reasoning, coding, agentic, general", file=sys.stderr)
            sys.exit(1)
        tags_by_source = _source_tags_for_output(config)
        results = [r for r in results if tag_lower in tags_by_source.get(r.source.lower(), [])]

    merged_sources = sources_filter or source_filter
    if merged_sources:
        requested = {s.strip().lower() for s in merged_sources.split(",") if s.strip()}
        if not requested:
            print("[error] --sources/--source requires at least one source name", file=sys.stderr)
            sys.exit(1)
        filtered = [r for r in results if r.source.lower() in requested]
        if not filtered:
            available = ", ".join(SOURCE_ORDER)
            print(f"[error] No matching sources in '{merged_sources}'. Available sources: {available}", file=sys.stderr)
            sys.exit(1)
        results = filtered

    if show_freshness:
        print("Data freshness:", file=sys.stderr)
        for result in results:
            freshness = _format_age(result.fetched_at, now)
            print(f"  {result.source:<20} {freshness}", file=sys.stderr)

    if any(r.source == "livebench" and r.scores for r in results):
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        month_name = month_names[LIVEBENCH_FROZEN_SINCE[1] - 1]
        print(f"[livebench] dataset frozen since {month_name} {LIVEBENCH_FROZEN_SINCE[0]} — scores are stale", file=sys.stderr)

    apply_aa_effort_filter(results, effort)

    if aggregate:
        threshold = min_sources if min_sources is not None else 2
        excluded_for_count = [] if show_excluded else _excluded_models(results, threshold)
        agg_result, excluded_list = aggregate_results(results, threshold, show_excluded)
        if not show_excluded:
            excluded_list = excluded_for_count

        if excluded_list:
            print(
                f"{len(excluded_list)} models excluded (appeared in fewer than {threshold} sources). Use --show-excluded to list.",
                file=sys.stderr,
            )
            if show_excluded:
                for model, count in excluded_list:
                    print(f"  {model} ({count})", file=sys.stderr)

        if top is not None:
            agg_result.scores = agg_result.scores[:top]
        results = [agg_result]
    elif top is not None:
        for result in results:
            result.scores = result.scores[:top]

    output = PondusOutput(
        timestamp=now,
        query=QueryInfo(query_type="rank", top=top),
        sources=results,
    )
    print(render_output(output, output_format))


def cmd_check(
    config: Config,
    cache: Cache,
    aliases: AliasMap,
    output_format: str,
    model: str,
    show_matches: bool,
) -> None:
    canonical = aliases.resolve(model)
    results = fetch_all(config, cache)

    filtered: list[SourceResult] = []
    for r in results:
        matching_scores = [
            s for s in r.scores
            if s.model.lower() == canonical or aliases.matches(s.source_model_name, canonical)
        ]
        if show_matches:
            for s in matching_scores:
                resolved = aliases.resolve(s.source_model_name)
                kind = "exact" if s.source_model_name.lower() == canonical else (
                    "alias" if resolved == canonical else "prefix"
                )
                print(f"[{r.source}]   {s.source_model_name!r}  ->  {canonical!r}  ({kind})", file=sys.stderr)
        filtered.append(SourceResult(
            source=r.source,
            fetched_at=r.fetched_at,
            status=r.status,
            scores=matching_scores,
        ))

    total_matches = sum(len(r.scores) for r in filtered)
    if total_matches == 0 and not show_matches:
        print(f"[warn] '{model}' not found in any source. Try: pondus check {model} --show-matches", file=sys.stderr)

    output = PondusOutput(
        timestamp=datetime.now(timezone.utc),
        query=QueryInfo(query_type="check", model=canonical),
        sources=filtered,
    )
    print(render_output(output, output_format))


def cmd_compare(
    config: Config,
    cache: Cache,
    aliases: AliasMap,
    output_format: str,
    model1: str,
    model2: str,
    effort: str,
) -> None:
    c1 = aliases.resolve(model1)
    c2 = aliases.resolve(model2)
    results = fetch_all(config, cache)
    apply_aa_effort_filter(results, effort)

    filtered = []
    for r in results:
        matching = [
            s for s in r.scores
            if aliases.resolve(s.source_model_name) in (c1, c2)
        ]
        filtered.append(SourceResult(
            source=r.source,
            fetched_at=r.fetched_at,
            status=r.status,
            scores=matching,
        ))

    output = PondusOutput(
        timestamp=datetime.now(timezone.utc),
        query=QueryInfo(query_type="compare", models=[c1, c2]),
        sources=filtered,
    )
    print(render_output(output, output_format))


def cmd_watch(
    config: Config,
    cache: Cache,
    aliases: AliasMap,
    model: str,
    interval: Optional[int],
    once: bool,
) -> None:
    canonical = aliases.resolve(model)
    interval_secs = interval if interval is not None else 3600

    while True:
        results = fetch_all(config, cache)
        covered = 0
        total_sources = len(results)
        status_lines: list[str] = []

        for r in results:
            matched = next(
                (s for s in r.scores
                 if s.model.lower() == canonical or aliases.matches(s.source_model_name, canonical)),
                None,
            )
            if matched is not None:
                covered += 1
                if matched.rank is not None:
                    rank_str = f"rank {matched.rank}/{len(r.scores)}"
                else:
                    rank_str = "no rank"
                metric_parts = sorted(
                    f"{name} {_format_metric(name, val)}"
                    for name, val in matched.metrics.items()
                    if name != "rank"
                )
                metrics_str = (", " + ", ".join(metric_parts)) if metric_parts else ""
                status_lines.append(f"  {r.source:<13} \u2713  {rank_str}{metrics_str}")
            else:
                status_lines.append(f"  {r.source:<13} \u2717  not yet indexed")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Watching: {model}  [{covered}/{total_sources} sources]  {now_str}")
        print()
        for line in status_lines:
            print(line)
        print()

        if covered == total_sources:
            print(f"All {total_sources} sources have data for {model}.")
            sys.exit(0)

        if once:
            print(f"{covered} of {total_sources} sources have data.")
            sys.exit(1)

        print(f"{covered} of {total_sources} sources have data. Rechecking in {interval_secs}s...")
        time.sleep(interval_secs)
        cache.clear()
        print("\n---\n")


def cmd_sources(config: Config, cache: Cache, output_format: str) -> None:
    results = fetch_all(config, cache)
    source_tags = _source_tags_for_output(config)
    output = PondusOutput(
        timestamp=datetime.now(timezone.utc),
        query=QueryInfo(query_type="sources"),
        sources=results,
        source_tags={k: v for k, v in source_tags.items()},
    )
    print(render_output(output, output_format))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        prog="pondus",
        description="Opinionated AI model benchmark aggregator",
    )
    parser.add_argument("--format", default="json", choices=["json", "table", "markdown", "md"],
                        help="Output format (default: json)")
    parser.add_argument("--refresh", action="store_true",
                        help="Bypass cache and re-fetch all sources")

    subparsers = parser.add_subparsers(dest="command")

    # rank
    rank_p = subparsers.add_parser("rank", help="Rank all models across sources")
    rank_p.add_argument("--top", type=int, default=None, help="Show top N models")
    rank_p.add_argument("--source", default=None, help="Filter to a single source name (case-insensitive)")
    rank_p.add_argument("--sources", default=None, help="Comma-separated source names (case-insensitive)")
    rank_p.add_argument("--tag", default=None, help="Filter to source tags: reasoning, coding, agentic, general")
    rank_p.add_argument("--aggregate", action="store_true", help="Produce a combined leaderboard across sources")
    rank_p.add_argument("--min-sources", type=int, default=None,
                        help="Minimum number of sources a model must appear in (default: 2 when --aggregate is set)")
    rank_p.add_argument("--show-excluded", action="store_true",
                        help="Show models excluded by --min-sources threshold when aggregating")
    rank_p.add_argument("--max-age", type=int, default=None, help="Exclude sources with data older than N days")
    rank_p.add_argument("--show-freshness", action="store_true", help="Show data age for each source")
    rank_p.add_argument("--effort", default="all", choices=["all", "max", "standard", "low"],
                        help="Filter AA results by reasoning effort level")

    # check
    check_p = subparsers.add_parser("check", help="Check a single model across all sources")
    check_p.add_argument("model", help="Model name (canonical or alias)")
    check_p.add_argument("--show-matches", action="store_true")

    # compare
    compare_p = subparsers.add_parser("compare", help="Compare two models head-to-head")
    compare_p.add_argument("model1", help="First model")
    compare_p.add_argument("model2", help="Second model")
    compare_p.add_argument("--effort", default="all", choices=["all", "max", "standard", "low"])

    # watch
    watch_p = subparsers.add_parser("watch", help="Watch a model across all sources until all have data")
    watch_p.add_argument("model", help="Model name (canonical or alias)")
    watch_p.add_argument("--interval", type=int, default=None, help="Interval in seconds for polling (default: 3600)")
    watch_p.add_argument("--once", action="store_true", help="Run once and exit with status code 1 if any source is missing data")

    # monitor
    monitor_p = subparsers.add_parser("monitor", help="Monitor models for new benchmark data")
    monitor_sub = monitor_p.add_subparsers(dest="monitor_command")
    monitor_add_p = monitor_sub.add_parser("add", help="Add a model to the watchlist")
    monitor_add_p.add_argument("model", help="Model name (canonical or alias)")
    monitor_sub.add_parser("list", help="List all watched models")
    monitor_remove_p = monitor_sub.add_parser("remove", help="Remove a model from the watchlist")
    monitor_remove_p.add_argument("model", help="Model name")
    monitor_sub.add_parser("check", help="Poll sources for new benchmark data for watched models")

    # sources
    subparsers.add_parser("sources", help="List all sources and their status")

    # refresh
    subparsers.add_parser("refresh", help="Force re-fetch all sources (clears cache)")

    # recommend
    recommend_p = subparsers.add_parser("recommend", help="Recommend models for a task type")
    recommend_p.add_argument("task", nargs="?", choices=VALID_TASKS, default=None,
                             help="Task type to recommend for")
    recommend_p.add_argument("--list-tasks", action="store_true", help="Print available task types with descriptions")
    recommend_p.add_argument("--top", type=int, default=5, help="Show top N models")
    recommend_p.add_argument("--effort", default="all", choices=["all", "max", "standard", "low"])

    args = parser.parse_args()

    output_format = "markdown" if args.format == "md" else args.format
    config = Config.load()
    cache = Cache(ttl_hours=config.ttl_hours)
    aliases = AliasMap.load(config.alias_path)

    if args.refresh:
        cache.clear()

    command = args.command or "rank"

    if command == "rank":
        cmd_rank(
            config, cache, aliases, output_format,
            top=args.top if command == "rank" else None,
            source_filter=args.source if command == "rank" else None,
            tag=args.tag if command == "rank" else None,
            sources_filter=args.sources if command == "rank" else None,
            aggregate=args.aggregate if command == "rank" else False,
            min_sources=args.min_sources if command == "rank" else None,
            show_excluded=args.show_excluded if command == "rank" else False,
            max_age=args.max_age if command == "rank" else None,
            show_freshness=args.show_freshness if command == "rank" else False,
            effort=args.effort if command == "rank" else "all",
        )
    elif command == "check":
        cmd_check(config, cache, aliases, output_format, args.model, args.show_matches)
    elif command == "compare":
        cmd_compare(config, cache, aliases, output_format, args.model1, args.model2, args.effort)
    elif command == "watch":
        cmd_watch(config, cache, aliases, args.model, args.interval, args.once)
    elif command == "sources":
        cmd_sources(config, cache, output_format)
    elif command == "refresh":
        cache.clear()
        print("Cache cleared. Re-fetching all sources...", file=sys.stderr)
        cmd_rank(config, cache, aliases, output_format,
                 top=None, source_filter=None, tag=None, sources_filter=None,
                 aggregate=False, min_sources=None, show_excluded=False,
                 max_age=None, show_freshness=False, effort="all")
    elif command == "recommend":
        cmd_recommend(
            config, cache, aliases,
            task=args.task or "",
            top=args.top,
            effort=args.effort,
            output_format=output_format,
            list_tasks=args.list_tasks,
        )
    elif command == "monitor":
        monitor_command = getattr(args, "monitor_command", None)
        if monitor_command == "add":
            cmd_monitor_add(args.model, aliases)
        elif monitor_command == "list":
            cmd_monitor_list()
        elif monitor_command == "remove":
            cmd_monitor_remove(args.model, aliases)
        elif monitor_command == "check":
            cmd_monitor_check(config, cache, aliases)
        else:
            monitor_p.print_help()


if __name__ == "__main__":
    _cli()
