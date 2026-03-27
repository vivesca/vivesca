#!/usr/bin/env python3
"""synapse.py — consolidated UserPromptSubmit hook.

Replaces 11 separate hooks (9 Python + 2 Node.js) with a single process.
Saves ~500ms per prompt by eliminating process startup overhead.

Each module runs in try/except for fault isolation.
"""

import configparser
import contextlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
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


def get_hebbian():
    global _hebbian
    if _hebbian is None:
        try:
            import hebbian_nudge

            _hebbian = hebbian_nudge
        except ImportError:
            _hebbian = False
    return _hebbian if _hebbian else None


# ── anamnesis: session-start context loading ───────────────

ANAM_NOW = CHROMATIN_DIR / "Tonus.md"
ANAM_CONST = _VIVESCA_ROOT / "genome.md"
ANAM_DOMAINS = {
    "anatomy": {
        "code",
        "vivesca",
        "hook",
        "mcp",
        "rename",
        "tool",
        "skill",
        "substrate",
        "metabolism",
        "pipeline",
        "agent",
    },
    "effectors": {"cli", "command", "binary", "script", "tool", "run", "which"},
    "circadian": {
        "calendar",
        "meeting",
        "schedule",
        "tomorrow",
        "today",
        "week",
        "plan",
        "agenda",
    },
    "vitals": {
        "health",
        "gym",
        "oura",
        "sleep",
        "exercise",
        "hrv",
        "readiness",
        "workout",
        "pain",
        "headache",
    },
    "budget": {"budget", "token", "usage", "cost", "quota", "limit", "red", "respirometry"},
}
ANAM_KEYS = list(ANAM_DOMAINS.keys())


def _anam_score(prompt_lower):
    words = set(prompt_lower.split())
    scores = {k: len(words & v) for k, v in ANAM_DOMAINS.items()}
    return sorted(scores, key=lambda k: (-scores[k], k))


def _anam_load(key):
    if key == "anatomy":
        from metabolon.resources.anatomy import generate_anatomy

        return "Anatomy (auto-generated)", generate_anatomy()
    elif key == "effectors":
        from metabolon.resources.proteome import generate_effector_index

        return "Effectors (tool routing)", generate_effector_index()
    elif key == "circadian":
        from metabolon.organelles.circadian_clock import scheduled_events

        try:
            events = scheduled_events("today")
        except Exception:
            events = ""
        return "Circadian (today's schedule)", events
    elif key == "vitals":
        from metabolon.resources.vitals import generate_vitals

        return "Vitals", generate_vitals()
    elif key == "budget":
        r = subprocess.run(["respirometry"], capture_output=True, text=True, timeout=10)
        return "Budget", r.stdout.strip() if r.returncode == 0 else ""
    return "", ""


def mod_anamnesis(data):
    session_id = data.get("session_id", "")
    if not session_id:
        return []
    marker = TMP_DIR / f"vault-pull-{session_id}.done"
    if marker.exists():
        return []

    msg = data.get("message", {})
    prompt = msg.get("content", "") if isinstance(msg, dict) else ""
    prompt_lower = prompt.lower() if prompt else ""

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

    try:
        c = ANAM_CONST.read_text(encoding="utf-8").strip()
        if c:
            lines.append(f"\nConstitution (vivesca canonical rules):\n{c}")
    except Exception:
        pass

    order = _anam_score(prompt_lower) if prompt_lower else ANAM_KEYS
    for key in order:
        try:
            label, content = _anam_load(key)
            if content:
                lines.append(f"\n{label}:\n{content}")
        except Exception:
            pass

    return lines


# ── allostasis: budget/phase/depth regulation ──────────────

ALLO_STATE = HOME / ".local/share/respirometry/budget-tier.json"
ALLO_GUIDANCE = {
    "anabolic": "",
    "homeostatic": "Prefer Sonnet subagents for heavy work. Keep effort default.",
    "catabolic": "Switch to Sonnet. Single focused approach per problem. Minimize tool calls — verify critical facts only. No exploratory research or brainstorming.",
    "autophagic": "WRAP UP. Deliver what you have now. /sporulation immediately. No new work — checkpoint and stop.",
}
# Map respirometry budget tiers to metabolic states
_BUDGET_TO_STATE = {"green": "anabolic", "yellow": "homeostatic", "red": "catabolic"}
ALLO_CIRCADIAN = {
    "night": "Late night — consider wrapping up.",
    "evening": "",
    "morning": "",
    "day": "",
}


def _allo_budget():
    try:
        r = subprocess.run(
            ["respirometry-cached", "--budget"], capture_output=True, text=True, timeout=2
        )
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _allo_phase():
    h = datetime.now(HKT).hour
    if 6 <= h < 10:
        return "morning"
    elif 10 <= h < 17:
        return "day"
    elif 17 <= h < 21:
        return "evening"
    return "night"


def _allo_effective(budget, phase, depth):
    states = ["anabolic", "homeostatic", "catabolic", "autophagic"]
    metabolic = _BUDGET_TO_STATE.get(budget)
    if metabolic is None:
        return _BUDGET_TO_STATE.get("yellow", "homeostatic")
    idx = states.index(metabolic)
    if phase == "night" or (phase == "evening" and depth > 35):
        idx += 1
    elif phase == "morning":
        idx -= 1
    if depth > 50:
        idx += 1
    return states[max(0, min(idx, len(states) - 1))]


def mod_allostasis(data):
    session_id = data.get("session_id", "")
    state = {}
    with contextlib.suppress(Exception):
        state = json.loads(ALLO_STATE.read_text())

    prev_tier = state.get("tier", "")
    prev_session = state.get("session_id", "")
    depth = 1 if session_id != prev_session else state.get("depth", 0) + 1

    budget = _allo_budget()
    phase = _allo_phase()
    tier = _allo_effective(budget, phase, depth)

    ALLO_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALLO_STATE.write_text(
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

    g = ALLO_GUIDANCE.get(tier, "")
    if g:
        parts.append(g)
    c = ALLO_CIRCADIAN.get(phase, "")
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
    "linkedin.com/posts": "LinkedIn post -> use `/agoras` skill (agent-browser fetch, author research, voice rules)",
    "linkedin.com/feed/update": "LinkedIn post -> use `/agoras` skill (agent-browser fetch, author research, voice rules)",
    "linkedin.com/in/terrylihm": "Own LinkedIn profile -> use `linkedin-profile` skill (Featured, About, Headline, announcements)",
    "linkedin.com/in/": "LinkedIn profile -> use `linkedin-research` skill (agent-browser extraction)",
    "linkedin.com/jobs": "LinkedIn job -> use `/adhesion` skill",
    "youtube.com/watch": "YouTube URL -> use `video-digest` skill (transcript + structured digest)",
    "youtu.be/": "YouTube URL -> use `video-digest` skill (transcript + structured digest)",
    "bilibili.com/video": "Bilibili URL -> use `video-digest` skill (transcript + structured digest)",
    "xiaoyuzhou.fm": "Xiaoyuzhou URL -> use `video-digest` skill (podcast transcript + digest)",
    "x.com/": "X URL -> use `auceps <url>` (smart bird wrapper)",
    "twitter.com/": "Twitter URL -> use `auceps <url>` (smart bird wrapper)",
    "e.tb.cn": "Taobao link -> use `agent-browser --profile` (WebFetch blocked, login required)",
    "taobao.com": "Taobao -> use `agent-browser --profile` (WebFetch blocked, login required)",
    "tmall.com": "Tmall -> use `agent-browser --profile` (WebFetch blocked, login required)",
}
CHEMO_KEYWORDS = [
    (r"\blaunch exp\b", "Experiment -> invoke `peira` skill first"),
    (r"\brun exp(eriment)?\b", "Experiment -> invoke `peira` skill first"),
    (r"\bcompare .{3,40} vs\b", "Comparison -> invoke `peira` skill first"),
    (r"\bbenchmark\b", "Benchmark -> invoke `peira` skill first"),
    (r"\b(worked before|used to work|stopped working|broke[n]?|not found|command not found|regression|troubleshoot)\b",
     "Diagnosis -> invoke /etiology skill. Frame the problem (regression? new issue?) before attempting fixes"),
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

    pn = _prim_norm(prompt)
    matches = []
    for skill, phrases in triggers.items():
        for phrase in phrases:
            phn = _prim_norm(phrase)
            if len(phn) >= 4 and phn in pn:
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
    if "/nucleation" in prompt.lower():
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
            "[mitogen] Coding task detected — /nucleation available. (Suppressing further nudges this session.)"
        ]
    return [
        "[mitogen] Coding task detected — use /nucleation as the on-ramp. Don't implement in-session unless trivial (<50 lines, single file)."
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


def mod_circaseptan(data):
    now = datetime.now()
    if now.weekday() not in (5, 6):
        return []
    week = now.strftime("%G-W%V")
    if CIRC_WEEKLY.exists() and any(week in f.name for f in CIRC_WEEKLY.glob("*.md")):
        return []
    if CIRC_MARKER.exists() and now.timestamp() - CIRC_MARKER.stat().st_mtime < 7200:
        return []
    CIRC_MARKER.touch()
    return [f"Weekly review for {week} not yet done. Run `/ecdysis` when ready."]


# ── calorimetry: respirometry autolog ──────────────────────

CAL_STATE = HOME / ".local/share/respirometry/autolog-state.json"
CAL_INTERVAL = _sconf_int("calorimetry", "cal_interval", 1800)


def mod_calorimetry(data):
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


# ── association: keyword retrieval from Reference/ ─────────

ASSOC_REF = CHROMATIN_DIR / "Reference"
ASSOC_DEB = HOME / ".claude" / "retrieval-hook-state.json"
ASSOC_DEB_SEC = _sconf_int("association", "debounce_seconds", 300)
ASSOC_TOP_K = _sconf_int("association", "top_k", 3)
ASSOC_MIN = _sconf_float("association", "min_score", 1.5)
ASSOC_SKIP = {"knowledge-structure.md", ".obsidian", ".DS_Store"}
ASSOC_STOP = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "shall",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "about",
    "between",
    "through",
    "after",
    "before",
    "during",
    "without",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "i",
    "me",
    "my",
    "we",
    "our",
    "you",
    "your",
    "he",
    "she",
    "they",
    "them",
    "what",
    "which",
    "who",
    "how",
    "when",
    "where",
    "why",
    "and",
    "or",
    "but",
    "not",
    "no",
    "if",
    "then",
    "so",
    "just",
    "also",
    "more",
    "some",
    "any",
    "all",
    "each",
    "every",
    "up",
    "out",
    "now",
    "new",
    "get",
    "make",
    "like",
    "use",
    "check",
}


def _assoc_tok(text):
    return [
        w
        for w in re.findall(r"[a-z][a-z0-9_-]+", text.lower())
        if w not in ASSOC_STOP and len(w) > 2
    ]


def mod_association(data):
    prompt = data.get("prompt", "")
    if not prompt or len(prompt) < 10:
        return []

    try:
        if (
            ASSOC_DEB.exists()
            and time.time() - float(ASSOC_DEB.read_text().strip()) < ASSOC_DEB_SEC
        ):
            return []
    except Exception:
        pass

    qtok = _assoc_tok(prompt)
    if len(qtok) < 2:
        return []
    if not ASSOC_REF.exists():
        return []

    docs = {}
    for md in ASSOC_REF.rglob("*.md"):
        rel = str(md.relative_to(ASSOC_REF))
        if any(s in rel for s in ASSOC_SKIP):
            continue
        try:
            c = md.read_text(errors="replace")
            if len(c) > 50:
                docs[rel] = c
        except OSError:
            continue
    if not docs:
        return []

    qc = Counter(qtok)
    nd = len(docs)
    df = Counter()
    dc = {}
    for p, c in docs.items():
        nt = _assoc_tok(Path(p).stem.replace("-", " ").replace("_", " "))
        ct = _assoc_tok(c[:3000])
        tc = Counter(ct + nt * 3)
        dc[p] = tc
        df.update(tc.keys())

    scored = []
    for p, tc in dc.items():
        s = sum(
            (1 + math.log(tc[t])) * (math.log(nd / df.get(t, 1)) + 1) * qf
            for t, qf in qc.items()
            if tc.get(t, 0) > 0
        )
        if s >= ASSOC_MIN:
            scored.append((p, s))
    scored.sort(key=lambda x: -x[1])
    scored = scored[:ASSOC_TOP_K]
    if not scored:
        return []

    try:
        ASSOC_DEB.parent.mkdir(parents=True, exist_ok=True)
        ASSOC_DEB.write_text(str(time.time()))
    except OSError:
        pass

    lines = []
    for p, _ in scored:
        fp = ASSOC_REF / p
        try:
            c = fp.read_text(errors="replace")
        except OSError:
            continue
        heading = next((line.lstrip("#").strip() for line in c.splitlines() if line.startswith("#")), "")
        body = c
        if body.startswith("---"):
            end = body.find("---", 3)
            if end > 0:
                body = body[end + 3 :]
        snippet = " ".join(body.split()[:40])
        display = heading or Path(p).stem
        lines.append(f"- [[{Path(p).stem}]] ({p}): {display}")
        if snippet:
            lines.append(f"  {snippet}...")

    if lines:
        sug = "\n".join(lines)
        return [
            f"<reference-suggestions>\nPotentially relevant Reference docs:\n{sug}\nRead with Read tool if relevant.\n</reference-suggestions>"
        ]
    return []


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
                "rheotaxis_multi MCP tool. Never answer from model memory."
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
    items = "\n".join(f"  - {p}" for p in parked[:5])
    return [f"Parked from earlier today (may be relevant):\n{items}"]


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
        mod_association,
        mod_context,
    ]

    output = []
    for mod in modules:
        try:
            lines = mod(data)
            if lines:
                output.extend(lines)
        except Exception:
            pass

    if output:
        print("\n".join(output))


if __name__ == "__main__":
    main()
