"""vivesca — unified MCP server.

Composes tools, resources, and prompts using FastMCP 3's
FileSystemProvider. Each domain is a standalone .py file.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.server.providers import FileSystemProvider
from fastmcp.tools.tool import ToolResult

from metabolon.metabolism.infection import record_infection
from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus

logger = logging.getLogger(__name__)

PHENOTYPE_MANIFEST = (
    "vivesca — unified MCP server. Tools prefixed by domain: "
    "deltos (Telegram), noesis (search), fasti (calendar, HKT), "
    "keryx (WhatsApp, NEVER sends), oghma (memory DB), "
    "navigator (browser), checkpoint (health/system)."
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
            error_msg = str(exc)[:500]
            raise
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)

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
                        logger.info(
                            "Acute immune response: promoted v%d for %s", vid, tool_name
                        )
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
            FileSystemProvider(_src / "tools"),
            FileSystemProvider(_src / "codons"),
        ],
    )
    mcp.add_middleware(SensoryMiddleware(collector=signal_collector))
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

    path = str(VIVESCA_ROOT / "effectors" / "keychain-env")
    loader = importlib.machinery.SourceFileLoader("keychain_env", path)
    spec = importlib.util.spec_from_file_location("keychain_env", path, loader=loader)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.load_keychain_env()


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
