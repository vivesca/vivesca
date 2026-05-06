#!/usr/bin/env python3
"""synapse.py — consolidated UserPromptSubmit hook.

Replaces 11 separate hooks (9 Python + 2 Node.js) with a single process.
Saves ~500ms per prompt by eliminating process startup overhead.

Each module runs in try/except for fault isolation.
"""

from __future__ import annotations

import configparser
import contextlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
HOOKS_DIR = HOME / ".claude" / "hooks"
CHROMATIN_DIR = HOME / "epigenome" / "chromatin"
EPIGENOME_DIR = HOME / "epigenome"
TMP_DIR = Path(tempfile.gettempdir())
HKT = timezone(timedelta(hours=8))

# Repo root: hooks → claude → vivesca
_VIVESCA_ROOT = Path(__file__).resolve().parent.parent.parent

# ── conf: signal transduction thresholds ──────────────
_SYNAPSE_CONF = configparser.ConfigParser()
_SYNAPSE_CONF.read(_VIVESCA_ROOT / "germline" / "synapse.conf")


def _sconf_float(section, key, default):
    try:
        return float(_SYNAPSE_CONF[section][key])
    except (KeyError, ValueError):
        return default


def _sconf_int(section, key, default):
    try:
        return int(_SYNAPSE_CONF[section][key])
    except (KeyError, ValueError):
        return default


sys.path.insert(0, str(HOOKS_DIR))

# Lazy hebbian_nudge
_hebbian = None
_hebbian_loaded = False


def get_hebbian():
    global _hebbian, _hebbian_loaded
    if not _hebbian_loaded:
        _hebbian_loaded = True
        try:
            import hebbian_nudge

            _hebbian = hebbian_nudge
        except ImportError:
            pass
    return _hebbian


# ── anamnesis: session-start context loading ───────────────

ANAM_NOW = CHROMATIN_DIR / "Tonus.md"


def _inject_recent_git_log() -> str:
    """Cross-reference block: last 48h of commits in load-bearing repos.

    Sits adjacent to Tonus injection so stale carry-forward claims are
    visible against fresh commits in the same context window. Per
    finding_carry_forward_decay_without_verification.md (Option A).

    Uses Path.home() (not module-level HOME) so assays can monkeypatch.
    Hardcoded to germline + epigenome; resist the urge to auto-detect.
    """
    repos = [
        ("germline", Path.home() / "germline"),
        ("epigenome", Path.home() / "epigenome"),
    ]
    sections = []
    for label, path in repos:
        if not (path / ".git").exists():
            continue
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(path),
                    "log",
                    "--since=48 hours ago",
                    "--oneline",
                    "--no-decorate",
                    "-30",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        if result.returncode == 0 and result.stdout.strip():
            sections.append(f"### Recent {label} commits (last 48h)\n{result.stdout.strip()}")
    if not sections:
        return ""
    return (
        "\n\n## Recent git activity (cross-reference against Tonus carry-forward)\n\n"
        + "\n\n".join(sections)
    )


def mod_anamnesis(data):
    """Session-start context: Tonus + epigenome git pull. Lean.

    Domain context (anatomy, effectors, circadian, vitals, budget) removed —
    already available on-demand via MCP tools (circadian, interoception,
    ergometer) or file reads. genome.md removed — duplicate of CLAUDE.md.
    """
    session_id = data.get("session_id", "")
    if not session_id:
        return []
    marker = TMP_DIR / f"chromatin-pull-{session_id}.done"
    if marker.exists():
        return []

    try:
        subprocess.run(
            ["git", "-C", str(EPIGENOME_DIR), "pull", "--no-rebase", "-X", "ours", "-q"],
            capture_output=True,
            timeout=15,
        )
        marker.touch()
    except Exception:
        pass

    lines = []
    now = datetime.now(HKT)
    lines.append(f"Current date/time: {now.strftime('%A, %d %B %Y, %H:%M HKT')}")

    try:
        c = ANAM_NOW.read_text(encoding="utf-8").strip()
        if c:
            lines.append(f"\nTonus.md (active session state):\n{c}")
            # Staleness check: warn if tonus checkpoint is old
            checkpoint_match = re.search(
                r"last checkpoint:\s*(\d{1,2}/\d{1,2}/\d{4})\s*~?\s*(\d{1,2}:\d{2})",
                c,
            )
            if checkpoint_match:
                try:
                    checkpoint_str = f"{checkpoint_match.group(1)} {checkpoint_match.group(2)}"
                    checkpoint_time = datetime.strptime(checkpoint_str, "%d/%m/%Y %H:%M")
                    checkpoint_time = checkpoint_time.replace(tzinfo=HKT)
                    hours_stale = (now - checkpoint_time).total_seconds() / 3600
                    if hours_stale > 4:
                        lines.append(
                            f"Tonus is {int(hours_stale)}h stale (last checkpoint: {checkpoint_match.group(0)}). "
                            "Ask user for updates before giving prioritisation advice — "
                            "calls, schedule changes, and decisions may have happened since."
                        )
                except (ValueError, OverflowError):
                    pass
    except Exception:
        pass

    # Recent git activity — surfaces fresh commits next to Tonus so stale
    # carry-forward claims are visible against ground truth in the same
    # context window. Per finding_carry_forward_decay_without_verification.md.
    try:
        git_log_block = _inject_recent_git_log()
        if git_log_block:
            lines.append(git_log_block)
    except Exception:
        pass

    # Session trace — what earlier sessions did today
    trace_file = CHROMATIN_DIR / "immunity" / "session-trace.md"
    try:
        if trace_file.exists():
            trace_content = trace_file.read_text(encoding="utf-8")
            today_key = now.strftime("%Y-%m-%d")
            if f"## {today_key}" in trace_content:
                start = trace_content.index(f"## {today_key}")
                section = trace_content[start:]
                next_section = section.find("\n## ", 1)
                if next_section != -1:
                    section = section[:next_section]
                entries = [
                    line.strip()
                    for line in section.splitlines()[1:]
                    if line.strip().startswith("- ")
                ]
                if entries:
                    lines.append(f"\nEarlier today ({len(entries)} events):")
                    for entry in entries[-10:]:
                        lines.append(f"  {entry}")
    except Exception:
        pass

    # Recent interactions — meetings + emails from last 5 days
    meetings_dir = CHROMATIN_DIR / "meetings"
    try:
        if meetings_dir.exists():
            cutoff = (now - timedelta(days=5)).timestamp()
            recent_notes = sorted(
                (f for f in meetings_dir.glob("*.md") if f.stat().st_mtime > cutoff),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if recent_notes:
                interaction_lines = []
                for note in recent_notes[:5]:
                    content = note.read_text(encoding="utf-8")
                    # Extract next: items from frontmatter
                    nexts = []
                    if content.startswith("---"):
                        end = content.find("---", 3)
                        if end != -1:
                            fm = content[3:end]
                            in_next = False
                            for fm_line in fm.splitlines():
                                if fm_line.strip().startswith("next:"):
                                    in_next = True
                                    continue
                                if in_next:
                                    if fm_line.strip().startswith("- "):
                                        nexts.append(fm_line.strip()[2:].strip()[:100])
                                    elif fm_line.strip() and not fm_line.startswith(" "):
                                        break
                    # Extract type
                    note_type = "interaction"
                    if content.startswith("---"):
                        end = content.find("---", 3)
                        if end != -1:
                            fm = content[3:end]
                            for fm_line in fm.splitlines():
                                if fm_line.strip().startswith("type:"):
                                    note_type = fm_line.split(":", 1)[1].strip()
                    stem = note.stem
                    summary = f"  - [{note_type}] {stem}"
                    if nexts:
                        summary += f" | next: {'; '.join(nexts[:3])}"
                    interaction_lines.append(summary)
                if interaction_lines:
                    lines.append(f"\nRecent interactions ({len(interaction_lines)}):")
                    lines.extend(interaction_lines)
    except Exception:
        pass

    try:
        dirty_counts = {}
        for label, repo in (("germline", HOME / "germline"), ("epigenome", EPIGENOME_DIR)):
            result = subprocess.run(
                ["git", "-C", str(repo), "status", "--short"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            dirty_counts[label] = sum(1 for line in result.stdout.splitlines() if line.strip())
        if dirty_counts["germline"] or dirty_counts["epigenome"]:
            lines.append(
                "Previous session left "
                f"{dirty_counts['germline']} dirty files in germline, "
                f"{dirty_counts['epigenome']} in epigenome. "
                "Commit or review before new work."
            )
    except Exception:
        pass

    # 24h retrospective-pattern frequency: when >=10 retrospectives filed in
    # past 24h, surface count + dominant named pattern as a hard pause.
    # Path-only mark/skill routing has not deterred recurrence (19+ instances
    # of assert-before-verifying on 2026-04-28 alone). Codifies retrospective
    # 2026-04-28-2300 §2d [Both] item 3 — load-bearing hook edit, Terry's
    # eyes per genome AUTONOMY rule.
    try:
        grades_file = CHROMATIN_DIR / "retrospectives" / "_grades.md"
        if grades_file.exists():
            text = grades_file.read_text(encoding="utf-8", errors="replace")
            cutoff = now - timedelta(hours=24)
            recent_grade_lines = []
            for grade_line in text.splitlines():
                m = re.match(r"^- (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) — ", grade_line)
                if not m:
                    continue
                try:
                    line_dt = datetime.strptime(
                        f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=HKT)
                except ValueError:
                    continue
                if line_dt >= cutoff:
                    recent_grade_lines.append(grade_line)
            if len(recent_grade_lines) >= 10:
                pattern_counts: dict[str, int] = {}
                for grade_line in recent_grade_lines:
                    for keyword in (
                        "assert-before-verifying",
                        "verify-before",
                        "self-context blindness",
                        "premature dismissal",
                        "premise miss",
                    ):
                        if keyword in grade_line.lower():
                            pattern_counts[keyword] = pattern_counts.get(keyword, 0) + 1
                if pattern_counts:
                    top_pattern, top_count = max(pattern_counts.items(), key=lambda kv: kv[1])
                    if top_count >= 5:
                        lines.append(
                            f"\n**24h pattern frequency:** {len(recent_grade_lines)} retrospectives filed in past 24h, "
                            f"{top_count} flag '{top_pattern}'. "
                            "BEFORE asserting any factual / institutional / authority / tool-existence claim, "
                            "fetch the primary source (URL / file / artefact) and grep for the cited element. "
                            "Marks/skills layer at this pattern have not deterred recurrence — the gate is on you, this turn."
                        )
    except Exception:
        pass

    return lines


# ── allostasis: budget/phase/depth regulation ──────────────

ALLOW_STATE = HOME / ".local/share/respirometry/budget-tier.json"
ALLOW_GUIDANCE = {
    "anabolic": "Stay concise. Budget headroom is not a license for verbose answers — lead with the answer, one section, no anticipatory caveats.",
    "homeostatic": "Delegate implementation to ribosome (`mtor` CLI or Sonnet subagent). CC designs and reviews only.",
    "catabolic": "STOP CODING. CC is architect only — spec tasks for Goose, review results. No direct implementation. Minimize tool calls — verify critical facts only.",
    "autophagic": "WRAP UP. Deliver what you have now. /sporulation immediately. No new work — checkpoint and stop.",
}
# Map respirometry budget tiers to metabolic states
_BUDGET_TO_STATE = {"green": "anabolic", "yellow": "homeostatic", "red": "catabolic"}
ALLOW_CIRCADIAN = {
    "night": "",
    "evening": "",
    "morning": "",
    "day": "",
}

# ── burn mode: use-it-or-lose-it budget override ─────────
BURN_FLAG = HOME / ".claude" / "burn-mode"
BURN_HOURS = _sconf_float("burn", "hours_threshold", 6.0)
BURN_UTIL = _sconf_float("burn", "util_threshold", 70.0)


def _allow_respirometry():
    """Fetch respirometry JSON once, return (budget_tier, util, hours_left).

    Single subprocess call replaces the previous two (--json + --budget).
    """
    try:
        r = subprocess.run(["respirometry", "--json"], capture_output=True, text=True, timeout=5)
        d = json.loads(r.stdout)
        w = d.get("seven_day", {})
        util = w.get("utilization", 0)
        resets_at = w.get("resets_at", "")
        if resets_at:
            reset_time = datetime.fromisoformat(resets_at)
            hours_left = max(0, (reset_time - datetime.now(UTC)).total_seconds() / 3600)
        else:
            hours_left = -1
        # Derive budget tier from utilization (matches respirometry --budget logic)
        if util >= 90:
            budget = "red"
        elif util >= 70:
            budget = "yellow"
        else:
            budget = "green"
        return budget, util, hours_left
    except Exception:
        return "unknown", 0, -1


def _burn_mode(util, hours_left):
    """Check if burn mode is active. Returns (reason, hours_left, util) or None."""
    # Manual: flag file with expiry timestamp
    if BURN_FLAG.exists():
        try:
            content = BURN_FLAG.read_text().strip()
            if content:
                expires = datetime.fromisoformat(content)
                if datetime.now(UTC) > expires:
                    BURN_FLAG.unlink(missing_ok=True)
                else:
                    return "manual", hours_left, util
            else:
                return "manual", hours_left, util
        except (ValueError, OSError):
            return "manual", hours_left, util

    # Auto: high utilization + imminent reset
    if util >= BURN_UTIL and 0 < hours_left < BURN_HOURS:
        return "auto", hours_left, util

    return None


def _allow_phase():
    h = datetime.now(HKT).hour
    if 6 <= h < 10:
        return "morning"
    elif 10 <= h < 17:
        return "day"
    elif 17 <= h < 21:
        return "evening"
    return "night"


def _allow_effective(budget, phase, depth):
    states = ["anabolic", "homeostatic", "catabolic", "autophagic"]
    metabolic = _BUDGET_TO_STATE.get(budget)
    if metabolic is None:
        return _BUDGET_TO_STATE.get("yellow", "homeostatic")
    idx = states.index(metabolic)
    # Night penalty disabled — user prefers uninterrupted late sessions
    if phase == "morning":
        idx -= 1
    if depth > 50:
        idx += 1
    return states[max(0, min(idx, len(states) - 1))]


def mod_allostasis(data):
    session_id = data.get("session_id", "")
    state = {}
    with contextlib.suppress(Exception):
        state = json.loads(ALLOW_STATE.read_text())

    prev_tier = state.get("tier", "")
    prev_session = state.get("session_id", "")
    depth = 1 if session_id != prev_session else state.get("depth", 0) + 1

    # Single respirometry call for both burn-mode and normal budget logic
    budget, util, hours_left = _allow_respirometry()
    phase = _allow_phase()

    # Check burn mode before normal budget logic
    burn = _burn_mode(util, hours_left)
    if burn:
        reason, hours_left, util = burn
        tier = "anabolic"

        ALLOW_STATE.parent.mkdir(parents=True, exist_ok=True)
        ALLOW_STATE.write_text(
            json.dumps(
                {
                    "tier": tier,
                    "budget": budget,
                    "phase": phase,
                    "depth": depth,
                    "session_id": session_id,
                    "burn_mode": reason,
                }
            )
        )

        if hours_left >= 0:
            h = int(hours_left)
            m = int((hours_left - h) * 60)
            msg = f"BURN MODE ({reason}) -- {h}h{m:02d}m until reset, {util:.0f}% used. Opus direct, skip delegation. Stay concise — burn mode ≠ verbose."
        else:
            msg = f"BURN MODE ({reason}) -- Opus direct, skip delegation. Stay concise — burn mode ≠ verbose."

        heb = get_hebbian()
        if heb:
            with contextlib.suppress(Exception):
                heb.log_nudge(
                    "allostasis",
                    "burn-mode",
                    metadata={"reason": reason, "hours_left": hours_left, "util": util},
                )
        return [msg]

    tier = _allow_effective(budget, phase, depth)

    ALLOW_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALLOW_STATE.write_text(
        json.dumps(
            {
                "tier": tier,
                "budget": budget,
                "phase": phase,
                "depth": depth,
                "session_id": session_id,
            }
        )
    )

    parts = []
    changed = tier != prev_tier and prev_tier != ""
    if changed:
        reason = [f"budget={budget}, phase={phase}, depth={depth}"]
        parts.append(f"Metabolic state: {prev_tier} -> {tier} ({', '.join(reason)})")
    elif tier in ("catabolic", "autophagic"):
        parts.append(f"Metabolic state: {tier} (budget={budget}, phase={phase}, depth={depth})")

    g = ALLOW_GUIDANCE.get(tier, "")
    if g:
        parts.append(g)
    c = ALLOW_CIRCADIAN.get(phase, "")
    if c and depth <= 2:
        parts.append(c)

    if parts:
        heb = get_hebbian()
        if heb:
            with contextlib.suppress(Exception):
                heb.log_nudge(
                    "allostasis",
                    f"tier:{tier}",
                    metadata={"budget": budget, "phase": phase, "depth": depth},
                )
        return [" — ".join(parts)]
    return []


# ── chemoreceptor: URL/keyword skill routing ───────────────

CHEMO_DOMAINS = {
    "linkedin.com/posts": "LinkedIn post -> use `/produce` skill (stage=forge)",
    "linkedin.com/feed/update": "LinkedIn post -> use `/produce` skill (stage=forge)",
    "linkedin.com/in/terrylihm": "Own LinkedIn profile -> use `linkedin-profile` skill (Featured, About, Headline, announcements)",
    "linkedin.com/in/": "LinkedIn profile -> use `linkedin-research` skill (agent-browser extraction)",
    "linkedin.com/jobs": "LinkedIn job -> use `/ops` skill (domain=jobs)",
    "youtube.com/watch": "YouTube URL -> use `video-digest` skill (transcript + structured digest)",
    "youtu.be/": "YouTube URL -> use `video-digest` skill (transcript + structured digest)",
    "bilibili.com/video": "Bilibili URL -> use `video-digest` skill (transcript + structured digest)",
    "xiaoyuzhou.fm": "Xiaoyuzhou URL -> use `video-digest` skill (podcast transcript + digest)",
    "x.com/": "X/Twitter URL -> use `/absorb` skill (source=web)",
    "twitter.com/": "X/Twitter URL -> use `/absorb` skill (source=web)",
    "e.tb.cn": "Taobao link -> use `agent-browser --profile` (WebFetch blocked, login required)",
    "taobao.com": "Taobao -> use `agent-browser --profile` (WebFetch blocked, login required)",
    "tmall.com": "Tmall -> use `agent-browser --profile` (WebFetch blocked, login required)",
}
CHEMO_KEYWORDS = [
    (r"\blaunch exp\b", "Experiment -> use `/build` skill (phase=experiment)"),
    (r"\brun exp(eriment)?\b", "Experiment -> use `/build` skill (phase=experiment)"),
    (r"\bcompare .{3,40} vs\b", "Comparison -> use `/build` skill (phase=experiment)"),
    (r"\bbenchmark\b", "Benchmark -> use `/build` skill (phase=experiment)"),
    (
        r"\b(worked before|used to work|stopped working|broke[n]?|not found|command not found|regression|troubleshoot)\b",
        "Diagnosis -> use `/diagnose` skill. Frame the problem (regression? new issue?) before attempting fixes",
    ),
    (
        r"\b(dispatch|build it|implement|ribosome|write.{0,10}spec)\b",
        "Dispatch -> use `/mitogen` skill for build/dispatch tasks.",
    ),
]


def mod_chemoreceptor(data):
    prompt = data.get("prompt", "")
    if not prompt:
        return []
    reminders, seen = [], set()
    prompt_lower = prompt.lower()
    for pat, rem in CHEMO_KEYWORDS:
        if re.search(pat, prompt_lower) and rem not in seen:
            reminders.append(rem)
            seen.add(rem)
    for url in re.findall(r'https?://[^\s<>"\']+', prompt):
        for dp, rem in CHEMO_DOMAINS.items():
            if dp in url and rem not in seen:
                reminders.append(rem)
                seen.add(rem)
                break
    if reminders:
        lines = "\n".join(f"- {r}" for r in reminders)
        return [f"Skill routing:\n{lines}\nUse the indicated skill — do not proceed ad-hoc."]
    return []


# ── priming: skill suggestion matching ─────────────────────

PRIM_TRIGGERS = HOME / ".claude" / "skill-triggers.json"
PRIM_LOG = HOME / ".claude" / "skill-suggest-log.tsv"
PRIM_CACHE = HOME / ".claude" / "last-prompt.txt"
PRIM_SLASH_RE = re.compile(r"^/", re.MULTILINE)


def _prim_norm(text):
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


def mod_priming(data):
    prompt = data.get("prompt", "")
    if not prompt or len(prompt) < 4:
        return []
    if PRIM_SLASH_RE.match(prompt.strip()):
        return []
    if not PRIM_TRIGGERS.exists():
        return []
    try:
        triggers = json.loads(PRIM_TRIGGERS.read_text())
    except Exception:
        return []

    on = _prim_norm(prompt)
    matches = []
    for skill, data in triggers.items():
        if isinstance(data, list):
            phrases = data
            anti = []
        else:
            phrases = data.get("triggers", [])
            anti = data.get("anti_triggers", [])

        if any(len(_prim_norm(a)) >= 4 and _prim_norm(a) in on for a in anti):
            continue

        for phrase in phrases:
            phn = _prim_norm(phrase)
            if len(phn) >= 4 and phn in on:
                matches.append((skill, phrase))
                break

    with contextlib.suppress(OSError):
        PRIM_CACHE.write_text(prompt[:500])

    if matches:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        try:
            with PRIM_LOG.open("a") as f:
                for n, p in matches:
                    f.write(f"{ts}\tsuggested\t{n}\t{p}\n")
        except OSError:
            pass
        heb = get_hebbian()
        if heb:
            try:
                for n, _ in matches:
                    heb.log_nudge("priming", f"use-skill:{n}", prompt_snippet=prompt[:200])
            except Exception:
                pass
        sug = ", ".join(f'`/{n}` (matched: "{p}")' for n, p in matches)
        return [f"[skill-suggest] Possible skill match: {sug}. Consider invoking if relevant."]
    return []


# ── mitogen: delegation nudging ────────────────────────────

MIT_VERBS = r"\b(build|implement|create|develop|port|refactor|write|add|make)\b"
MIT_NOUNS = r"\b(cli|tool|script|crate|binary|rust|python|typescript|feature|flag|subcommand|command|endpoint|api|function|struct|module|daemon|launchagent|hook)\b"
MIT_STANDALONE = [
    r"\bnew (cli|crate|binary|project|tool)\b",
    r"\bfix(ing)? (the )?(bug|error|crash|compile|panic|borrow)\b",
    r"\bcargo (build|test|run|check)\b",
    r"\bwrite.{0,15}(in rust|in python|using clap|using ureq)\b",
]
MIT_THRESHOLD = _sconf_int("mitogen", "mit_threshold", 3)


def _mit_is_coding(prompt):
    p = prompt.lower()
    for pat in MIT_STANDALONE:
        if re.search(pat, p):
            return True
    for m in re.finditer(MIT_VERBS, p):
        window = p[max(0, m.start() - 10) : min(len(p), m.end() + 60)]
        if re.search(MIT_NOUNS, window):
            return True
    return False


def mod_mitogen(data):
    prompt = data.get("prompt", "")
    sid = data.get("session_id", "unknown")
    if not prompt:
        return []

    sf = TMP_DIR / f"mitogen-{sid}.json"
    if "/build" in prompt.lower():
        sf.write_text(json.dumps({"fires": 0}))
        return []
    if not _mit_is_coding(prompt):
        return []

    heb = get_hebbian()
    if heb:
        with contextlib.suppress(Exception):
            heb.log_nudge("mitogen", "delegate", prompt_snippet=prompt[:200])

    state = {"fires": 0}
    with contextlib.suppress(Exception):
        state = json.loads(sf.read_text())

    fires = state.get("fires", 0)
    if fires >= MIT_THRESHOLD:
        return []
    fires += 1
    sf.write_text(json.dumps({"fires": fires}))

    if fires == MIT_THRESHOLD:
        return [
            "[mitogen] Coding task detected — /build available. (Suppressing further nudges this session.)"
        ]
    return [
        "[mitogen] Coding task detected — use /build as the on-ramp. Don't implement in-session unless trivial (<50 lines, single file)."
    ]


# ── senescence: wind-down detection ────────────────────────

SEN_PHRASES = [
    "that's all",
    "thats all",
    "that's it",
    "thats it",
    "nothing else",
    "good for now",
    "all done",
    "done for today",
    "done for now",
    "signing off",
    "nothing more",
    "we're done",
    "were done",
    "i'm done",
    "im done",
    "all good",
    "no more",
    "bye",
    "ok bye",
    "thanks bye",
    "any good way to avoid forgetting",
    "anything else i should",
    "anything we missed",
    "did we miss anything",
    "what else should we",
    "are we done",
    "is that everything",
    "that covers it",
    "wrap up",
    "wrap this up",
    "before we finish",
    "before i go",
    "last thing",
    "one last",
]
SEN_CLOSING_RE = re.compile(
    r"^(thanks|thank you|cheers|ok|okay|cool|great|perfect|got it|"
    r"sounds good|looks good|follow your advice|lets do it|makes sense|"
    r"fair enough|noted)[\s.!]*$"
)


def mod_senescence(data):
    prompt = data.get("prompt", "").lower().strip()
    if not prompt or len(prompt) > 80:
        return []
    if not any(p in prompt for p in SEN_PHRASES) and not SEN_CLOSING_RE.match(prompt):
        return []

    h = datetime.now(HKT).hour
    msg = (
        "Session winding down — any loose ends? Consider /daily to log the day."
        if h >= 21 or h < 5
        else "Session winding down — any loose ends? Consider /wrap to capture open threads."
    )
    print(msg, file=sys.stderr)
    return [msg]


# ── circaseptan: weekly note nudge ─────────────────────────

CIRC_WEEKLY = CHROMATIN_DIR / "Weekly"
CIRC_MARKER = HOME / ".claude" / ".weekly-reminded"


def mod_circaseptan(_):
    now = datetime.now()
    if now.weekday() not in (5, 6):
        return []
    week = now.strftime("%G-W%V")
    if CIRC_WEEKLY.exists() and any(week in f.name for f in CIRC_WEEKLY.glob("*.md")):
        return []
    if CIRC_MARKER.exists() and now.timestamp() - CIRC_MARKER.stat().st_mtime < 7200:
        return []
    CIRC_MARKER.touch()
    return [f"Weekly review for {week} not yet done. Run `/rhythm` when ready."]


# ── calorimetry: respirometry autolog ──────────────────────

CAL_STATE = HOME / ".local/share/respirometry/autolog-state.json"
CAL_INTERVAL = _sconf_int("calorimetry", "cal_interval", 1800)


def mod_calorimetry(_):
    now = time.time()
    state = {}
    if CAL_STATE.exists():
        with contextlib.suppress(Exception):
            state = json.loads(CAL_STATE.read_text())

    is_new = not state.get("session_id")
    if not is_new and now - state.get("last_log", 0) < CAL_INTERVAL:
        return []
    if is_new:
        state["session_id"] = str(uuid.uuid4())

    try:
        subprocess.Popen(
            ["respirometry", "log", "--note", "autolog"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return []

    state["last_log"] = now
    CAL_STATE.parent.mkdir(parents=True, exist_ok=True)
    CAL_STATE.write_text(json.dumps(state))
    return []


# ── phenotype: tmux window naming (background) ────────────

PHENO_DEFAULTS = {"cc", "zsh", "bash", "python", "claude", "fish", "sh"}


def mod_phenotype(data):
    if not os.environ.get("TMUX"):
        return []
    try:
        r = subprocess.run(
            ["tmux", "display-message", "-p", "#W"], capture_output=True, text=True, timeout=2
        )
        if r.stdout.strip() not in PHENO_DEFAULTS:
            return []
    except Exception:
        return []

    prompt = data.get("prompt", "").strip()
    if len(prompt) < 5:
        return []

    window_id = ""
    try:
        r = subprocess.run(
            ["tmux", "display-message", "-p", "#{window_id}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        window_id = r.stdout.strip()
    except Exception:
        pass

    # Fork Gemini call as background
    worker = HOOKS_DIR / "phenotype_rename.py"
    with contextlib.suppress(Exception):
        subprocess.Popen(
            [sys.executable, str(worker), prompt[:300], window_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return []


# ── association: REMOVED ──
# Crude TF-IDF over Reference/ docs on every prompt (with 5min debounce).
# Replaced by on-demand search via rheotaxis/histone MCP tools.


# ── rheotaxis: factual question detection ─────────────────

_RHEO_PATTERNS = [
    # Location questions — "where is X" (excluding code: "where is the function/file/bug")
    r"\bwhere\b.{0,5}\b(is|are|can|to)\b(?!.{0,10}\b(function|file|bug|error|class|method|variable|defined|declared)\b)",
    r"\b(nearest|closest|near me|nearby)\b",
    r"\b(is there|are there)\b.{0,20}\b(a |any )",
    # Hours/availability
    r"\b(what|when)\b.{0,15}\b(open|close|hour|time)\b",
    r"\b(how much|price|cost)\b.{0,20}\b(is|does|for)\b",
    r"\b(do they|does it|is it)\b.{0,15}\b(still|open|available|exist)\b",
    # Store/location explicit
    r"\b(store|shop|branch|outlet|restaurant|clinic)\b.{0,15}\b(location|address|in |at |near)\b",
]
_RHEO_RE = [re.compile(p, re.IGNORECASE) for p in _RHEO_PATTERNS]


def mod_rheotaxis(data):
    """Detect factual real-world questions and nudge toward search-first."""
    prompt = data.get("prompt", "")
    if not prompt or len(prompt) < 8:
        return []
    for pat in _RHEO_RE:
        if pat.search(prompt):
            return [
                "[rheotaxis] Factual real-world question detected. "
                "Search before asserting — use rheotaxis skill or "
                "rheotaxis_search MCP tool (pipe-separate queries for multi-framing). Never answer from model memory."
            ]
    return []


# ── named-tool pushback: named-entity + pushback detection ──

_PUSHBACK_PHRASES = [
    r"\bbut\b",
    r"\bactually\b",
    "\\bdidn[\u2019']t you\\b",
    r"\bhave you\b",
    r"\bare you sure\b",
    r"\breally\b",
    r"\bis it\b",
    r"\bdid you check\b",
    r"\byou said\b",
]
_PUSHBACK_RE = [re.compile(p, re.IGNORECASE) for p in _PUSHBACK_PHRASES]

_NAMED_STOPWORDS = frozenset(
    {
        "I",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
        "Group",
        "Compliance",
    }
)


def _sense_pushback(text: str) -> bool:
    return any(pat.search(text) for pat in _PUSHBACK_RE)


def _flag_named_antigens(text: str) -> list[str]:
    tokens = [tok.strip(".,;:!?'\"\u2019()[]{}") for tok in text.split()]
    entities: list[str] = []
    for i, tok in enumerate(tokens):
        if i == 0:
            continue
        if not tok or not tok[0].isupper():
            continue
        if tok in _NAMED_STOPWORDS:
            continue
        entities.append(tok)
    return entities


# ── oscillation: deliver warning flagged by dendrite ──

_OSCILLATION_SESSIONS_DIR = HOME / ".claude" / "projects" / "-home-vivesca"


def _oscillation_flag_path(session_id: str) -> Path:
    return _OSCILLATION_SESSIONS_DIR / f"{session_id}-oscillation-warning.flag"


def mod_oscillation_warning(data):
    """Deliver the oscillation warning dendrite raised, then consume the flag.

    Sub-detector C of the reactive-not-proactive family. Dendrite logs hash
    signatures on Edit/MultiEdit and writes a flag file when 3+ reversals
    are detected on the same file. This mod reads the flag at the next
    UserPromptSubmit and emits a non-blocking additionalContext warning.
    """
    session_id = data.get("session_id", "")
    if not session_id:
        return []
    flag_path = _oscillation_flag_path(session_id)
    if not flag_path.exists():
        return []
    try:
        flagged_path = flag_path.read_text(encoding="utf-8").strip()
    except OSError:
        return []
    with contextlib.suppress(OSError):
        flag_path.unlink()
    if not flagged_path:
        return []
    return [
        f"3+ reversals detected on `{flagged_path}` this session — sub-shape 8a "
        "(framing-driven oscillation). STOP and quorate this decision externally "
        "rather than reversing again. "
        "See `feedback_repeated_ask_signals_empirical_test.md`."
    ]


def mod_named_tool_pushback(data):
    prompt = data.get("prompt", "")
    if not prompt:
        return []
    if not _sense_pushback(prompt):
        return []
    antigens = _flag_named_antigens(prompt)
    if not antigens:
        return []
    names = ", ".join(antigens)
    return [
        f"User named specific entity/entities ({names}). "
        "Run rheotaxis on names BEFORE responding. "
        "See `finding_run_empirical_check_on_named_tools_immediately.md`."
    ]


# ── context: parked item injection ───────────────────────

DAILY_DIR = CHROMATIN_DIR / "Daily"


def _read_parked():
    """Extract ### Parked sections from today's daily note."""
    today = datetime.now(HKT).strftime("%Y-%m-%d")
    daily = DAILY_DIR / f"{today}.md"
    if not daily.exists():
        return []
    try:
        content = daily.read_text(encoding="utf-8")
    except Exception:
        return []
    items = []
    in_parked = False
    for line in content.splitlines():
        if line.strip().startswith("### Parked"):
            in_parked = True
            continue
        if in_parked:
            if line.startswith("###") or line.startswith("## "):
                in_parked = False
                continue
            stripped = line.strip().lstrip("- ").strip()
            if stripped and stripped != "none" and not stripped.startswith("[LLM"):
                items.append(stripped)
    return items


def mod_context(data):
    """Inject parked items from today's daily note on session start."""
    session_id = data.get("session_id", "")
    if not session_id:
        return []
    marker = TMP_DIR / f"context-inject-{session_id}.done"
    if marker.exists():
        return []
    marker.touch()

    parked = _read_parked()
    if not parked:
        return []
    # Deduplicate and truncate — keep token cost under ~200
    seen = set()
    unique = []
    for p in parked:
        key = p[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(p[:150])
    items = "\n".join(f"  - {p}" for p in unique[:5])
    return [f"Parked from earlier today (may be relevant):\n{items}"]


# ── entrainment: compact morning brief on "gm" ──────────────

_ENTRAIN_RE = re.compile(r"^(g+m+|good\s+morning|morning)[.!,\s]*$", re.IGNORECASE)
_ENTRAIN_QUEUE = HOME / "germline" / "loci" / "translation-queue.md"


def mod_entrainment(data):
    """Inject compact morning brief when 'gm' detected. Hook, not skill."""
    prompt = data.get("prompt", "").strip()
    session_id = data.get("session_id", "")
    if not prompt or len(prompt) > 30 or not _ENTRAIN_RE.match(prompt):
        return []

    # Once per session
    marker = TMP_DIR / f"entrainment-{session_id}.done"
    if marker.exists():
        return []
    marker.touch()

    parts = []

    # Calendar — fire-and-forget start, collect after weather
    cal_proc = None
    with contextlib.suppress(Exception):
        cal_proc = subprocess.Popen(
            ["fasti", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

    # Weather (one-liner)
    with contextlib.suppress(Exception):
        wx = subprocess.run(["hygroreception"], capture_output=True, text=True, timeout=5)
        if wx.returncode == 0 and wx.stdout.strip():
            parts.append(wx.stdout.strip().splitlines()[0])

    # Collect calendar
    if cal_proc:
        with contextlib.suppress(Exception):
            stdout, _ = cal_proc.communicate(timeout=5)
            if cal_proc.returncode == 0 and stdout.strip():
                events = [e.strip() for e in stdout.strip().splitlines()[:6] if e.strip()]
                parts.append("Today: " + " | ".join(events))

    # Ribosome queue summary
    with contextlib.suppress(Exception):
        content = _ENTRAIN_QUEUE.read_text()
        pending = len(re.findall(r"^- \[ \]", content, re.MULTILINE))
        retry = len(re.findall(r"^- \[!\]", content, re.MULTILINE))
        done = len(re.findall(r"^- \[x\]", content, re.MULTILINE))
        if pending or retry or done:
            parts.append(f"Queue: {pending} pending, {retry} retry, {done} done")

    if parts:
        return ["[entrainment] " + " | ".join(parts)]
    return []


# ── overnight: queue results on "what ran" ───────────────────

_OVERNIGHT_RE = re.compile(
    r"^(what ran|overnight|overnight results|queue status|what ran overnight)[?.!\s]*$",
    re.IGNORECASE,
)
_OVERNIGHT_QUEUE = HOME / "germline" / "loci" / "translation-queue.md"
_OVERNIGHT_TASK_RE = re.compile(
    r"^- \[([x!])\] `ribosome \[([^\]]+)\](?:\s*\[[^\]]*\])*\s*"
    r'(?:--\S+\s+\S+\s+)*"([^"]{0,80})'
)


def mod_overnight(data):
    """Inject queue results when 'what ran' / 'overnight' detected."""
    prompt = data.get("prompt", "").strip()
    if not prompt or len(prompt) > 40 or not _OVERNIGHT_RE.match(prompt):
        return []

    # Once per session
    session_id = data.get("session_id", "")
    marker = TMP_DIR / f"overnight-{session_id}.done"
    if marker.exists():
        return []
    marker.touch()

    try:
        content = _OVERNIGHT_QUEUE.read_text()
    except Exception:
        return []

    items = []
    for line in content.splitlines():
        match = _OVERNIGHT_TASK_RE.match(line)
        if match:
            status, task_id, desc = match.groups()
            icon = "done" if status == "x" else "RETRY"
            snippet = desc[:60].rstrip()
            if len(desc) > 60:
                snippet += "..."
            items.append(f"  {icon}: {task_id} — {snippet}")

    if not items:
        return ["[overnight] Queue is empty."]

    pending = len(re.findall(r"^- \[ \]", content, re.MULTILINE))
    header = f"[overnight] {len(items)} resolved, {pending} pending:"
    # Cap at 10 items to keep tokens low
    body = "\n".join(items[:10])
    if len(items) > 10:
        body += f"\n  ... and {len(items) - 10} more"
    return [f"{header}\n{body}"]


# ── telomere: context aging nudge ────────────────────────

_TELO_THRESHOLDS = {
    75: "[telomere] Session depth 75 — consider rewind (esc-esc) or proactive /compact with direction before context rots.",
    150: "[telomere] Session depth 150 — context aging. /clear with a brief, or /compact focus on <current goal>. New task = new session.",
}


def mod_telomere(data):
    """Nudge about context hygiene at depth thresholds."""
    session_id = data.get("session_id", "")
    if not session_id:
        return []

    # Read depth from allostasis state (written by mod_allostasis earlier in pipeline)
    try:
        state = json.loads(ALLOW_STATE.read_text())
        depth = state.get("depth", 0)
    except Exception:
        return []

    msg = _TELO_THRESHOLDS.get(depth)
    if not msg:
        return []

    heb = get_hebbian()
    if heb:
        with contextlib.suppress(Exception):
            heb.log_nudge("telomere", f"depth:{depth}")

    return [msg]


# ── main ───────────────────────────────────────────────────


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    modules = [
        mod_anamnesis,
        mod_allostasis,
        mod_chemoreceptor,
        mod_priming,
        mod_rheotaxis,
        mod_named_tool_pushback,
        mod_oscillation_warning,
        mod_mitogen,
        mod_senescence,
        mod_circaseptan,
        mod_calorimetry,
        mod_phenotype,
        mod_context,
        mod_entrainment,
        mod_overnight,
        mod_telomere,
    ]

    output = []
    for mod in modules:
        try:
            lines = mod(data)
            if lines:
                output.extend(lines)
        except Exception as e:
            print(f"[synapse] {mod.__name__} failed: {e}", file=sys.stderr)

    if output:
        print("\n".join(output))


if __name__ == "__main__":
    main()
