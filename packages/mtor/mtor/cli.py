"""mtor CLI — local-mode dispatch for AI coding agents."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from mtor import __version__
from mtor.config import MtorConfig
from mtor.log import filter_reflections, filter_stalls, read_log, summary_stats
from mtor.worker import log_result, run_task

app = App(name="mtor", help="Architect-implementer dispatch for AI coding agents.", version=__version__)


@app.command
def run(prompt: str, provider: Annotated[str, Parameter(["--provider", "-p"])] = "", config_file: Annotated[str | None, Parameter(["--config", "-c"])] = None) -> None:
    config = MtorConfig.load(Path(config_file) if config_file else None)
    provider_name = provider or config.default_provider
    if not provider_name or provider_name not in config.providers:
        available = ", ".join(config.providers.keys()) or "none configured"
        print(json.dumps({"ok": False, "error": f"Unknown provider '{provider_name}'. Available: {available}"}))
        sys.exit(1)
    prov = config.providers[provider_name]
    print(f"[mtor] running on {prov.name} ({prov.model})...", file=sys.stderr)
    result = run_task(prompt, prov, config)
    log_result(result, config.log_file)
    output = {"ok": result.exit_code == 0, "provider": result.provider, "duration": result.duration_seconds, "files_created": result.files_created, "stall": result.stall.stall_type}
    if result.reflection:
        output["reflection"] = result.reflection
    if result.stall.is_stalled:
        output["stall_detail"] = result.stall.detail
    print(json.dumps(output))
    sys.exit(result.exit_code)


@app.command
def log(count: Annotated[int, Parameter(["--count", "-n"])] = 20, stalls_only: Annotated[bool, Parameter(["--stalls"])] = False, reflections_only: Annotated[bool, Parameter(["--reflections"])] = False, stats: Annotated[bool, Parameter(["--stats"])] = False, config_file: Annotated[str | None, Parameter(["--config", "-c"])] = None) -> None:
    config = MtorConfig.load(Path(config_file) if config_file else None)
    entries = read_log(config.log_file, limit=count)
    if stats:
        print(json.dumps(summary_stats(entries), indent=2))
        return
    if stalls_only:
        entries = filter_stalls(entries)
    elif reflections_only:
        entries = filter_reflections(entries)
    for entry in entries:
        status = "OK" if entry.succeeded else f"FAIL(stall={entry.stall})" if entry.is_stalled else "FAIL"
        print(f"{entry.timestamp}  {entry.provider:<10}  {status:<20}  {entry.duration}s  files={entry.files_created}")


@app.command
def doctor(config_file: Annotated[str | None, Parameter(["--config", "-c"])] = None) -> None:
    config = MtorConfig.load(Path(config_file) if config_file else None)
    checks = [{"provider": n, "model": p.model, "harness": p.harness, "has_key": p.api_key is not None} for n, p in config.providers.items()]
    print(json.dumps({"ok": all(c["has_key"] for c in checks), "coaching_file": str(config.coaching_file) if config.coaching_file else None, "providers": checks}, indent=2))
