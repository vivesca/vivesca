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
    lines.append(f"Current date/time: {now.strftime('%A, %d %B %Y (HKT)')}")

    try:
        c = ANAM_NOW.read_text(encoding="utf-8").strip()
        if c:
            lines.append(f"\nTonus.md (active session state):\n{c}")
    except Exception:
        pass

    # Dirty-state detection — warn if previous session left uncommitted work
    try:
        dirty = {}
        for label, repo in [("germline", HOME / "germline"), ("epigenome", EPIGENOME_DIR)]:
            r = subprocess.run(
                ["git", "-C", str(repo), "status", "--short"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            n = len([line for line in r.stdout.splitlines() if line.strip()])
            if n:
                dirty[label] = n
        if dirty:
            summary = ", ".join(f"{n} in {k}" for k, n in dirty.items())
            lines.append(
                f"Previous session left {summary} dirty files. Commit or review before new work."
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
    for skill, phrases in triggers.items():
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
    15: "[telomere] Session depth 15 — consider rewind (esc-esc) or proactive /compact with direction before context rots.",
    30: "[telomere] Session depth 30 — context aging. /clear with a brief, or /compact focus on <current goal>. New task = new session.",
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
