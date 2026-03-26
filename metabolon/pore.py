# src/vivesca/cli.py
"""vivesca CLI — scaffold and validate MCP tool ecosystems."""

import os
import sys
from datetime import UTC
from pathlib import Path

import click


@click.group()
@click.version_option(package_name="metabolon")
def cli():
    """Vivesca — a living organism."""
    pass


@cli.command()
@click.option("--http", is_flag=True, help="Run as HTTP server instead of stdio")
@click.option("--host", default=None, help="HTTP bind address (default: 127.0.0.1)")
@click.option("--port", type=int, default=None, help="HTTP port (default: 8741)")
def serve(http: bool, host: str | None, port: int | None):
    """Run as MCP server."""
    from metabolon.membrane import DEFAULT_HOST, DEFAULT_PORT, assemble_organism

    mcp = assemble_organism()
    if http:
        mcp.run(
            transport="streamable-http",
            host=host or DEFAULT_HOST,
            port=port or DEFAULT_PORT,
        )
    else:
        mcp.run(transport="stdio")


@cli.command()
def reload():
    """Restart the HTTP server by bouncing the LaunchAgent."""
    import subprocess

    label = "com.vivesca.mcp"
    plist = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    if not os.path.exists(plist):
        click.echo(f"LaunchAgent not found: {plist}", err=True)
        sys.exit(1)
    subprocess.run(["launchctl", "unload", plist], check=True)
    subprocess.run(["launchctl", "load", plist], check=True)
    click.echo(f"Reloaded {label}")


@cli.command()
@click.argument("name")
@click.option(
    "--description",
    "-d",
    default="An MCP server built with vivesca.",
    help="Project description.",
)
def init(name: str, description: str):
    """Scaffold a new MCP server project."""
    from metabolon.gastrulation.init import scaffold_project

    target = Path.cwd() / name
    scaffold_project(name, target, description)
    click.echo(f"Created {name}/ — cd {name} && uv sync to get started.")


@cli.command()
@click.argument("name", default="epigenome")
def epigenome(name: str):
    """Scaffold a new epigenome (instance repo) for this organism.

    Creates the directory structure for a personalised vivesca instance:
    credentials, config, launchd automation, and a default constitution.
    The epigenome expresses the genome — override defaults to personalise.
    """
    from metabolon.gastrulation.epigenome import scaffold_epigenome

    target = Path.cwd() / name
    scaffold_epigenome(target)
    click.echo(
        f"Epigenome created at ./{name}. "
        "Add your credentials, customise genome.md, then run vivesca."
    )


@cli.command("receptor-health")
@click.option(
    "--output",
    "-o",
    default=None,
    help="Write report to this path (default: receptor-health.md in cwd).",
)
def receptor_health(output: str | None):
    """Run integrin_probe + integrin_apoptosis_check and write receptor-health.md.

    Deterministic health check — no LLM needed. Classifies all receptors by
    activation state, reports anoikis candidates, and appends retirement
    candidates to ~/epigenome/chromatin/receptor-retirement.md.

    Exit 0 = clean or quiescent only. Exit 1 = anoikis candidates found.
    """
    from datetime import datetime

    from metabolon.tools.integrin import integrin_apoptosis_check, integrin_probe

    probe = integrin_probe()
    apoptosis = integrin_apoptosis_check()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Receptor Health — {now}\n",
        "\n## Attachment Integrity\n",
        f"- Total receptors: {probe.total_receptors}",
        f"- Total references: {probe.total_references}",
        f"- Attached: {probe.attached}",
        f"- Detached: {len(probe.detached)}",
        f"- Mechanically silent: {len(probe.mechanically_silent)}",
        f"- Focal adhesion risks: {len(probe.focal_adhesions)}",
        "",
        "## Activation State",
        apoptosis.summary,
        "",
    ]

    if apoptosis.anoikis_candidates:
        lines.append("## Anoikis Candidates (retirement flagged)")
        for r in apoptosis.anoikis_candidates:
            lines.append(f"- {r}")
        lines.append("")

    if apoptosis.quiescent:
        lines.append("## Quiescent (bent but ligands healthy)")
        for r in apoptosis.quiescent:
            lines.append(f"- {r}")
        lines.append("")

    if probe.detached:
        lines.append("## Detached References")
        for entry in probe.detached:
            lines.append(f"- {entry['receptor']}: `{entry['binary']}`")
        lines.append("")

    verdict = (
        "NEEDS_ATTENTION"
        if (apoptosis.anoikis_candidates or probe.detached)
        else "HEALTHY"
    )
    lines.append(f"## Verdict: {verdict}")
    if apoptosis.retirement_log_updated:
        lines.append(
            f"\nAnoikis candidates logged to ~/epigenome/chromatin/receptor-retirement.md"
        )

    report = "\n".join(lines) + "\n"

    out_path = Path(output) if output else Path.cwd() / "receptor-health.md"
    out_path.write_text(report)
    click.echo(f"receptor-health: {verdict} → {out_path}")

    raise SystemExit(1 if apoptosis.anoikis_candidates else 0)


@cli.group()
def add():
    """Add a component to the current project."""
    pass


@add.command("tool")
@click.argument("name")
@click.option("--domain", "-d", help="Tool domain prefix (default: derived from name).")
@click.option("--verb", "-v", help="Tool verb (default: derived from name).")
@click.option("--description", default="TODO: describe this tool.", help="Tool description.")
@click.option("--read-only/--no-read-only", default=True, help="Whether tool is read-only.")
def add_tool(name: str, domain: str | None, verb: str | None, description: str, read_only: bool):
    """Add a tool to the current project.

    NAME can be 'domain_verb' (e.g., 'weather_fetch') or just 'domain'
    with --verb flag.
    """
    from metabolon.gastrulation.add import graft_tool

    if "_" in name and not domain:
        parts = name.split("_", 1)
        domain, verb = parts[0], parts[1]
    elif not domain:
        domain = name
    if not verb:
        verb = "get"

    path = graft_tool(
        Path.cwd(),
        domain=domain,
        verb=verb,
        description=description,
        read_only=read_only,
    )
    click.echo(f"Created {path.relative_to(Path.cwd())}")


@add.command("prompt")
@click.argument("name")
@click.option("--description", default="TODO: describe this prompt.", help="Prompt description.")
def add_prompt(name: str, description: str):
    """Add a prompt to the current project."""
    from metabolon.gastrulation.add import graft_prompt

    path = graft_prompt(Path.cwd(), name=name, description=description)
    click.echo(f"Created {path.relative_to(Path.cwd())}")


@add.command("resource")
@click.argument("name")
@click.option(
    "--description",
    default="TODO: describe this resource.",
    help="Resource description.",
)
@click.option("--uri-path", default="", help="Custom URI path (default: name).")
def add_resource(name: str, description: str, uri_path: str):
    """Add a resource to the current project."""
    from metabolon.gastrulation.add import graft_resource

    path = graft_resource(
        Path.cwd(), name=name, description=description, uri_path=uri_path
    )
    click.echo(f"Created {path.relative_to(Path.cwd())}")


@cli.command()
def check():
    """Validate project against vivesca conventions."""
    from metabolon.gastrulation.check import probe_gastrulation

    issues = probe_gastrulation(Path.cwd())
    if not issues:
        click.echo("All checks passed.")
    else:
        click.echo(f"Found {len(issues)} issue(s):\n")
        for issue in issues:
            click.echo(f"  - {issue}")
        raise SystemExit(1)


@cli.group()
def hooks():
    """Check and repair ~/.claude symlinks."""
    pass


def _hooks_status():
    """Return (issues, hook_is_symlink) where issues is a list of problem strings."""
    from metabolon.cytosol import VIVESCA_ROOT

    claude = Path.home() / ".claude"
    expected = {
        "hooks": VIVESCA_ROOT / "membrane" / "cytoskeleton",
        "settings.json": VIVESCA_ROOT / "membrane" / "expression.json",
        "CLAUDE.md": VIVESCA_ROOT / "membrane" / "phenotype.md",
    }
    issues = []
    for name, target in expected.items():
        link = claude / name
        if not link.is_symlink():
            issues.append(f"{name}: not a symlink (is {'dir' if link.is_dir() else 'file' if link.exists() else 'missing'})")
        elif link.resolve() != target.resolve():
            issues.append(f"{name}: points to {os.readlink(link)!r}, expected {target}")

    skills_dir = claude / "skills"
    if skills_dir.exists():
        for skill in skills_dir.iterdir():
            if skill.is_symlink() and not skill.exists():
                issues.append(f"skills/{skill.name}: broken -> {os.readlink(skill)}")

    return issues


@hooks.command("check")
def hooks_check():
    """Verify ~/.claude symlinks are intact."""
    issues = _hooks_status()
    if not issues:
        click.echo("HEALTHY")
    else:
        click.echo("BROKEN:")
        for issue in issues:
            click.echo(f"  - {issue}")
        raise SystemExit(1)


@hooks.command("repair")
def hooks_repair():
    """Fix broken ~/.claude symlinks."""
    from metabolon.cytosol import VIVESCA_ROOT

    claude = Path.home() / ".claude"
    repairs = {
        "hooks": VIVESCA_ROOT / "membrane" / "cytoskeleton",
        "settings.json": VIVESCA_ROOT / "membrane" / "expression.json",
        "CLAUDE.md": VIVESCA_ROOT / "membrane" / "phenotype.md",
    }
    fixed = []
    for name, target in repairs.items():
        link = claude / name
        if link.is_symlink() and link.resolve() == target.resolve():
            continue
        if link.exists() or link.is_symlink():
            if link.is_dir() and not link.is_symlink():
                import shutil
                shutil.rmtree(link)
            else:
                link.unlink()
        link.symlink_to(target)
        fixed.append(f"{name} -> {target}")

    skills_dir = claude / "skills"
    receptors = VIVESCA_ROOT / "membrane" / "receptors"
    if skills_dir.exists():
        for skill in skills_dir.iterdir():
            if skill.is_symlink() and not skill.exists():
                new_target = receptors / skill.name
                if new_target.exists():
                    skill.unlink()
                    skill.symlink_to(new_target)
                    fixed.append(f"skills/{skill.name} -> {new_target}")

    if fixed:
        for item in fixed:
            click.echo(f"Fixed: {item}")
    else:
        click.echo("Nothing to repair.")


# ── metabolise (top-level) ───────────────────────────────────────────

# Common words excluded from chain-seed detection (deterministic, no LLM)
_COMMON_WORDS = frozenset(
    {
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "among",
        "around",
        "because",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "could",
        "design",
        "during",
        "enable",
        "every",
        "first",
        "from",
        "ideas",
        "instead",
        "into",
        "itself",
        "might",
        "model",
        "more",
        "never",
        "other",
        "rather",
        "right",
        "second",
        "should",
        "since",
        "still",
        "system",
        "their",
        "themselves",
        "there",
        "these",
        "thing",
        "things",
        "think",
        "those",
        "three",
        "through",
        "toward",
        "under",
        "until",
        "using",
        "what",
        "whatever",
        "where",
        "whether",
        "which",
        "while",
        "whose",
        "without",
        "would",
        "approach",
        "based",
        "being",
        "build",
        "change",
        "clear",
        "different",
        "direct",
        "existing",
        "general",
        "given",
        "going",
        "great",
        "having",
        "human",
        "important",
        "large",
        "likely",
        "makes",
        "making",
        "means",
        "needs",
        "often",
        "point",
        "possible",
        "process",
        "provide",
        "really",
        "reason",
        "require",
        "result",
        "single",
        "small",
        "specific",
        "state",
        "structure",
        "support",
        "taken",
        "understanding",
        "value",
        "within",
        "works",
        "world",
    }
)


def _extract_key_nouns(text: str) -> set[str]:
    """Extract significant words (>5 chars, not common) from text."""
    import re

    words = re.findall(r"[a-z][a-z]+", text.lower())
    return {w for w in words if len(w) > 5 and w not in _COMMON_WORDS}


def _detect_chain_seeds(result: str, existing_seeds: list[str]) -> list[str]:
    """Detect novel concepts in a metabolised result for automatic chaining.

    Extracts key noun phrases from the result and compares against all
    previously-processed seeds. Concepts that appear in the product but
    not in any original seed become candidate chain seeds.

    Returns up to 2 new seed phrases. Deterministic — no LLM calls.
    """
    result_nouns = _extract_key_nouns(result)

    # Build the set of concepts already covered by existing seeds
    covered = set()
    for s in existing_seeds:
        covered |= _extract_key_nouns(s)

    novel = sorted(result_nouns - covered)  # sorted for determinism
    if not novel:
        return []

    # Build seed phrases from clusters of up to 3 adjacent novel concepts
    chain_seeds: list[str] = []
    i = 0
    while i < len(novel) and len(chain_seeds) < 2:
        phrase_words = novel[i : i + 3]
        chain_seeds.append(" ".join(phrase_words))
        i += 3

    return chain_seeds


def _word_set(text: str) -> set[str]:
    """Tokenize text into a lowercase word set for similarity comparison."""
    return {w.lower() for w in text.split() if len(w) >= 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


DIVERGENCE_TEMPLATE = """\
You are exploring an idea. Cast wide — dimensions, implications, connections, analogies. No filter yet.

Idea: {seed}

Expand this idea in 200-400 words."""

CRYSTALLISATION_TEMPLATE = """\
Read this expansion and compress it to ONE sentence — the essential insight. Strip everything that isn't load-bearing.

Expansion:
{expansion}

One sentence:"""

SELECTION_PRESSURE_TEMPLATE = """\
You are the adversarial pusher in an idea metabolism cycle. Apply ONE push from this taxonomy — whichever exposes the biggest weakness:

- "Just this?" — scope too narrow, missing dimensions
- "Am I lazy?" — not deep enough, something hiding
- "Make it real" — too theoretical, needs concrete mechanism
- "Perfect?" — find the gap, what breaks under load
- "Future me will understand?" — not self-documenting

Current compression: {compression}

Pick the push that exposes the biggest weakness. State which push and the specific challenge in 2-3 sentences. Do NOT expand or solve."""

ADAPTATION_TEMPLATE = """\
You were exploring this idea:
{seed}

Your current compression: {previous_compression}

An adversary pushed back:
{push}

Respond to the push. Go deeper. 200-400 words."""


def _exocytose(result: str, seed: str, title: str | None, draft_model: str = "gemini"):
    """Draft a spore from crystallised result and publish via sarcio."""
    import subprocess as _sp
    from datetime import datetime

    symbiont = _acquire_catalyst()
    post_title = title or seed[:60]
    slug = post_title.lower().replace(" ", "-")
    # Remove non-alphanumeric except hyphens
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    prompt = f"""Write a spore for terryli.hm. Voice: clear, direct, slightly wry. Prose, not bullets. 800-1200 words.

Crystallised insight:
{result}

Include frontmatter:
---
title: "{post_title}"
description: "one-line description"
pubDatetime: {timestamp}
draft: false
tags: [ai, agents, design, vivesca]
---"""

    try:
        content = symbiont.transduce(draft_model, prompt, timeout=120)
        post_path = Path.home() / "notes" / "Writing" / "Blog" / "Published" / f"{slug}.md"
        post_path.write_text(content)
        click.echo(f"Drafted: {post_path}")

        r = _sp.run(
            ["sarcio", "publish", slug, "--push"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        click.echo(f"Published: {r.stdout.strip()}")
    except Exception as e:
        click.echo(f"Auto-publish error: {e}")


def _acquire_catalyst():
    """Import and return the shared llm module."""
    from metabolon.cytosol import VIVESCA_ROOT

    from metabolon import symbiont as llm

    return llm


@cli.command()
@click.argument("seed")
@click.option("--expander", default="gemini", help="Model for expansion (default: gemini)")
@click.option("--pusher", default="claude", help="Model for adversarial pushes (default: claude)")
@click.option("--rounds", default=5, help="Max rounds before stopping (default: 5)")
@click.option("--output", "-o", default=None, help="Write crystallised result to file")
@click.option("--no-publish", is_flag=True, help="Skip auto-publish (default: publish)")
@click.option("--title", default=None, help="Post title (defaults to first 60 chars of seed)")
@click.option(
    "--no-chain",
    is_flag=True,
    help="Disable automatic chaining of metabolised products",
)
def metabolise(seed, expander, pusher, rounds, output, no_publish, title, no_chain):
    """Metabolise anything — substrates, ideas, or batch.

    SEED is a substrate (dna, phenotype, crystals, respiration, all),
    a seed idea string, or a JSON file path for batch parallel.
    """
    from metabolon.metabolism.substrates import receptor_catalog

    # ── Substrate mode: known biological name ─────────────────────
    registry = receptor_catalog()
    if seed in registry or seed == "all":
        targets = list(registry.keys()) if seed == "all" else [seed]
        for i, name in enumerate(targets):
            if i > 0:
                click.echo("\n" + "=" * 60 + "\n")
            click.echo(_run_substrate(name, days=30))
        return

    # ── Batch mode: JSON file with multiple seeds ─────────────────
    if Path(seed).exists() and seed.endswith(".json"):
        import concurrent.futures
        import json as _json

        seeds = _json.loads(Path(seed).read_text())
        click.echo(f"=== Batch: {len(seeds)} seeds (parallel) ===\n")

        # Track all seed texts for chain-detection (across all depths)
        all_seed_texts: list[str] = [item["seed"] for item in seeds]

        # Queue: list of (item_dict, depth) — original seeds are depth 0
        queue: list[tuple[dict, int]] = [(item, 0) for item in seeds]
        max_chain_depth = 2

        def _run_one(item):
            import subprocess as _sp

            cmd = [
                "uv",
                "run",
                "vivesca-dev",
                "metabolise",
                item["seed"],
                "--expander",
                expander,
                "--pusher",
                pusher,
                "--rounds",
                str(rounds),
                "--no-chain",
            ]
            if not no_publish:
                cmd += ["--publish", "--title", item.get("title", item["seed"][:60])]
            if output:
                slug = item.get("slug", item["seed"][:30].replace(" ", "-"))
                cmd += ["-o", str(Path(output).parent / f"{slug}.md")]
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
            r = _sp.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,
                cwd=str(Path(__file__).resolve().parent.parent.parent),
                env=env,
            )
            return item.get("slug", item["seed"][:30]), r.stdout

        while queue:
            # Process current batch in parallel
            batch = queue[:]
            queue.clear()

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                future_to_meta = {
                    pool.submit(_run_one, item): (item, depth) for item, depth in batch
                }
                for f in concurrent.futures.as_completed(future_to_meta):
                    _item, depth = future_to_meta[f]
                    slug, out = f.result()
                    click.echo(f"[{slug}] done")
                    if out:
                        for line in out.strip().split("\n")[-3:]:
                            click.echo(f"  {line}")

                    # ── Chain detection ────────────────────────────
                    if not no_chain and depth < max_chain_depth and out:
                        # Extract the crystallised result from subprocess output
                        result_line = ""
                        for line in out.strip().split("\n"):
                            if line.startswith("Result:"):
                                result_line = line[len("Result:") :].strip()
                                break
                        if result_line:
                            chain_seeds = _detect_chain_seeds(result_line, all_seed_texts)
                            for cs in chain_seeds:
                                click.echo(f"  \u27f6 Chain: spawned '{cs}' from product")
                                all_seed_texts.append(cs)
                                chain_item = {
                                    "seed": cs,
                                    "slug": cs[:30].replace(" ", "-"),
                                    "title": cs[:60],
                                }
                                queue.append((chain_item, depth + 1))
        return

    symbiont = _acquire_catalyst()

    header = f"─── Metabolise: {seed} "
    header += "─" * max(1, 50 - len(header))
    click.echo(header)
    click.echo(f"Expander: {expander} | Pusher: {pusher}\n")

    previous_compression = None
    final_compression = None

    for round_num in range(1, rounds + 1):
        # ── Expand or Deepen ─────────────────────────────────────────
        if round_num == 1:
            expand_prompt = DIVERGENCE_TEMPLATE.format(seed=seed)
        else:
            expand_prompt = ADAPTATION_TEMPLATE.format(
                seed=seed,
                previous_compression=previous_compression,
                push=push_text,  # noqa: F821 — set in prior iteration
            )

        try:
            expansion = symbiont.transduce(expander, expand_prompt, timeout=120)
        except Exception as e:
            click.echo(f"Round {round_num} [{expander}]: ERROR — {e}")
            break

        # ── Compress ─────────────────────────────────────────────────
        compress_prompt = CRYSTALLISATION_TEMPLATE.format(expansion=expansion)
        try:
            compression = symbiont.transduce(expander, compress_prompt, timeout=120)
        except Exception as e:
            click.echo(f"Round {round_num} [{expander} compress]: ERROR — {e}")
            break

        click.echo(f"Round {round_num} [{expander}]: {compression}")
        final_compression = compression

        # ── Convergence check ────────────────────────────────────────
        if previous_compression is not None:
            similarity = _jaccard(_word_set(compression), _word_set(previous_compression))
            if similarity > 0.6:
                click.echo(f"  ⟳ Converged (similarity: {similarity:.2f})\n")
                break

        previous_compression = compression

        # ── Push (not on last round) ─────────────────────────────────
        if round_num < rounds:
            push_prompt = SELECTION_PRESSURE_TEMPLATE.format(compression=compression)
            try:
                push_text = symbiont.transduce(pusher, push_prompt, timeout=120)
            except Exception as e:
                click.echo(f"Round {round_num + 1} [{pusher} push]: ERROR — {e}")
                break

            # Truncate push display to first sentence for readability
            push_summary = push_text.split("\n")[0]
            click.echo(f"Round {round_num + 1} [{pusher} push]: {push_summary}")

    # ── Final output ─────────────────────────────────────────────────
    if final_compression:
        click.echo(f"Result: {final_compression}")
    click.echo("─" * 50)

    if output and final_compression:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(final_compression + "\n")
        click.echo(f"Written to {out_path}")

    if not no_publish and final_compression:
        _exocytose(final_compression, seed, title, expander)


# ── metabolism subgroup ──────────────────────────────────────────────


@cli.group()
def metabolism():
    """Metabolism subsystem — sense, select, act, report."""
    pass


def _run_substrate(name: str, days: int) -> str:
    """Run the sense -> candidates -> act -> report cycle for a substrate.

    Returns the formatted report string.
    """
    from metabolon.metabolism.substrates import receptor_catalog

    registry = receptor_catalog()
    cls = registry[name]
    substrate = cls()
    sensed = substrate.sense(days=days)
    cands = substrate.candidates(sensed)
    acted = [substrate.act(c) for c in cands]
    return substrate.report(sensed, acted)


@metabolism.command("run")
@click.argument("target")
@click.option("--days", default=30, help="Signal window in days.")
def metabolism_run(target: str, days: int):
    """Run sense -> select -> act -> report cycle for a substrate.

    TARGET is a substrate name (phenotype, dna, crystals, respiration, all).
    Legacy names (tools, constitution, memory) also accepted.
    """
    from metabolon.metabolism.substrates import receptor_catalog

    # Accept both biological and legacy names
    legacy_map = {
        "tools": "phenotype",
        "constitution": "executive",
        "dna": "executive",
        "memory": "consolidation",
        "crystals": "consolidation",
    }
    registry = receptor_catalog()

    if target == "all":
        targets = list(registry.keys())
    elif target in registry:
        targets = [target]
    elif target in legacy_map:
        targets = [legacy_map[target]]
    else:
        click.echo(
            f"Unknown target: {target}. Available: {', '.join(sorted(registry.keys()))}, all"
        )
        raise SystemExit(1)

    for i, name in enumerate(targets):
        if i > 0:
            click.echo("\n" + "=" * 60 + "\n")
        click.echo(_run_substrate(name, days=days))


@metabolism.command("init")
def metabolism_init():
    """Seed genome from current tool descriptions."""
    import asyncio

    from metabolon.membrane import assemble_organism
    from metabolon.metabolism.variants import Genome

    store = Genome()
    server = assemble_organism()

    tools = asyncio.run(server.expressed_tools())
    count = 0
    for tool in tools:
        if tool.description:
            store.seed_tool(tool.name, tool.description)
            count += 1

    click.echo(f"Initialized {count} tool(s) in variant store.")


@metabolism.command("status")
def metabolism_status():
    """Show per-tool emotion and variant info."""
    from datetime import datetime, timedelta

    from metabolon.metabolism.fitness import sense_affect
    from metabolon.metabolism.signals import SensorySystem
    from metabolon.metabolism.variants import Genome

    collector = SensorySystem()
    store = Genome()

    since = datetime.now(UTC) - timedelta(days=7)
    signals = collector.recall_since(since)
    emotions = sense_affect(signals)

    tools = store.expressed_tools()
    if not tools and not emotions:
        click.echo("No tools or stimuli found. Run 'vivesca-dev metabolism init' first.")
        return

    click.echo(f"Stimuli (last 7 days): {len(signals)}")
    click.echo(f"Tools in genome: {len(tools)}\n")

    for tool in sorted(set(list(emotions.keys()) + tools)):
        e = emotions.get(tool)
        variants = store.allele_variants(tool) if tool in tools else []

        if e:
            val_str = f"{e.valence:.3f}" if e.valence is not None else "N/A"
            click.echo(
                f"  {tool}: valence={val_str} "
                f"activations={e.activations} success_rate={e.success_rate:.1%} "
                f"variants={len(variants)}"
            )
        else:
            click.echo(f"  {tool}: no stimuli, variants={len(variants)}")


@metabolism.command("sweep")
def metabolism_sweep():
    """Run natural selection sweep across tools with below-median valence."""
    import asyncio
    from datetime import datetime, timedelta

    from metabolon.metabolism.fitness import sense_affect
    from metabolon.metabolism.gates import reflex_check, taste
    from metabolon.metabolism.signals import SensorySystem
    from metabolon.metabolism.sweep import mutate, recombine, select
    from metabolon.metabolism.variants import Genome

    collector = SensorySystem()
    store = Genome()

    since = datetime.now(UTC) - timedelta(days=7)
    stimuli = collector.recall_since(since)

    if not stimuli:
        click.echo("No stimuli found. Accumulate usage data first.")
        return

    emotions = sense_affect(stimuli)
    click.echo(f"Computed emotion for {len(emotions)} tool(s) from {len(stimuli)} stimuli.")

    candidates = select(emotions)
    if not candidates:
        click.echo("No candidates — all tools above median valence.")
        return

    click.echo(f"Candidates: {', '.join(candidates)}")

    async def run_sweep() -> int:
        promoted = 0
        for tool_name in candidates:
            if tool_name not in store.expressed_tools():
                click.echo(f"  {tool_name}: not in genome, skipping")
                continue

            current = store.active_allele(tool_name)
            founding = store.founding_allele(tool_name)
            variants = store.allele_variants(tool_name)

            # Choose mutation strategy
            non_active = [
                v for v in variants if v != store._read_meta(tool_name)["active"] and v != 0
            ]
            if non_active:
                v_b_text = (store._locus_dir(tool_name) / f"v{non_active[0]}.md").read_text()
                candidate_desc = await recombine(tool_name, founding, v_b_text, current)
            else:
                e = emotions.get(tool_name)
                failure_mode = (
                    "below median valence"
                    if e and e.valence is not None
                    else "insufficient stimulus data"
                )
                candidate_desc = await mutate(tool_name, current, failure_mode)

            # Reflex check (deterministic gate)
            gate = reflex_check(candidate_desc)
            if not gate.passed:
                click.echo(f"  {tool_name}: reflex failed — {gate.reason}")
                continue

            # Taste (enzymatic judge) with founding genome as reference
            judge = await taste(tool_name, founding, candidate_desc)
            if not judge.passed:
                click.echo(f"  {tool_name}: taste rejected — {judge.reason}")
                continue

            vid = store.express_variant(tool_name, candidate_desc)
            store.promote(tool_name, vid)
            click.echo(f"  {tool_name}: promoted v{vid}")
            promoted += 1

        return promoted

    promoted = asyncio.run(run_sweep())
    click.echo(f"\nSelection complete. Promoted {promoted}/{len(candidates)}.")


@metabolism.command("audit")
@click.option("--days", default=30, help="Number of days of signals to consider.")
def metabolism_audit(days: int):
    """Health check — audit DNA against signal evidence."""
    import re
    from datetime import datetime, timedelta

    from metabolon.metabolism.signals import SensorySystem

    constitution_path = Path.home() / ".local" / "share" / "vivesca" / "genome.md"
    if not constitution_path.exists():
        click.echo("No constitution found at " + str(constitution_path))
        raise SystemExit(1)

    constitution = constitution_path.read_text()

    # ── Extract bold-prefixed rules ──────────────────────────────────
    # Matches lines like "**Token-conscious.** ..." or "**Opus default.** ..."
    rule_pattern = re.compile(r"\*\*([^*]+?)\.?\*\*\s*(.*)")
    rules: list[dict] = []
    for line in constitution.splitlines():
        stripped = line.strip()
        # Only consider lines that start with bold marker (rule declarations)
        if not stripped.startswith("**"):
            continue
        m = rule_pattern.match(stripped)
        if m:
            title = m.group(1).strip()
            body = m.group(2).strip()
            rules.append({"title": title, "body": body, "line": stripped})

    if not rules:
        click.echo("No bold-prefixed rules found in constitution.")
        return

    click.echo(f"Found {len(rules)} constitutional rule(s).\n")

    # ── Read recent signals ──────────────────────────────────────────
    collector = SensorySystem()
    since = datetime.now(UTC) - timedelta(days=days)
    signals = collector.recall_since(since)
    click.echo(f"Signals (last {days} days): {len(signals)}\n")

    # Build a set of tool names that appear in signals
    signal_tools: set[str] = set()
    for s in signals:
        signal_tools.add(s.tool)
        # Also add domain prefix (e.g., "checkpoint" from "checkpoint_list")
        if "_" in s.tool:
            signal_tools.add(s.tool.split("_")[0])

    # ── Cross-reference rules with signal evidence ───────────────────
    with_evidence: list[dict] = []
    without_evidence: list[dict] = []

    for rule in rules:
        # Build search text: title + body, lowercased
        search_text = (rule["title"] + " " + rule["body"]).lower()
        # Extract potential tool-like words (alphanumeric + underscore)
        words = set(re.findall(r"[a-z][a-z0-9_]+", search_text))

        # Check if any signal tool name appears in the rule text
        matched_tools = words & {t.lower() for t in signal_tools}
        rule["matched_tools"] = matched_tools

        if matched_tools:
            with_evidence.append(rule)
        else:
            without_evidence.append(rule)

    # ── Detect potential conflicts (overlapping scope) ───────────────
    conflicts: list[tuple[dict, dict]] = []
    for i, r1 in enumerate(rules):
        for r2 in rules[i + 1 :]:
            t1 = r1.get("matched_tools", set())
            t2 = r2.get("matched_tools", set())
            overlap = t1 & t2
            if overlap and len(overlap) >= 1:
                conflicts.append((r1, r2))

    # ── Report ───────────────────────────────────────────────────────
    click.echo("── Rules with signal evidence ──")
    if with_evidence:
        for r in with_evidence:
            tools_str = ", ".join(sorted(r["matched_tools"]))
            click.echo(f"  ✓ {r['title']}  ({tools_str})")
    else:
        click.echo("  (none)")

    click.echo("\n── Rules without signal evidence (pruning candidates) ──")
    if without_evidence:
        for r in without_evidence:
            click.echo(f"  ? {r['title']}")
    else:
        click.echo("  (none)")

    click.echo(f"\n── Potential conflicts ({len(conflicts)} pair(s)) ──")
    if conflicts:
        for r1, r2 in conflicts:
            overlap = r1["matched_tools"] & r2["matched_tools"]
            click.echo(
                f"  ! {r1['title']} <-> {r2['title']}  (shared: {', '.join(sorted(overlap))})"
            )
    else:
        click.echo("  (none)")

    click.echo(
        f"\nSummary: {len(with_evidence)} evidenced, "
        f"{len(without_evidence)} without evidence, "
        f"{len(conflicts)} potential conflict(s)."
    )


# ── type → migration target map ────────────────────────────────────

CONSOLIDATION_PATHWAYS: dict[str, tuple[str, str]] = {
    "feedback": ("Constitution", "Behavioral rules that govern every session"),
    "finding": (
        "Program (hook/guard/linter)",
        "Technical gotchas should be enforced, not remembered",
    ),
    "user": (
        "Constitution user section or relevant skill",
        "Preferences that matter every session",
    ),
    "project": ("Vault note (~/epigenome/chromatin/)", "Project state belongs in source of truth"),
    "reference": ("tool-index.md or skill file", "Pointers belong where the action is"),
}


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter from a markdown file.

    Simple key: value parser — no pyyaml dependency.
    """
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def _keyword_overlap(text_a: str, text_b: str, min_word_len: int = 4) -> set[str]:
    """Return significant words shared between two texts."""
    import re

    def _words(text: str) -> set[str]:
        return {
            w.lower()
            for w in re.findall(r"[a-z][a-z0-9_]+", text.lower())
            if len(w) >= min_word_len
        }

    return _words(text_a) & _words(text_b)


# ── pulse (top-level) ────────────────────────────────────────────


@cli.command()
@click.option(
    "--waves",
    type=int,
    default=None,
    help="Max waves (default: auto based on time of day).",
)
@click.option("--model", default="opus", help="Model (default: opus).")
@click.option("--retry", type=int, default=1, help="Retries per failed wave (default: 1).")
@click.option(
    "--focus",
    type=str,
    default=None,
    help="Restrict to specific north stars (e.g. 'career,financial').",
)
@click.option(
    "--stop-after",
    type=str,
    default=None,
    help="Stop dispatching after HH:MM (e.g. '07:00').",
)
@click.option("--overnight", is_flag=True, help="Force overnight mode (3 waves, 07:00 deadline).")
@click.option("--max-waves", type=int, default=None, help="Alias for --waves.")
@click.option("--dry-run", is_flag=True, help="Show plan without executing.")
def pulse(waves, model, retry, focus, stop_after, overnight, max_waves, dry_run):
    """The organism's heartbeat — wave executor."""
    from metabolon.pulse import main as pulse_main

    # --max-waves is an alias for --waves
    effective_waves = waves or max_waves

    # --overnight forces overnight defaults
    if overnight:
        if effective_waves is None:
            effective_waves = 3
        if stop_after is None:
            stop_after = "07:00"

    pulse_main(
        waves=effective_waves,
        model=model,
        retry=retry,
        focus=focus,
        stop_after=stop_after,
        dry_run=dry_run,
    )


@metabolism.command("dissolve")
@click.option(
    "--memory-dir",
    type=click.Path(exists=False),
    default=None,
    help="Crystal directory (default: ~/.claude/projects/-Users-terry/memory/).",
)
@click.option("--days", default=30, help="Stimulus window in days.")
def metabolism_dissolve(memory_dir: str | None, days: int):
    """Apoptosis — classify crystals and propose migration targets."""
    from datetime import datetime, timedelta

    from metabolon.metabolism.signals import SensorySystem

    # ── Resolve memory directory ────────────────────────────────────
    if memory_dir:
        mem_path = Path(memory_dir)
    else:
        mem_path = Path.home() / ".claude" / "projects" / "-Users-terry" / "memory"

    if not mem_path.exists():
        click.echo(f"Memory directory not found: {mem_path}")
        return

    md_files = sorted(p for p in mem_path.glob("*.md") if p.name != "MEMORY.md")
    if not md_files:
        click.echo(f"No memory files found in {mem_path}")
        return

    # ── Parse all memories ──────────────────────────────────────────
    memories: list[dict] = []
    for fp in md_files:
        text = fp.read_text()
        meta = _parse_frontmatter(text)
        mem_type = meta.get("type", "unknown")
        memories.append(
            {
                "path": fp,
                "name": meta.get("name", fp.stem),
                "description": meta.get("description", ""),
                "type": mem_type,
                "text": text,
                "target": CONSOLIDATION_PATHWAYS.get(
                    mem_type, ("Unknown", "No migration rule for this type")
                ),
            }
        )

    # ── Read constitution for overlap detection ─────────────────────
    constitution_path = Path.home() / ".local" / "share" / "vivesca" / "genome.md"
    constitution = constitution_path.read_text() if constitution_path.exists() else ""

    # ── Read signals for cross-reference ────────────────────────────
    collector = SensorySystem()
    since = datetime.now(UTC) - timedelta(days=days)
    signals = collector.recall_since(since)

    signal_tools: set[str] = set()
    for s in signals:
        signal_tools.add(s.tool.lower())
        if "_" in s.tool:
            signal_tools.add(s.tool.split("_")[0].lower())

    # ── Classify and annotate ───────────────────────────────────────
    type_counts: dict[str, int] = {}
    promotion_candidates: list[dict] = []
    program_candidates: list[dict] = []
    migration_candidates: list[dict] = []
    dead_candidates: list[dict] = []
    already_promoted: list[dict] = []

    for mem in memories:
        mt = mem["type"]
        type_counts[mt] = type_counts.get(mt, 0) + 1

        # Check constitution overlap
        overlap = _keyword_overlap(mem["text"], constitution)
        mem["constitution_overlap"] = overlap

        # Check signal overlap
        mem_words = {w.lower() for w in mem["text"].split() if len(w) >= 3}
        signal_match = bool(mem_words & signal_tools)
        mem["signal_match"] = signal_match

        if mt == "feedback":
            if len(overlap) >= 5:
                already_promoted.append(mem)
            elif signal_match:
                mem["priority"] = "high (signal evidence)"
                promotion_candidates.append(mem)
            else:
                promotion_candidates.append(mem)

        elif mt == "finding":
            if signal_match:
                mem["priority"] = "high (signal evidence)"
            program_candidates.append(mem)

        elif mt in ("project", "reference"):
            migration_candidates.append(mem)

        elif mt == "user":
            if len(overlap) >= 5:
                already_promoted.append(mem)
            else:
                promotion_candidates.append(mem)

    # Detect dead memories — no constitution overlap AND no signal match
    for mem in memories:
        if (
            not mem["constitution_overlap"]
            and not mem["signal_match"]
            and mem not in already_promoted
        ):
            dead_candidates.append(mem)

    # ── Report ──────────────────────────────────────────────────────
    click.echo(f"Memory files: {len(memories)} (from {mem_path})")
    click.echo(f"Signals (last {days} days): {len(signals)}\n")

    # By type
    click.echo("── Memories by type ──")
    for t in sorted(type_counts):
        target_name, rationale = CONSOLIDATION_PATHWAYS.get(t, ("Unknown", ""))
        click.echo(f"  {t}: {type_counts[t]}  → {target_name}")

    # Promotion candidates
    click.echo(f"\n── Promotion candidates ({len(promotion_candidates)}) ──")
    if promotion_candidates:
        for mem in promotion_candidates:
            priority = mem.get("priority", "")
            pstr = f"  [{priority}]" if priority else ""
            click.echo(f"  → {mem['name']}{pstr}")
    else:
        click.echo("  (none)")

    # Already promoted
    click.echo(f"\n── Already promoted ({len(already_promoted)}) ──")
    if already_promoted:
        for mem in already_promoted:
            click.echo(
                f"  ✓ {mem['name']}  (overlap: {len(mem['constitution_overlap'])} keywords)"
            )
    else:
        click.echo("  (none)")

    # Program candidates
    click.echo(f"\n── Program candidates ({len(program_candidates)}) ──")
    if program_candidates:
        for mem in program_candidates:
            priority = mem.get("priority", "")
            pstr = f"  [{priority}]" if priority else ""
            click.echo(f"  → {mem['name']}{pstr}")
    else:
        click.echo("  (none)")

    # Migration candidates
    click.echo(f"\n── Migration candidates ({len(migration_candidates)}) ──")
    if migration_candidates:
        for mem in migration_candidates:
            target_name, rationale = mem["target"]
            click.echo(f"  → {mem['name']}  → {target_name} ({rationale})")
    else:
        click.echo("  (none)")

    # Dead candidates
    click.echo(f"\n── Dead candidates ({len(dead_candidates)}) ──")
    if dead_candidates:
        for mem in dead_candidates:
            click.echo(f"  ✗ {mem['name']}  (no signal or constitution evidence)")
    else:
        click.echo("  (none)")

    click.echo(
        f"\nSummary: {len(promotion_candidates)} to promote, "
        f"{len(already_promoted)} already promoted, "
        f"{len(program_candidates)} to program, "
        f"{len(migration_candidates)} to migrate, "
        f"{len(dead_candidates)} dead."
    )


# ── endocytosis (receptor-mediated RSS endocytosis) ──────────────────


@cli.group()
def endocytosis():
    """Receptor-mediated endocytosis — RSS/web/X feed ingestion."""
    pass


@endocytosis.command("fetch")
@click.option("--no-archive", is_flag=True, help="Skip full-text archiving (tier-1 only).")
def endocytosis_fetch(no_archive: bool):
    """Internalise new ligands from all active receptors (RSS/web/X).

    Runs a full fetch cycle: scan all sources, score relevance, route through
    endosomal sorting, and append surviving articles to the news log.
    Long-running (60-300s depending on source count).
    """
    from metabolon.organelles.endocytosis_rss.config import restore_config
    from metabolon.organelles.endocytosis_rss.state import lockfile

    cfg = restore_config()
    with lockfile(cfg.state_path):
        from metabolon.organelles.endocytosis_rss.cli import _fetch_locked

        _fetch_locked(cfg, no_archive)


@endocytosis.command("digest")
@click.option("--month", default=None, help="Target month YYYY-MM.")
@click.option("--dry-run", is_flag=True, help="Show themes only, no output file.")
@click.option("--themes", type=int, default=None, help="Max themes.")
@click.option("--model", default=None, help="Model ID.")
@click.option("--tag", "-t", multiple=True, help="Filter by tag (repeatable).")
@click.option("--weekly", is_flag=True, help="Secrete weekly digest (past 7 days, no LLM).")
def endocytosis_digest(month, dry_run, themes, model, tag, weekly):
    """Synthesise a thematic digest from the news log.

    Default: monthly LLM-powered theme identification.
    --weekly: score-based weekly secretion (no LLM, fast).
    """
    import json

    from metabolon.organelles.endocytosis_rss.config import restore_config
    from metabolon.organelles.endocytosis_rss.digest import metabolize_digest, metabolize_weekly

    cfg = restore_config()

    if weekly:
        try:
            item_count, output_path = metabolize_weekly(cfg=cfg, tags=list(tag))
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            raise SystemExit(1)
        click.echo(f"Weekly digest: {item_count} items above threshold.", err=True)
        if output_path is not None:
            click.echo(f"Written: {output_path}", err=True)
        return

    try:
        themes_result, output_path = metabolize_digest(
            cfg=cfg,
            month=month,
            dry_run=dry_run,
            themes=themes,
            model=model,
            tags=list(tag),
        )
    except RuntimeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"Found {len(themes_result)} themes.", err=True)
    for i, theme in enumerate(themes_result, 1):
        tname = theme.get("theme", f"Theme {i}")
        count = len(theme.get("article_indices", []))
        click.echo(f"{i}. {tname} ({count} articles)", err=True)

    if dry_run:
        click.echo(json.dumps(themes_result, indent=2, ensure_ascii=False))
        return

    if output_path is not None:
        click.echo(f"Digest written: {output_path}", err=True)


@endocytosis.command("breaking")
@click.option("--dry-run", is_flag=True, help="Detect signals but do not notify.")
def endocytosis_breaking(dry_run: bool):
    """Scan recent news for breaking signals and notify if found."""
    from metabolon.organelles.endocytosis_rss.breaking import scan_breaking
    from metabolon.organelles.endocytosis_rss.config import restore_config

    cfg = restore_config()
    result = scan_breaking(cfg=cfg, dry_run=dry_run)
    raise SystemExit(result)


@endocytosis.command("status")
def endocytosis_status():
    """Show receptor status: last fetch times, source count, cache size."""
    from datetime import datetime, timedelta, timezone

    from metabolon.organelles.endocytosis_rss.config import restore_config
    from metabolon.organelles.endocytosis_rss.state import restore_state

    def _file_age(path: Path, now: datetime) -> str:
        if not path.exists():
            return "missing"
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
        delta = now - modified
        if delta.total_seconds() < 60:
            return "just now"
        if delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() // 60)}m ago"
        if delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() // 3600)}h ago"
        return f"{delta.days}d ago"

    def _parse_aware(value: str) -> datetime | None:
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    cfg = restore_config()
    now = datetime.now().astimezone()
    click.echo(f"Endocytosis Status  ({now.strftime('%Y-%m-%d %H:%M %Z')})")
    click.echo("=" * 44)
    click.echo(f"\nConfig dir:    {cfg.config_dir}")
    click.echo(f"Sources file:  {_file_age(cfg.sources_path, now)}")
    click.echo(f"State file:    {_file_age(cfg.state_path, now)}")
    click.echo(f"News log:      {_file_age(cfg.log_path, now)}")

    state = restore_state(cfg.state_path)
    if state:
        click.echo(f"Sources:       {len(state)} tracked")
        latest = max(
            (dt for ts in state.values() if isinstance(ts, str) for dt in [_parse_aware(ts)] if dt),
            default=None,
        )
        if latest is not None:
            click.echo(f"Last fetch:    {latest.strftime('%Y-%m-%d %H:%M')}")

    if cfg.article_cache_dir.exists():
        files = list(cfg.article_cache_dir.glob("*.json"))
        size_kb = sum(f.stat().st_size for f in files) / 1024
        click.echo(f"Article cache: {len(files)} files, {size_kb:.0f} KB")
    else:
        click.echo(f"Article cache: missing ({cfg.article_cache_dir})")


@endocytosis.command("sources")
@click.option("--tier", type=int, default=None, help="Filter sources by tier.")
def endocytosis_sources(tier: int | None):
    """List configured receptor sources."""
    from metabolon.organelles.endocytosis_rss.config import restore_config

    cfg = restore_config()
    rows: list[tuple[str, str, int, str]] = []

    for source in cfg.sources_data.get("web_sources", []):
        if not isinstance(source, dict):
            continue
        source_tier = int(source.get("tier", 2))
        if tier is not None and source_tier != tier:
            continue
        source_type = "rss" if source.get("rss") else "web"
        rows.append((str(source.get("name", "")), source_type, source_tier, str(source.get("cadence", "-"))))

    for account in cfg.sources_data.get("x_accounts", []):
        if not isinstance(account, dict):
            continue
        account_tier = int(account.get("tier", 2))
        if tier is not None and account_tier != tier:
            continue
        rows.append((str(account.get("name") or account.get("handle", "")), "x", account_tier, str(account.get("cadence", "-"))))

    for bm in cfg.sources_data.get("x_bookmarks", []):
        if not isinstance(bm, dict):
            continue
        bm_tier = int(bm.get("tier", 2))
        if tier is not None and bm_tier != tier:
            continue
        rows.append((str(bm.get("name", "X Bookmarks")), "bkmk", bm_tier, str(bm.get("cadence", "-"))))

    if not rows:
        click.echo("No sources configured.")
        return

    click.echo(f"{'Name':<36} {'Type':<4} {'Tier':>4} {'Cadence':<12}")
    click.echo("-" * 64)
    for name, source_type, source_tier, cadence in rows:
        click.echo(f"{name[:36]:<36} {source_type:<4} {source_tier:>4} {cadence:<12}")
    click.echo(f"\nTotal: {len(rows)} sources")


@endocytosis.command("relevance")
@click.option("--top", type=int, default=None, help="Show top N highest-scored items (last 7 days).")
def endocytosis_relevance(top: int | None):
    """Show relevance scoring stats or top-scored items."""
    from metabolon.organelles.endocytosis_rss.relevance import (
        affinity_stats,
        top_cargo,
    )

    if top is not None:
        items = top_cargo(limit=top)
        if not items:
            click.echo("No recent relevance data found.")
            return
        for index, item in enumerate(items, 1):
            title = item.get("title", "Untitled")
            source = item.get("source", "Unknown")
            score = item.get("score", 0)
            angle = item.get("banking_angle", "")
            line = f"{index}. [{score}/10] {title} -- {source}"
            if angle and angle != "N/A":
                line = f"{line} ({angle})"
            click.echo(line)
        return

    stats = affinity_stats()
    if stats.get("status") == "insufficient_data":
        click.echo("Relevance stats unavailable: insufficient_data")
        return

    click.echo("Relevance scoring stats")
    click.echo(f"Total scored: {stats['total_scored']}")
    click.echo(f"Total engaged: {stats['total_engaged']}")
    click.echo(f"Average engaged score: {stats['avg_engaged_score']:.2f}")
    click.echo(f"False positives (count): {stats['false_positives_count']}")
    click.echo("False negatives:")
    for title in stats["false_negatives"]:
        click.echo(f"- {title}")


@endocytosis.command("discover")
@click.option("--count", type=int, default=None, help="Number of tweets to scan.")
def endocytosis_discover(count: int | None):
    """Discover new receptor candidates from X/Twitter timeline."""
    from metabolon.organelles.endocytosis_rss.config import restore_config
    from metabolon.organelles.endocytosis_rss.discover import scout_sources

    cfg = restore_config()
    result = scout_sources(cfg=cfg, count=count, bird_path=cfg.resolve_bird())
    raise SystemExit(result)


@cli.command("auscultate")
def auscultate():
    """Listen to the organism's internals — smoke test everything."""
    import importlib
    import subprocess
    import sys

    from metabolon.cytosol import VIVESCA_ROOT

    checks = []

    # 1. MCP server imports
    try:
        from metabolon.membrane import main  # noqa: F401
        checks.append(("MCP server import", True, ""))
    except Exception as e:
        checks.append(("MCP server import", False, str(e)))

    # 2. Key module imports
    for mod in [
        "metabolon.symbiont",
        "metabolon.pinocytosis",
        "metabolon.pinocytosis.interphase",
        "metabolon.respiration",
        "metabolon.respirometry",
    ]:
        try:
            importlib.import_module(mod)
            checks.append((f"import {mod.split('.')[-1]}", True, ""))
        except Exception as e:
            checks.append((f"import {mod.split('.')[-1]}", False, str(e)))

    # 3. VIVESCA_ROOT resolves correctly
    expected = str(VIVESCA_ROOT)
    if expected.endswith("germline"):
        checks.append(("VIVESCA_ROOT", True, expected))
    else:
        checks.append(("VIVESCA_ROOT", False, f"expected */germline, got {expected}"))

    # 4. Key paths exist
    from pathlib import Path
    paths = {
        "genome.md": VIVESCA_ROOT / "genome.md",
        "anatomy.md": VIVESCA_ROOT / "anatomy.md",
        "membrane/cytoskeleton": VIVESCA_ROOT / "membrane" / "cytoskeleton",
        "membrane/receptors": VIVESCA_ROOT / "membrane" / "receptors",
        "effectors": VIVESCA_ROOT / "effectors",
        "chromatin": __import__("metabolon.locus", fromlist=["chromatin"]).chromatin,
        "engrams": __import__("metabolon.locus", fromlist=["engrams"]).engrams,
    }
    for name, path in paths.items():
        checks.append((f"path {name}", path.exists(), str(path)))

    # 5. Hooks symlink resolves
    hooks = Path.home() / ".claude" / "hooks"
    if hooks.is_symlink() and hooks.resolve().exists():
        checks.append(("hooks symlink", True, str(hooks.resolve())))
    else:
        checks.append(("hooks symlink", False, "broken or missing"))

    # 6. CC config symlinks
    for name in ["settings.json", "CLAUDE.md"]:
        p = Path.home() / ".claude" / name
        if p.is_symlink() and p.resolve().exists():
            checks.append((f"CC {name}", True, ""))
        else:
            checks.append((f"CC {name}", False, "broken symlink"))

    # 7. Pyright undefined count
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pyright", str(VIVESCA_ROOT / "metabolon"), "--outputjson"],
            capture_output=True, text=True, timeout=60,
        )
        import json
        data = json.loads(r.stdout)
        undefs = [d for d in data.get("generalDiagnostics", []) if d.get("rule") == "reportUndefinedVariable"]
        checks.append(("pyright undefined", len(undefs) == 0, f"{len(undefs)} undefined"))
    except Exception as e:
        checks.append(("pyright undefined", None, f"skipped: {e}"))

    # 8. Tests
    try:
        r = subprocess.run(
            ["uv", "run", "pytest", str(VIVESCA_ROOT / "assays"), "-q", "--ignore", str(VIVESCA_ROOT / "assays" / "test_cli.py")],
            capture_output=True, text=True, timeout=120, cwd=str(VIVESCA_ROOT),
        )
        last_line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        passed = "passed" in last_line and "failed" not in last_line
        checks.append(("pytest", passed, last_line))
    except Exception as e:
        checks.append(("pytest", None, f"skipped: {e}"))

    # Report
    click.echo("\n  AUSCULTATION — Organism Vital Signs\n")
    all_ok = True
    for name, ok, detail in checks:
        if ok is True:
            symbol = click.style("OK", fg="green")
        elif ok is False:
            symbol = click.style("FAIL", fg="red")
            all_ok = False
        else:
            symbol = click.style("SKIP", fg="yellow")
        line = f"  {symbol}  {name}"
        if detail and ok is not True:
            line += f"  ({detail})"
        click.echo(line)

    click.echo("")
    if all_ok:
        click.echo(click.style("  Organism is healthy.", fg="green", bold=True))
    else:
        click.echo(click.style("  Organism needs attention.", fg="red", bold=True))
    click.echo("")
