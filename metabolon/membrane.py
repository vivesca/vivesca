"""vivesca — unified MCP server.

Composes tools, resources, and prompts using FastMCP 3's
FileSystemProvider. Each domain is a standalone .py file.
"""

from __future__ import annotations

import json
import logging
import time
import traceback
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.server.providers import FileSystemProvider
from fastmcp.tools.tool import ToolResult

from metabolon.metabolism.infection import record_infection
from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.server import RequestLogger

logger = logging.getLogger(__name__)

PHENOTYPE_MANIFEST = (
    "vivesca — unified MCP server. Tools prefixed by domain: "
    "deltos (Telegram), rheotaxis (search), fasti (calendar, HKT), "
    "gap_junction (WhatsApp, NEVER sends), histone (memory DB), "
    "navigator (browser), interoception (health/system)."
)

_src = Path(__file__).resolve().parent

# Rough chars-per-token ratio for estimation (conservative).
_CHARS_PER_TOKEN = 4


def _estimate_metabolic_cost(text: str) -> int:
    """Rough token count from character length — each token is a unit of metabolic cost."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _extract_substrate(result: ToolResult) -> str:
    """Pull substrate (text content) from ToolResult for metabolic cost estimation."""
    parts: list[str] = []
    for block in result.content:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(text)
    return "\n".join(parts)


def _summarize_traceback(exc: Exception, max_frames: int = 4) -> list[str]:
    """Return the most relevant traceback frames in a compact format."""
    if exc.__traceback__ is None:
        return []
    extracted_frames = traceback.extract_tb(exc.__traceback__)[-max_frames:]
    return [
        f"{Path(frame.filename).name}:{frame.lineno} in {frame.name}"
        for frame in extracted_frames
    ]


def _suggest_fix(tool_name: str, exc: Exception) -> str:
    """Return a concrete next step based on the failure mode."""
    error_text = str(exc).lower()

    if isinstance(exc, TimeoutError) or "timed out" in error_text:
        return "Retry the tool call or increase the upstream timeout if the dependency is slow."
    if isinstance(exc, FileNotFoundError) or "binary not found" in error_text:
        return "Verify the referenced binary or file exists and is on PATH, then rerun the tool."
    if isinstance(exc, PermissionError) or "permission denied" in error_text:
        return "Check filesystem permissions and any OS-level access grants required by this tool."
    if "api key" in error_text or "not set" in error_text or "credential" in error_text:
        return "Confirm the required environment variable or keychain credential is loaded before calling the tool."
    if isinstance(exc, ValueError):
        return f"Check the arguments passed to '{tool_name}' and validate required formats or enum values."
    return "Inspect the traceback summary and the underlying organelle dependency, then rerun after fixing the root cause."


def _format_tool_error(tool_name: str, exc: Exception) -> str:
    """Serialize tool-call failures into a structured debug payload."""
    payload = {
        "tool_name": tool_name,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback_summary": _summarize_traceback(exc),
        "suggested_fix": _suggest_fix(tool_name, exc),
    }
    return json.dumps(payload, indent=2)


class ToolTiming:
    """Single tool-call timing record."""

    __slots__ = ("tool", "latency_ms", "outcome")

    def __init__(self, tool: str, latency_ms: int, outcome: str) -> None:
        self.tool = tool
        self.latency_ms = latency_ms
        self.outcome = outcome


class TimingBuffer:
    """Rotating buffer of the last N tool-call timings (in-process, O(1) append)."""

    def __init__(self, maxlen: int = 100) -> None:
        self._buf: deque[ToolTiming] = deque(maxlen=maxlen)

    def record(self, timing: ToolTiming) -> None:
        self._buf.append(timing)

    def snapshot(self) -> list[ToolTiming]:
        return list(self._buf)


timing_buffer = TimingBuffer(maxlen=100)


class SensoryMiddleware(Middleware):
    """Emit a Stimulus for every tool call and resource read."""

    def __init__(self, collector: SensorySystem | None = None) -> None:
        self.collector = collector or SensorySystem()

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ) -> Any:
        tool_name: str = getattr(context.message, "name", "unknown")
        args = getattr(context.message, "arguments", None) or {}

        # Estimate input tokens from serialised arguments.
        try:
            args_text = json.dumps(args, default=str)
        except Exception:
            args_text = str(args)
        tokens_in = _estimate_metabolic_cost(args_text)

        start = time.perf_counter()
        error_msg: str | None = None
        outcome = Outcome.success
        result: Any = None

        try:
            result = await call_next(context)
            return result
        except Exception as exc:
            outcome = Outcome.error
            error_msg = _format_tool_error(tool_name, exc)
            raise ToolError(error_msg) from exc
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)

            # Record to in-memory rotating buffer for timing stats.
            try:
                timing_buffer.record(
                    ToolTiming(
                        tool=tool_name,
                        latency_ms=latency_ms,
                        outcome=outcome.value,
                    )
                )
            except Exception:
                logger.debug("Timing buffer record failed", exc_info=True)

            # Estimate output tokens.
            tokens_out = 0
            if result is not None:
                try:
                    tokens_out = _estimate_metabolic_cost(_extract_substrate(result))
                except Exception:
                    tokens_out = 0

            # Fire-and-forget: never let signal collection break a tool call.
            try:
                self.collector.append(
                    Stimulus(
                        tool=tool_name,
                        outcome=outcome,
                        substrate_consumed=tokens_in,
                        product_released=tokens_out,
                        response_latency=latency_ms,
                        error=error_msg,
                    )
                )
            except Exception:
                logger.debug("Stimulus collection failed", exc_info=True)

            # Hot-path repair: on error, attempt metaprompt repair.
            if outcome == Outcome.error and error_msg:
                try:
                    await self._acute_immune_response(tool_name, error_msg)
                except Exception:
                    logger.debug("Acute immune response failed", exc_info=True)

    async def _acute_immune_response(self, tool_name: str, error_msg: str) -> None:
        """Acute immune response: log the infection, then attempt metaprompt repair.

        Honest immunity — the organism logs every tool error to a structured
        infection log regardless of whether LLM repair is attempted or succeeds.
        Recurring patterns (same tool + same error fingerprint) are flagged as
        chronic infections and surfaced in the nightly homeostasis check.

        Fast-path — never raises, all exceptions caught and logged.
        """
        healed = False
        try:
            from metabolon.metabolism.gates import taste
            from metabolon.metabolism.repair import ImmuneRequest, immune_response
            from metabolon.metabolism.variants import Genome

            store = Genome()
            if tool_name in store.expressed_tools():
                current_desc = store.active_allele(tool_name)
                request = ImmuneRequest(
                    tool=tool_name,
                    current_description=current_desc,
                    failure_reason=error_msg,
                )
                repair_result = await immune_response(request)
                if repair_result.accepted and repair_result.candidate:
                    # Constitutional gate: judge against founding description
                    founding = store.founding_allele(tool_name)
                    judge_result = await taste(tool_name, founding, repair_result.candidate)
                    if judge_result.passed:
                        vid = store.express_variant(tool_name, repair_result.candidate)
                        store.promote(tool_name, vid)
                        logger.info("Acute immune response: promoted v%d for %s", vid, tool_name)
                        healed = True
        except Exception:
            logger.debug("Acute immune response failed for %s", tool_name, exc_info=True)
        finally:
            # Always record the infection event — healed or not.
            # This is the honest part: the organism knows what it detected
            # even when it cannot repair.
            try:
                record_infection(tool_name, error_msg, healed=healed)
            except Exception:
                logger.debug("Infection log failed for %s", tool_name, exc_info=True)


def assemble_organism(
    *,
    signal_collector: SensorySystem | None = None,
) -> FastMCP:
    """Assemble the organism — compose tools, resources, and prompts into a living MCP server."""
    mcp = FastMCP(
        "vivesca",
        instructions=PHENOTYPE_MANIFEST,
        providers=[
            FileSystemProvider(_src / "enzymes"),
            FileSystemProvider(_src / "codons"),
        ],
    )
    mcp.add_middleware(SensoryMiddleware(collector=signal_collector))

    # Guard: provider dirs must exist and contain .py files (0-tool server burned us 2026-03-28)
    for provider_dir in [_src / "enzymes", _src / "codons"]:
        py_files = list(provider_dir.glob("*.py"))
        non_init = [f for f in py_files if f.name != "__init__.py"]
        assert non_init, f"No tool modules in {provider_dir} — check FileSystemProvider paths"
    logger.info("vivesca assembled from %s", _src)

    return mcp


mcp = assemble_organism()


_FALLBACK_HOST = "127.0.0.1"
_FALLBACK_PORT = 8741
_CONFIG_PATH = Path.home() / ".config" / "vivesca" / "server.yaml"


def _absorb_genome() -> dict:
    """Absorb the organism's genome — read server config from ~/.config/vivesca/server.yaml."""
    if _CONFIG_PATH.exists():
        try:
            import yaml

            return yaml.safe_load(_CONFIG_PATH.read_text()) or {}
        except Exception:
            return {}
    return {}


def server_config() -> tuple[str, int]:
    """Return (host, port) from config file, with fallbacks."""
    genome = _absorb_genome()
    return genome.get("host", _FALLBACK_HOST), genome.get("port", _FALLBACK_PORT)


# Public constants for CLI reuse
DEFAULT_HOST, DEFAULT_PORT = server_config()


def _absorb_cofactors() -> None:
    """Load API keys from macOS Keychain into process env at startup."""
    import importlib.machinery
    import importlib.util

    from metabolon.cytosol import VIVESCA_ROOT

    path = str(VIVESCA_ROOT / "effectors" / "importin")
    try:
        loader = importlib.machinery.SourceFileLoader("keychain_env", path)
        spec = importlib.util.spec_from_file_location("keychain_env", path, loader=loader)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.load_keychain_env()
    except FileNotFoundError:
        pass  # keychain-env not present — keys loaded from environment instead


def main():
    """Entry point for `python -m vivesca` — supports stdio and http."""
    import argparse

    _absorb_cofactors()

    host, port = server_config()

    parser = argparse.ArgumentParser(description="vivesca MCP server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server instead of stdio")
    parser.add_argument("--host", default=host, help=f"HTTP bind address (default: {host})")
    parser.add_argument("--port", type=int, default=port, help=f"HTTP port (default: {port})")
    args = parser.parse_args()

    # Emit startup signal — frequency of these signals tracks crash/restart rate.
    try:
        collector = SensorySystem()
        collector.append(
            Stimulus(
                tool="server",
                outcome=Outcome.success,
                substrate_consumed=0,
                product_released=0,
                response_latency=0,
                context="startup",
            )
        )
    except Exception:
        pass

    if args.http:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
