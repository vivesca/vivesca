"""potentiation — spaced repetition engine (potentiation = LTP, learning via timed stimulation)."""

# GARP RAI spaced repetition: FSRS scheduling, tracker markdown, session planning.
# Translated from Rust (~/code/melete/src/main.rs).

import itertools
import json
import math
import re
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from metabolon.locus import chromatin as _chromatin

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DESIRED_RETENTION: float = 0.9
TRACKER_FILE = "GARP RAI Quiz Tracker.md"
STATE_FILE = ".garp-fsrs-state.json"
DRILLS_FILE = "GARP RAI Definition Drills.md"

MODE_THRESHOLDS = [(0.60, "drill"), (0.70, "free-recall"), (1.01, "MCQ")]

EXAM_DATE = datetime(2026, 4, 4, 10, 45, 0, tzinfo=timezone(timedelta(hours=8)))

GARP_RAI_SYLLABUS = [
    "M1-ai-risks",
    "M1-classical-ai",
    "M1-ml-types",
    "M2-clustering",
    "M2-data-prep",
    "M2-econometric",
    "M2-intro-tools",
    "M2-model-estimation",
    "M2-model-eval",
    "M2-neural-networks",
    "M2-nlp-genai",
    "M2-nlp-traditional",
    "M2-regression-classification",
    "M2-semi-rl",
    "M2-semi-supervised",
    "M3-autonomy-safety",
    "M3-bias-unfairness",
    "M3-fairness-measures",
    "M3-genai-risks",
    "M3-global-challenges",
    "M3-reputational-existential",
    "M3-xai",
    "M4-bias-discrimination",
    "M4-ethical-frameworks",
    "M4-ethics-principles",
    "M4-governance-challenges",
    "M4-privacy-cybersecurity",
    "M4-regulatory",
    "M5-data-governance",
    "M5-genai-governance",
    "M5-governance-recommendations",
    "M5-implementation",
    "M5-model-changes-review",
    "M5-model-dev-testing",
    "M5-model-governance",
    "M5-model-risk-roles",
    "M5-model-validation",
]

# ---------------------------------------------------------------------------
# FSRS algorithm (pure Python, default parameters)
# ---------------------------------------------------------------------------
# Reference: https://github.com/open-spaced-repetition/fsrs4anki/wiki
# Default parameters from the fsrs-rs crate DEFAULT_PARAMETERS.

_FSRS_PARAMS = [
    0.4072,
    1.1829,
    3.1262,
    15.4722,
    7.2102,
    0.5316,
    1.0651,
    0.0589,
    1.5330,
    0.1544,
    1.0071,
    1.9395,
    0.1100,
    0.2900,
    2.2700,
    0.2500,
    2.9898,
    0.5100,
    0.3400,
]

# Rating indices: 1=Again, 2=Hard, 3=Good, 4=Easy
_AGAIN, _HARD, _GOOD, _EASY = 1, 2, 3, 4


def _fsrs_forgetting_curve(elapsed_days: float, stability: float) -> float:
    """Retrieve-ability after elapsed_days given stability."""

    if stability <= 0:
        return 0.0
    return (1 + elapsed_days / (9 * stability)) ** (-1)


def _fsrs_initial_stability(rating: int) -> float:
    w = _FSRS_PARAMS
    return w[rating - 1]  # w[0..3]


def _fsrs_initial_difficulty(rating: int) -> float:
    w = _FSRS_PARAMS
    # D0(r) = w[4] - exp(w[5] * (r - 1)) + 1
    return w[4] - math.exp(w[5] * (rating - 1)) + 1


def _fsrs_next_difficulty(difficulty: float, rating: int) -> float:
    w = _FSRS_PARAMS
    # D' = D - w[6] * (r - 3)
    d = difficulty - w[6] * (rating - 3)
    # Mean reversion: D'' = w[7] * D0(Good=3) + (1 - w[7]) * D'
    d0_good = _fsrs_initial_difficulty(3)
    d = w[7] * d0_good + (1 - w[7]) * d
    return max(1.0, min(10.0, d))


def _fsrs_next_stability_recall(
    difficulty: float, stability: float, retrievability: float, rating: int
) -> float:
    w = _FSRS_PARAMS
    hard_penalty = w[15] if rating == _HARD else 1.0
    easy_bonus = w[16] if rating == _EASY else 1.0
    s = stability * (
        math.exp(w[8])
        * (11 - difficulty)
        * (stability ** (-w[9]))
        * (math.exp((1 - retrievability) * w[10]) - 1)
        * hard_penalty
        * easy_bonus
    )
    return max(0.01, s)


def _fsrs_next_stability_forget(
    difficulty: float, stability: float, retrievability: float
) -> float:
    w = _FSRS_PARAMS
    s = (
        w[11]
        * (difficulty ** (-w[12]))
        * ((stability + 1) ** w[13])
        * math.exp((1 - retrievability) * w[14])
    )
    return max(0.01, s)


def _fsrs_interval(stability: float, desired_retention: float) -> float:
    """Optimal interval in days."""
    # From the forgetting curve: R = (1 + t/(9*S))^-1 => t = 9*S*(R^-1 - 1)
    if desired_retention >= 1.0:
        return stability
    t = 9.0 * stability * (desired_retention ** (-1) - 1)
    return max(1.0, t)


class _MemoryState:
    def __init__(self, stability: float, difficulty: float):
        self.stability = stability
        self.difficulty = difficulty


class _NextStates:
    def __init__(self, again, hard, good, easy):
        self.again = again
        self.hard = hard
        self.good = good
        self.easy = easy


class _CardState:
    def __init__(self, memory: _MemoryState, interval: float):
        self.memory = memory
        self.interval = interval


def fsrs_next_states(
    prev: _MemoryState | None,
    desired_retention: float,
    elapsed_days: int,
) -> _NextStates:
    """Compute next card states for all four ratings."""
    results = {}
    for rating in (_AGAIN, _HARD, _GOOD, _EASY):
        if prev is None:
            # New card
            s = _fsrs_initial_stability(rating)
            d = _fsrs_initial_difficulty(rating)
        else:
            s0, d0 = prev.stability, prev.difficulty
            r = _fsrs_forgetting_curve(elapsed_days, s0)
            d = _fsrs_next_difficulty(d0, rating)
            if rating == _AGAIN:
                s = _fsrs_next_stability_forget(d0, s0, r)
            else:
                s = _fsrs_next_stability_recall(d0, s0, r, rating)
        interval = _fsrs_interval(s, desired_retention)
        results[rating] = _CardState(_MemoryState(s, d), interval)
    return _NextStates(results[_AGAIN], results[_HARD], results[_GOOD], results[_EASY])


# ---------------------------------------------------------------------------
# Timezone helpers
# ---------------------------------------------------------------------------

HKT = timezone(timedelta(hours=8))


def _now_hkt() -> datetime:
    return datetime.now(tz=HKT)


def _today_hkt():
    return _now_hkt().date()


def _days_until_exam() -> int:
    return int((EXAM_DATE - _now_hkt()).total_seconds() // 86400)


def _parse_datetime(s: str) -> datetime | None:
    """Parse RFC3339 / ISO8601 string to aware datetime."""
    if not s:
        return None
    # Try standard formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    # Python <3.11 doesn't parse "+08:00" with %z in all formats; try fromisoformat
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    return None


def _card_due_hkt(card: dict) -> datetime | None:
    dt = _parse_datetime(card.get("due", ""))
    if dt is None:
        return None
    return dt.astimezone(HKT)


def _card_last_review(card: dict) -> datetime | None:
    lr = card.get("last_review")
    if not lr:
        return None
    dt = _parse_datetime(lr)
    return dt.astimezone(HKT) if dt else None


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _notes_dir() -> Path:
    return _chromatin


def _tracker_path() -> Path:
    return _notes_dir() / TRACKER_FILE


def _state_path() -> Path:
    return _notes_dir() / STATE_FILE


def _drills_path() -> Path:
    return _notes_dir() / DRILLS_FILE


def _module_path(module_char: str) -> Path:
    return _notes_dir() / f"GARP RAI Module {module_char} - Raw Content.md"


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{time.time_ns()}.tmp"
    tmp.write_text(content, encoding="utf-8")
    tmp.rename(path)


# ---------------------------------------------------------------------------
# Phase / quota
# ---------------------------------------------------------------------------


def _get_phase() -> tuple[int, str]:
    d = _today_hkt()
    from datetime import date

    cruise_end = date(2026, 3, 13)
    ramp_end = date(2026, 3, 28)
    if d <= cruise_end:
        return 1, "Cruise"
    elif d <= ramp_end:
        return 2, "Ramp"
    else:
        return 3, "Peak"


def _daily_quota() -> int:
    phase, _ = _get_phase()
    return {1: 10, 2: 15}.get(phase, 20)


def _module_weight(topic_id: str) -> float:
    prefix = topic_id.split("-")[0]
    return {"M1": 0.10, "M2": 0.30, "M3": 0.20, "M4": 0.20, "M5": 0.20}.get(prefix, 0.0)


def _get_mode(rate: float) -> str:
    for threshold, label in MODE_THRESHOLDS:
        if rate < threshold:
            return label
    return "MCQ"


def _state_name(state: int) -> str:
    return {1: "learning", 2: "review", 3: "relearning"}.get(state, "new")


# ---------------------------------------------------------------------------
# Rating helpers
# ---------------------------------------------------------------------------

RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY = "again", "hard", "good", "easy"

_RATING_ALIASES = {
    "again": RATING_AGAIN,
    "miss": RATING_AGAIN,
    "hard": RATING_HARD,
    "guess": RATING_HARD,
    "good": RATING_GOOD,
    "ok": RATING_GOOD,
    "easy": RATING_EASY,
    "confident": RATING_EASY,
}

_RATING_FSRS_INDEX = {
    RATING_AGAIN: _AGAIN,
    RATING_HARD: _HARD,
    RATING_GOOD: _GOOD,
    RATING_EASY: _EASY,
}

_RATING_RESULT_STR = {
    RATING_AGAIN: "MISS",
    RATING_HARD: "OK-GUESS",
    RATING_GOOD: "OK",
    RATING_EASY: "OK",
}

_RATING_DISPLAY_STR = {
    RATING_AGAIN: "Again (miss)",
    RATING_HARD: "Hard (guess)",
    RATING_GOOD: "Good",
    RATING_EASY: "Easy",
}


def _rating_from_str(s: str) -> str | None:
    return _RATING_ALIASES.get(s.lower())


# ---------------------------------------------------------------------------
# Card helpers
# ---------------------------------------------------------------------------


def _new_card(now: datetime) -> dict:
    return {
        "card_id": int(time.time() * 1000),
        "state": 1,
        "step": 0,
        "stability": 0.0,
        "difficulty": 0.0,
        "due": now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "last_review": now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    }


def _schedule_card(card: dict, rating: str, now: datetime) -> dict:
    card = dict(card)
    s, d = card.get("stability", 0.0), card.get("difficulty", 0.0)
    prev = _MemoryState(s, d) if s > 0.0 and d > 0.0 else None

    last_review_dt = _card_last_review(card)
    elapsed = max(0, (now - last_review_dt).days) if last_review_dt is not None else 0

    next_states = fsrs_next_states(prev, DESIRED_RETENTION, elapsed)
    fsrs_idx = _RATING_FSRS_INDEX[rating]
    item = {
        _AGAIN: next_states.again,
        _HARD: next_states.hard,
        _GOOD: next_states.good,
        _EASY: next_states.easy,
    }[fsrs_idx]

    interval_days = max(1.0, item.interval)
    raw_due = now + timedelta(seconds=round(interval_days * 86400))

    # Cap at 2 days before exam
    exam_cutoff = EXAM_DATE - timedelta(days=2)
    due = min(raw_due, exam_cutoff)

    was_new = prev is None
    if rating == RATING_AGAIN:
        new_state = 1 if was_new else 3
        step = 0
    else:
        new_state = 2
        step = None

    card["state"] = new_state
    card["step"] = step
    card["stability"] = item.memory.stability
    card["difficulty"] = item.memory.difficulty
    card["last_review"] = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    card["due"] = due.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    if not card.get("card_id"):
        card["card_id"] = int(time.time() * 1000)

    return card


# ---------------------------------------------------------------------------
# State I/O
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    path = _state_path()
    if not path.exists():
        return {"cards": {}, "review_log": []}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        print("\033[31mWarning: corrupt state file, starting fresh\033[0m", file=sys.stderr)
        return {"cards": {}, "review_log": []}

    cards = {}
    for topic, v in raw.get("cards", {}).items():
        if isinstance(v, str):
            try:
                card = json.loads(v)
            except Exception:
                card = None
        elif isinstance(v, dict):
            card = v
        else:
            card = None
        if card:
            cards[topic] = card
        else:
            print(f"\033[33mWarning: skipping corrupt card for {topic}\033[0m", file=sys.stderr)

    return {"cards": cards, "review_log": raw.get("review_log", [])}


def _save_state(state: dict) -> None:
    path = _state_path()
    cutoff = (_now_hkt() - timedelta(days=90)).isoformat()
    log = [e for e in state["review_log"] if e.get("date", "") >= cutoff]

    cards_map = {topic: json.dumps(card) for topic, card in state["cards"].items()}
    out = {"cards": cards_map, "review_log": log}
    _atomic_write(path, json.dumps(out, indent=2))


# ---------------------------------------------------------------------------
# Tracker parsing
# ---------------------------------------------------------------------------

_TOPIC_ROW_RE = re.compile(
    r"^\|\s*(M\d-[\w-]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d\u2014-]+%?)\s*\|",
    re.MULTILINE,
)
_SUMMARY_RE = re.compile(
    r"^\|\s*Total Questions\s*\|\s*(\d+)\s*\|.*?"
    r"^\|\s*Correct\s*\|\s*(\d+)\s*\|.*?"
    r"^\|\s*Rate\s*\|\s*(\d+)%\s*\|.*?"
    r"^\|\s*Sessions\s*\|\s*(\d+)\s*\|",
    re.MULTILINE | re.DOTALL,
)
_MISS_ROW_RE = re.compile(r"^\|\s*([\d-]+)\s*\|\s*(M\d-[\w-]+)\s*\|\s*(.+?)\s*\|")


def _parse_tracker() -> dict:
    path = _tracker_path()
    if not path.exists():
        return {"summary": {}, "topics": {}, "recent_misses": []}

    text = path.read_text(encoding="utf-8")
    topics = {}
    for m in _TOPIC_ROW_RE.finditer(text):
        topic = m.group(1)
        attempts = int(m.group(2))
        correct = int(m.group(3))
        rate_str = m.group(4).strip()
        rate = 0.0 if rate_str in ("—", "-", "") else float(rate_str.rstrip("%")) / 100.0
        topics[topic] = {"attempts": attempts, "correct": correct, "rate": rate}

    summary = {}
    m = _SUMMARY_RE.search(text)
    if m:
        summary = {
            "total": int(m.group(1)),
            "correct": int(m.group(2)),
            "rate": int(m.group(3)),
            "sessions": int(m.group(4)),
        }

    recent_misses = []
    in_misses = False
    for line in text.splitlines():
        if "## Recent Misses" in line:
            in_misses = True
            continue
        if in_misses and line.startswith("## "):
            break
        if in_misses:
            m2 = _MISS_ROW_RE.match(line)
            if m2 and m2.group(1) != "Date":
                recent_misses.append(
                    {
                        "date": m2.group(1),
                        "topic": m2.group(2),
                        "concept": m2.group(3).strip(),
                    }
                )

    if not topics:
        print(
            "\033[33mWarning: No topics parsed from tracker. Check markdown format.\033[0m",
            file=sys.stderr,
        )

    return {"summary": summary, "topics": topics, "recent_misses": recent_misses}


# ---------------------------------------------------------------------------
# Tracker update
# ---------------------------------------------------------------------------


def _update_tracker_record(topic: str, rating: str, note: str | None) -> None:
    path = _tracker_path()
    if not path.exists():
        return

    text = path.read_text(encoding="utf-8")
    is_correct = rating in (RATING_GOOD, RATING_EASY)

    def replace_summary(t: str) -> str:
        m_total = re.search(r"(\|\s*Total Questions\s*\|\s*)(\d+)(\s*\|)", t)
        m_correct = re.search(r"(\|\s*Correct\s*\|\s*)(\d+)(\s*\|)", t)
        re.search(r"(\|\s*Rate\s*\|\s*)(\d+)(%\s*\|)", t)
        if m_total and m_correct:
            new_total = int(m_total.group(2)) + 1
            new_correct = int(m_correct.group(2)) + (1 if is_correct else 0)
            new_rate = round(new_correct / new_total * 100) if new_total else 0
            t = t[: m_total.start(2)] + str(new_total) + t[m_total.end(2) :]
            # Recompute positions after replacement
            m_correct2 = re.search(r"(\|\s*Correct\s*\|\s*)(\d+)(\s*\|)", t)
            if m_correct2:
                t = t[: m_correct2.start(2)] + str(new_correct) + t[m_correct2.end(2) :]
            m_rate2 = re.search(r"(\|\s*Rate\s*\|\s*)(\d+)(%\s*\|)", t)
            if m_rate2:
                t = t[: m_rate2.start(2)] + str(new_rate) + t[m_rate2.end(2) :]
        return t

    text = replace_summary(text)

    # Update topic row
    topic_pat = re.compile(
        r"(\|\s*"
        + re.escape(topic)
        + r"\s*\|\s*)(\d+)(\s*\|\s*)(\d+)(\s*\|\s*)([\d\u2014-]+%?)(\s*\|)"
    )
    m = topic_pat.search(text)
    if m:
        na = int(m.group(2)) + 1
        nc = int(m.group(4)) + (1 if is_correct else 0)
        nr = round(nc / na * 100) if na else 0
        text = (
            text[: m.start(2)]
            + str(na)
            + text[m.end(2) : m.start(4)]
            + str(nc)
            + text[m.end(4) : m.start(6)]
            + f"{nr}%"
            + text[m.end(6) :]
        )

    note_cell = f"(recorded via rai) \u2014 {note}" if note else "(recorded via rai)"
    history_line = f"| {_now_hkt().strftime('%Y-%m-%d')} | {topic} | {_RATING_RESULT_STR[rating]} | {note_cell} |"

    lines = text.splitlines()
    last_idx = None
    in_history = False
    for i, line in enumerate(lines):
        if "## History" in line:
            in_history = True
        elif in_history and line.startswith("## "):
            break
        elif in_history and line.startswith("|") and "Date" not in line and "---" not in line:
            last_idx = i

    if last_idx is not None:
        lines.insert(last_idx + 1, history_line)
    elif in_history:
        for i, line in enumerate(lines):
            if "## History" in line:
                lines.insert(i + 1, history_line)
                break

    _atomic_write(path, "\n".join(lines))


# ---------------------------------------------------------------------------
# Drills
# ---------------------------------------------------------------------------


def _topics_with_drills() -> set:
    path = _drills_path()
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"\((M\d-[\w-]+)")
    out = set()
    for line in text.splitlines():
        if line.startswith("## "):
            m = pattern.search(line)
            if m:
                out.add(m.group(1))
    return out


# ---------------------------------------------------------------------------
# Topic search
# ---------------------------------------------------------------------------

_SEARCH_TERMS: dict[str, list[str]] = {
    "M1-classical-ai": ["Classical AI", "GOFAI", "Limits of Classical"],
    "M1-ml-types": ["Types of Machine Learning", "Four Types"],
    "M1-ai-risks": ["Risks of Inscrutability", "Risks of Over-Reliance"],
    "M2-intro-tools": ["Machine Learning, Classical Statistics"],
    "M2-data-prep": ["Data Scaling", "normalization", "standardization"],
    "M2-data-types": ["Data Collection And Preparation", "Structured", "Unstructured"],
    "M2-data-cleaning": ["Data Cleaning", "1.3.2"],
    "M2-train-val-test-split": ["Training Validation And Testing", "Cross Validation", "7.7"],
    "M2-linear-regression": ["Ordinary Least Squares", "7.2 Least Squares", "Linear Regression"],
    "M2-rl-value-functions": ["Terminology in Reinforcement", "Value Function", "Action-Value"],
    "M2-nlp-pipeline": ["Data Pre Processing", "Tokenization", "Stemming", "Lemmatization"],
    "M2-clustering": ["K-means", "Hierarchical Clustering", "DBSCAN"],
    "M2-econometric": ["Econometric", "Stepwise", "Variable Selection"],
    "M2-regression-classification": [
        "Decision Tree",
        "Random Forest",
        "SVM",
        "Logistic Regression",
    ],
    "M2-semi-supervised": ["Semi-supervised Learning Assumptions", "Self-Training", "Co-Training"],
    "M2-neural-networks": ["Neural Net", "Deep Learning", "Overfitting", "Dropout"],
    "M2-semi-rl": ["Reinforcement Learning", "Q-learning", "TD Learning", "Monte Carlo"],
    "M2-model-estimation": ["Regularization", "Ridge", "LASSO", "Elastic Net"],
    "M2-model-eval": ["Model Evaluation", "Precision", "Recall", "AUC", "ROC"],
    "M2-nlp-traditional": ["Tokenization", "Stemming", "Lemmatization", "TF-IDF"],
    "M2-nlp-genai": ["Transformer", "BERT", "GPT", "Attention Mechanism"],
    "M3-bias-unfairness": ["Sources of Unfairness", "Algorithmic Bias", "Historical Bias"],
    "M3-fairness-measures": [
        "Group Fairness",
        "Demographic Parity",
        "Equal Opportunity",
        "Equalized Odds",
    ],
    "M3-xai": ["Explainability", "Interpretability", "LIME", "SHAP", "LUCID"],
    "M3-autonomy-safety": ["Autonomy", "Manipulation", "Automation Bias", "Well-Being"],
    "M3-reputational-existential": ["Reputational Risk", "Existential Risk"],
    "M3-genai-risks": ["GenAI", "Generative AI", "Hallucination", "Deepfake"],
    "M4-ethical-frameworks": [
        "Ethical Framework",
        "Consequentialism",
        "Deontology",
        "Virtue Ethics",
    ],
    "M4-ethics-principles": ["Ethics Principles", "Beneficence", "Justice", "Non-maleficence"],
    "M4-bias-discrimination": ["Bias, Discrimination", "Problematic Biases", "When Does Bias"],
    "M4-privacy-cybersecurity": ["Privacy", "Cybersecurity", "Data Minimization"],
    "M4-governance-challenges": ["Governance Challenges", "Power Asymmetries"],
    "M4-regulatory": ["GDPR", "EU AI Act", "Regulatory", "AI Office"],
    "M5-data-governance": ["Data Governance", "Data Quality", "Alternative Data"],
    "M5-model-governance": ["Model Governance", "Model Landscape", "Interdependencies"],
    "M5-model-risk-roles": ["Three Lines", "Model Risk Management", "First Line"],
    "M5-model-dev-testing": ["Model Development", "Model Testing"],
    "M5-model-validation": ["Model Validation", "Validation Framework"],
    "M5-model-changes-review": ["Model Changes", "Model Review", "Ongoing Monitoring"],
    "M5-genai-governance": ["GenAI Governance", "Stochasticity", "Third-Party", "Provider"],
}


def _normalize(s: str) -> str:
    return "".join(c.lower() for c in s if c.isalnum())


def _find_source_location(topic: str) -> str | None:
    if len(topic) < 2:
        return None
    module_char = topic[1]
    module_file = _module_path(module_char)
    if not module_file.exists():
        return None

    if topic in _SEARCH_TERMS:
        terms = _SEARCH_TERMS[topic]
    else:
        suffix = topic.split("-", 1)[1] if "-" in topic else topic
        terms = [w.capitalize() for w in suffix.split("-") if len(w) > 2]

    lines = module_file.read_text(encoding="utf-8").splitlines()
    seen: set = set()
    hits = []

    for i, line in enumerate(lines):
        if line.startswith("##"):
            for term in terms:
                if term.lower() in line.lower():
                    h = line.strip()
                    if h not in seen:
                        seen.add(h)
                        hits.append(i)
                    break

    if not hits:
        for i, line in enumerate(lines):
            matched = False
            for term in terms:
                if term.lower() in line.lower():
                    upper = min(i + 6, len(lines))
                    long_nearby = any(len(lines[j]) > 80 for j in range(i + 1, upper))
                    if long_nearby:
                        hits.append(max(0, i - 2))
                    matched = True
                    break
            if matched and len(hits) >= 2:
                break

    if not hits:
        return None

    start = hits[0]
    end = min(start + 80, len(lines))
    for i in range(start + 4, end):
        if lines[i].startswith("## "):
            end = i
            break

    return f"{module_file}:{start + 1}-{end}"


def _resolve_topic(input_str: str, tracker: dict) -> str | None:
    topics = tracker["topics"]
    if input_str in topics:
        return input_str

    q = input_str.lower()
    for t in topics:
        if t.lower() == q:
            print(f"\033[2mMatched: {t}\033[0m")
            return t

    # Build alias map
    alias_map: dict[str, set] = defaultdict(set)
    for topic in topics:
        aliases = [topic.lower()]
        if "-" in topic:
            suffix = topic.split("-", 1)[1]
            aliases.append(suffix.lower())
            aliases.append(suffix.replace("-", " ").lower())
            aliases.append(_normalize(suffix))
        aliases.append(_normalize(topic))
        for term in _SEARCH_TERMS.get(topic, []):
            aliases.append(term.lower())
            aliases.append(_normalize(term))
        for a in aliases:
            alias_map[a].add(topic)

    matches: set = set()
    if q in alias_map:
        matches.update(alias_map[q])
    qn = _normalize(input_str)
    if qn in alias_map:
        matches.update(alias_map[qn])

    if not matches:
        for t in topics:
            tl = t.lower()
            ts = t.split("-", 1)[1].lower() if "-" in t else tl
            if tl.find(q) >= 0 or ts.find(q) >= 0 or q.find(ts) >= 0:
                matches.add(t)

    if len(matches) == 1:
        m = next(iter(matches))
        print(f"\033[2mMatched: {m}\033[0m")
        return m

    if matches:
        print("\033[33mAmbiguous:\033[0m")
        for m in sorted(matches):
            print(f"  - {m}")
        return None

    print(f"\033[31mUnknown topic: {input_str}\033[0m")
    return None


# ---------------------------------------------------------------------------
# TTY / display helpers
# ---------------------------------------------------------------------------


def _is_tty() -> bool:
    return sys.stdout.isatty()


def _print_panel(title: str) -> None:
    if _is_tty():
        BOX_TOP_LEFT = "\u256d"
        BOX_HORIZ = "\u2500"
        BOX_TOP_RIGHT = "\u256e"
        BOX_VERT = "\u2502"
        BOX_BOTTOM_LEFT = "\u2570"
        BOX_BOTTOM_RIGHT = "\u256f"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        w = len(title) + 2
        print()
        print(f"{BOX_TOP_LEFT}{BOX_HORIZ * w}{BOX_TOP_RIGHT}")
        print(f"{BOX_VERT} {BOLD}{title}{RESET} {BOX_VERT}")
        print(f"{BOX_BOTTOM_LEFT}{BOX_HORIZ * w}{BOX_BOTTOM_RIGHT}")
    else:
        print(f"## {title}")


def _color(text: str, code: str) -> str:
    if not _is_tty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _red(t: str) -> str:
    return _color(t, "31")


def _green(t: str) -> str:
    return _color(t, "32")


def _yellow(t: str) -> str:
    return _color(t, "33")


def _cyan(t: str) -> str:
    return _color(t, "36")


def _bold(t: str) -> str:
    return _color(t, "1")


def _dim(t: str) -> str:
    return _color(t, "2")


def _bright_green(t: str) -> str:
    return _color(t, "92")


def _bright_magenta(t: str) -> str:
    return _color(t, "95")


# ---------------------------------------------------------------------------
# Today's reviews helper
# ---------------------------------------------------------------------------


def _get_today_reviews(state: dict) -> list:
    today = str(_today_hkt())
    return [e for e in state["review_log"] if e.get("date", "").startswith(today)]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_session(count: int | None = None) -> None:
    state = _load_state()
    tracker = _parse_tracker()
    now = _now_hkt()
    days_left = _days_until_exam()
    phase_num, phase_name = _get_phase()
    n = count if count is not None else _daily_quota()

    if n < 1:
        print(_red("Session count must be positive"), file=sys.stderr)
        sys.exit(1)

    today_reviews = _get_today_reviews(state)
    tested_today = {e["topic"] for e in today_reviews}
    q_per_session = _daily_quota()

    if len(today_reviews) >= q_per_session:
        print()
        print(
            f"  {_green(f'Already done {len(today_reviews)} questions today ({len(tested_today)} topics). Quota met.')}"
        )
        print(f"  {_dim('Continuing with unreviewed topics...')}")
        print()

    due = []
    for topic, card in state["cards"].items():
        if topic in tested_today:
            continue
        info = tracker["topics"].get(topic, {"attempts": 0, "correct": 0, "rate": 0.0})
        due_dt = _card_due_hkt(card)
        if due_dt is not None:
            if due_dt <= now:
                overdue = (now - due_dt).days
                due.append((topic, info, overdue))
        else:
            due.append((topic, info, 999))

    due.sort(
        key=lambda x: (
            -x[2],
            -_module_weight(x[0]),
            x[1].get("rate", 0.0),
        )
    )

    weak = [x for x in due if x[1].get("rate", 0.0) < 0.60]
    strong = [x for x in due if x[1].get("rate", 0.0) >= 0.60]

    max_weak = min(len(weak), max(1, int(n * 0.6)))
    selected = weak[:max_weak]
    need = n - len(selected)
    selected.extend(strong[:need])

    if len(selected) < n:
        used = {x[0] for x in selected}
        for item in due:
            if len(selected) >= n:
                break
            if item[0] not in used:
                selected.append(item)

    selected = selected[:n]

    # Interleave: avoid 2+ same-module consecutive
    interleaved = []
    remaining = list(selected)
    while remaining:
        if len(interleaved) >= 2:
            last_mod = interleaved[-1][0][:2]
            prev_mod = interleaved[-2][0][:2]
            if last_mod == prev_mod:
                pos = next((i for i, x in enumerate(remaining) if x[0][:2] != last_mod), None)
                if pos is not None:
                    interleaved.append(remaining.pop(pos))
                else:
                    interleaved.append(remaining.pop(0))
                continue
        interleaved.append(remaining.pop(0))

    summary = tracker.get("summary", {})
    _print_panel(f"Session Plan | Phase {phase_num} ({phase_name}) | {days_left} days to exam")
    print(
        f"  Overall: {summary.get('correct', 0)}/{summary.get('total', 0)} "
        f"({summary.get('rate', 0)}%)  |  {summary.get('sessions', 0)} sessions"
    )

    m12 = sum(1 for t, _, _ in interleaved if t.startswith("M1-") or t.startswith("M2-"))
    if interleaved and (m12 / len(interleaved)) < 0.30:
        print(f"  {_yellow(f'M1/M2 quota: {m12}/{len(interleaved)} (target >=30%)')}")
    print()

    recent_misses = tracker.get("recent_misses", [])
    if recent_misses:
        print(_bold("Recent misses:"))
        for miss in list(reversed(recent_misses[-5:])):
            print(f"  - {miss['concept']} ({miss['date']}) [{miss['topic']}]")
        print()

    drilled = _topics_with_drills()
    print(_bold(f"Questions ({len(interleaved)}):"))
    print()

    for idx, (topic, info, overdue) in enumerate(interleaved):
        is_new = info.get("attempts", 0) == 0
        mode = "drill" if is_new else _get_mode(info.get("rate", 0.0))
        colored_topic = (
            _red(_bold(topic))
            if mode == "drill"
            else _yellow(_bold(topic))
            if mode == "free-recall"
            else _green(_bold(topic))
        )
        drill_tag = f" {_cyan('[drill]')}" if topic in drilled else ""
        new_tag = f" {_bright_magenta('[new]')}" if is_new else ""
        source = _find_source_location(topic) or "not found"
        weight_pct = round(_module_weight(topic) * 100)
        accuracy_str = "0%" if is_new else f"{info.get('rate', 0.0) * 100:.0f}%"
        print(
            f"  Q{idx + 1}: {colored_topic}  |  {mode} ({accuracy_str})"
            f"  |  overdue {overdue}d  |  wt {weight_pct}%{drill_tag}{new_tag}"
        )
        print(f"      {_dim(source)}")
    print()


def cmd_record(
    topic_input: str,
    rating_str: str,
    confidence: str | None = None,
    dry_run: bool = False,
    note: str | None = None,
) -> None:
    conf = None
    if confidence:
        cu = confidence.upper()
        if cu not in ("C", "U", "G"):
            print(_red(f"Invalid confidence: {confidence}. Valid: C, U, G"), file=sys.stderr)
            sys.exit(1)
        conf = cu

    rating = _rating_from_str(rating_str)
    if rating is None:
        print(
            _red(
                f"Unknown rating: {rating_str}. "
                "Valid: again/miss, hard/guess, good/ok, easy/confident"
            )
        )
        return

    state = _load_state()
    tracker = _parse_tracker()

    topic = topic_input if topic_input in state["cards"] else _resolve_topic(topic_input, tracker)
    if topic is None:
        return

    intended_rating = rating
    topic_info = tracker["topics"].get(topic, {"attempts": 0, "correct": 0, "rate": 0.0})
    topic_rate = topic_info.get("rate", 0.0)

    if topic_rate < 0.60 and rating in (RATING_GOOD, RATING_EASY):
        print(
            f"  {_yellow(f'Acquisition cap: {topic} at {topic_rate * 100:.0f}% -- capping {rating_str} -> hard')}"
        )
        rating = RATING_HARD

    now = _now_hkt()
    pre_review_card = state["cards"].get(topic)
    card = dict(pre_review_card) if pre_review_card else _new_card(now)
    card = _schedule_card(card, rating, now)

    if not dry_run:
        state["cards"][topic] = card
        state["review_log"].append(
            {
                "topic": topic,
                "rating": rating,
                "date": now.isoformat(),
                "confidence": conf,
                "card_snapshot": pre_review_card,
            }
        )
        _save_state(state)
        _update_tracker_record(topic, intended_rating, note)

    due_hkt = _card_due_hkt(card) or now
    days = (due_hkt - _now_hkt()).days

    if rating == RATING_AGAIN:
        display = _red(_RATING_DISPLAY_STR[rating])
    elif rating == RATING_HARD:
        display = _yellow(_RATING_DISPLAY_STR[rating])
    elif rating == RATING_GOOD:
        display = _green(_RATING_DISPLAY_STR[rating])
    else:
        display = _bright_green(_RATING_DISPLAY_STR[rating])

    print()
    dry_suffix = f"  {_dim('(dry run)')}" if dry_run else ""
    print(f"  {display}  {_bold(topic)}{dry_suffix}")
    print(
        f"  Next: {_cyan(due_hkt.strftime('%b %d'))} ({days:+d}d)  |  {_state_name(card['state'])}"
    )
    if not dry_run:
        if pre_review_card:
            print(f"  {_dim('snapshot saved')}")
        else:
            print(f"  {_dim('no snapshot (first record or pre-snapshot entry)')}")
    if note:
        print(f"  {_dim('Note')}  {note}")
    print()


def cmd_void(topic_input: str, dry_run: bool = False) -> None:
    state = _load_state()

    indices = [i for i, e in enumerate(state["review_log"]) if e["topic"] == topic_input]
    if not indices:
        print(f"No review history found for {topic_input}", file=sys.stderr)
        sys.exit(1)

    last_idx = indices[-1]
    last_entry = state["review_log"][last_idx]
    dry_suffix = "  (dry run)" if dry_run else ""

    if len(indices) == 1:
        msg = (
            f"Would void last review for {topic_input} (was: {last_entry['rating']} "
            f"on {last_entry['date']}). Topic reset to new{dry_suffix}"
            if dry_run
            else (
                f"Voided last review for {topic_input} (was: {last_entry['rating']} "
                f"on {last_entry['date']}). Topic reset to new"
            )
        )
        if not dry_run:
            del state["review_log"][last_idx]
            state["cards"][topic_input] = _new_card(_now_hkt())
            _save_state(state)
        print(msg)
    else:
        prev_idx = indices[-2]
        restored_card = last_entry.get("card_snapshot") or state["review_log"][prev_idx].get(
            "card_snapshot"
        )

        if restored_card:
            due_dt = _card_due_hkt(restored_card)
            next_due_str = due_dt.strftime("%Y-%m-%d") if due_dt else restored_card.get("due", "")
        else:
            next_due_str = "(unknown -- no snapshot available)"

        msg = (
            f"Would void last review for {topic_input} (was: {last_entry['rating']} "
            f"on {last_entry['date']}). Next due: {next_due_str}{dry_suffix}"
            if dry_run
            else (
                f"Voided last review for {topic_input} (was: {last_entry['rating']} "
                f"on {last_entry['date']}). Next due: {next_due_str}"
            )
        )
        if not dry_run:
            del state["review_log"][last_idx]
            if restored_card:
                state["cards"][topic_input] = restored_card
            else:
                print(
                    "Warning: no card_snapshot on voided entry -- FSRS card state not restored. "
                    "Re-run `melete record` to re-establish scheduling.",
                    file=sys.stderr,
                )
            _save_state(state)
        print(msg)


def cmd_end() -> None:
    state = _load_state()
    path = _tracker_path()
    if not path.exists():
        print(_red("Tracker not found"))
        return

    text = path.read_text(encoding="utf-8")
    m = re.search(r"(\|\s*Sessions\s*\|\s*)(\d+)(\s*\|)", text)
    if not m:
        print(_red("Sessions row not found in tracker"))
        return

    old = int(m.group(2))
    new = old + 1
    text = text[: m.start(2)] + str(new) + text[m.end(2) :]
    _atomic_write(path, text)

    print()
    print(f"  Session {_bold(str(new))} recorded (was {old})")

    today_reviews = _get_today_reviews(state)
    confident_misses = [
        r
        for r in today_reviews
        if r.get("rating", "").lower() in ("again", "miss") and r.get("confidence") == "C"
    ]
    if confident_misses:
        print()
        print(_yellow(_bold("  Confident misses this session:")))
        topics_cm = sorted({r["topic"] for r in confident_misses})
        print(f"   Topics: {', '.join(topics_cm)}")
        print(
            "   -> These are high-priority for next session -- overconfidence is the most dangerous blind spot."
        )
    print()


def cmd_today() -> None:
    state = _load_state()
    phase_num, phase_name = _get_phase()
    today_reviews = _get_today_reviews(state)
    q_per_session = _daily_quota()

    topics_today: set = set()
    correct_today = 0
    miss_today = 0

    for r in today_reviews:
        topics_today.add(r["topic"])
        rl = r.get("rating", "").lower()
        if rl in ("good", "ok", "easy", "confident"):
            correct_today += 1
        elif rl in ("again", "miss"):
            miss_today += 1

    total_today = len(today_reviews)

    sessions_today = 0
    if today_reviews:
        sessions_today = 1
        sorted_reviews = sorted(today_reviews, key=lambda r: r.get("date", ""))
        for a, b in itertools.pairwise(sorted_reviews):
            dt_a = _parse_datetime(a.get("date", ""))
            dt_b = _parse_datetime(b.get("date", ""))
            if dt_a and dt_b and (dt_b - dt_a).total_seconds() > 1800:
                sessions_today += 1

    quota_met = total_today >= q_per_session

    _print_panel(f"Today | Phase {phase_num} ({phase_name}) | {_days_until_exam()} days to exam")

    if total_today == 0:
        print(f"  {_dim('No reviews today.')}")
    else:
        rate = round(correct_today / total_today * 100)
        print(
            f"  Questions: {total_today}  |  Correct: {correct_today}  |  "
            f"Missed: {miss_today}  |  Rate: {rate}%"
        )
        print(f"  Sessions: ~{sessions_today}  |  Topics: {len(topics_today)}")
        if quota_met:
            print(f"  {_green(f'Daily quota met ({q_per_session}+ questions)')}")
        else:
            remaining = q_per_session - total_today
            print(
                f"  {_yellow(f'O {remaining} more questions to meet daily quota ({q_per_session})')}"
            )

    if today_reviews:
        print()
        print(_bold("Topics reviewed today:"))
        topic_results: dict[str, list] = defaultdict(list)
        for r in today_reviews:
            topic_results[r["topic"]].append(r.get("rating", "").lower())
        for t in sorted(topic_results):
            print(f"  {t}: {', '.join(topic_results[t])}")

    print()


def cmd_stats() -> None:
    tracker = _parse_tracker()
    summary = tracker.get("summary", {})
    phase_num, phase_name = _get_phase()
    days_left = _days_until_exam()
    drilled = _topics_with_drills()

    _print_panel(f"Stats | Phase {phase_num} ({phase_name}) | {days_left} days to exam")
    print(
        f"  Total: {summary.get('total', 0)} questions across {summary.get('sessions', 0)} sessions"
    )
    print(
        f"  Rate: {summary.get('rate', 0)}%  "
        f"({summary.get('correct', 0)}/{summary.get('total', 0)})"
    )
    print(f"  Drill coverage: {len(drilled)} topics have Definition Drills entries")
    print()

    topics = tracker["topics"]
    weak = sorted(
        [(t, i) for t, i in topics.items() if i.get("rate", 0.0) < 0.60],
        key=lambda x: x[1].get("rate", 0.0),
    )
    if weak:
        print(_bold("Weak topics (<60%):"))
        for t, i in weak:
            tag = _cyan("[drill]") if t in drilled else _dim("[no drill]")
            print(
                f"  {t}: {i.get('rate', 0.0) * 100:.0f}% "
                f"({i.get('correct', 0)}/{i.get('attempts', 0)}) {tag}"
            )
        print()

    state = _load_state()
    confident_miss_counts: dict[str, int] = defaultdict(int)
    for r in state["review_log"]:
        rl = r.get("rating", "").lower()
        if rl in ("again", "miss") and r.get("confidence") == "C":
            confident_miss_counts[r["topic"]] += 1

    if confident_miss_counts:
        total_c_misses = sum(confident_miss_counts.values())
        top_offenders = sorted(confident_miss_counts.items(), key=lambda x: (-x[1], x[0]))
        print(_bold("Confident misses (all time):"))
        print(f"  Total: {total_c_misses}")
        offenders_str = ", ".join(f"{t} ({c} times)" for t, c in top_offenders[:5])
        print(f"  Top offenders: {offenders_str}")
        print()


def cmd_topics() -> None:
    state = _load_state()
    tracker = _parse_tracker()
    drilled = _topics_with_drills()

    topics = [
        (t, tracker["topics"].get(t, {"attempts": 0, "correct": 0, "rate": 0.0}))
        for t in state["cards"]
    ]
    topics.sort(key=lambda x: x[1].get("rate", 0.0))

    print()
    print(_bold(f"All topics ({len(topics)}):"))
    print()
    for t, i in topics:
        att = i.get("attempts", 0)
        rate_str = f"{i.get('rate', 0.0) * 100:.0f}%" if att > 0 else "[new]"
        tag = f" {_cyan('[drill]')}" if t in drilled else ""
        line = f"{t}: {rate_str} ({i.get('correct', 0)}/{att}){tag}"
        if att == 0:
            print(f"  {_dim(line)}")
        elif i.get("rate", 0.0) < 0.60:
            print(f"  {_red(line)}")
        elif i.get("rate", 0.0) < 0.70:
            print(f"  {_yellow(line)}")
        else:
            print(f"  {_green(line)}")
    print()


def cmd_due() -> None:
    state = _load_state()
    now = _now_hkt()

    due_topics = []
    for topic, card in state["cards"].items():
        due_dt = _card_due_hkt(card)
        if due_dt is not None:
            if due_dt <= now:
                overdue = (now - due_dt).days
                due_topics.append((topic, overdue, _state_name(card.get("state", 0))))
        else:
            due_topics.append((topic, 999, "new"))

    due_topics.sort(key=lambda x: -x[1])

    print()
    print(_bold(f"{len(due_topics)} topics due:"))
    print()
    for t, overdue, st in due_topics:
        line = f"{t}: overdue {overdue}d ({st})"
        if overdue > 0:
            print(f"  {_red(line)}")
        else:
            print(f"  {_yellow(line)}")
    print()


def cmd_coverage() -> None:
    tracker = _parse_tracker()
    topics = tracker["topics"]
    days_left = _days_until_exam()

    # Module rollup
    mod_correct: dict[str, int] = defaultdict(int)
    mod_attempts: dict[str, int] = defaultdict(int)
    for syllabus_topic in GARP_RAI_SYLLABUS:
        pfx = syllabus_topic.split("-")[0]
        info = topics.get(syllabus_topic, {})
        mod_correct[pfx] += info.get("correct", 0)
        mod_attempts[pfx] += info.get("attempts", 0)

    fragile = sorted(
        [
            (t, i)
            for t, i in topics.items()
            if i.get("attempts", 0) > 0
            and i.get("attempts", 0) <= 5
            and i.get("rate", 0.0) >= 0.80
        ],
        key=lambda x: x[0],
    )
    low_sample = sorted(
        [(t, i) for t, i in topics.items() if i.get("attempts", 0) < 3],
        key=lambda x: x[1].get("attempts", 0),
    )

    _print_panel(f"Coverage | {len(topics)} topics | {days_left} days to exam")
    print()
    print(f"  {_bold('Module rollup (weighted accuracy):')}")
    for pfx in sorted(mod_attempts):
        attempts = mod_attempts[pfx]
        correct = mod_correct[pfx]
        rate = correct / attempts if attempts else 0.0
        pct = f"{rate * 100:3.0f}%"
        colored_pct = _red(pct) if rate < 0.70 else _yellow(pct) if rate < 0.80 else _green(pct)
        print(f"    {pfx}   {colored_pct}  ({correct} / {attempts})")

    print()
    if fragile:
        print(
            f"  {_yellow(_bold(f'FRAGILE ({len(fragile)}):'))} "
            f"{_dim('accuracy >=80% but <=5 questions')}"
        )
        for topic, info in fragile:
            print(
                f"    {topic:<35} {info.get('rate', 0.0) * 100:3.0f}%  "
                f"({info.get('correct', 0)}/{info.get('attempts', 0)})"
            )

    print()
    if low_sample:
        print(
            f"  {_red(_bold(f'LOW SAMPLE ({len(low_sample)}):'))} "
            f"{_dim('<3 questions -- effectively untested')}"
        )
        for topic, info in low_sample:
            att = info.get("attempts", 0)
            acc = f"{info.get('rate', 0.0) * 100:.0f}%" if att > 0 else "\u2014"
            print(f"    {topic:<35} {att} attempts  ({acc})")

    if not fragile and not low_sample:
        print(f"  {_green('All topics adequately sampled.')}")


def cmd_reconcile() -> None:
    path = _tracker_path()
    if not path.exists():
        print(_red("Tracker not found"))
        return

    tracker = _parse_tracker()
    topics = tracker["topics"]

    if len(topics) < 10:
        print(
            f"  {_red(f'Abort: only {len(topics)} topics parsed (expected ~34). Check tracker format.')}"
        )
        return

    actual_total = sum(i.get("attempts", 0) for i in topics.values())
    actual_correct = sum(i.get("correct", 0) for i in topics.values())
    actual_rate = round(actual_correct / actual_total * 100) if actual_total else 0

    old_total = tracker["summary"].get("total", 0)
    old_correct = tracker["summary"].get("correct", 0)
    old_rate = tracker["summary"].get("rate", 0)

    if old_total == actual_total and old_correct == actual_correct:
        print()
        print(f"  {_green('Summary is in sync. No changes needed.')}")
        print()
        return

    text = path.read_text(encoding="utf-8")
    m_total = re.search(r"(\|\s*Total Questions\s*\|\s*)(\d+)(\s*\|)", text)
    re.search(r"(\|\s*Correct\s*\|\s*)(\d+)(\s*\|)", text)
    re.search(r"(\|\s*Rate\s*\|\s*)(\d+)(%\s*\|)", text)

    if m_total:
        text = text[: m_total.start(2)] + str(actual_total) + text[m_total.end(2) :]
    m_correct2 = re.search(r"(\|\s*Correct\s*\|\s*)(\d+)(\s*\|)", text)
    if m_correct2:
        text = text[: m_correct2.start(2)] + str(actual_correct) + text[m_correct2.end(2) :]
    m_rate2 = re.search(r"(\|\s*Rate\s*\|\s*)(\d+)(%\s*\|)", text)
    if m_rate2:
        text = text[: m_rate2.start(2)] + str(actual_rate) + text[m_rate2.end(2) :]

    _atomic_write(path, text)

    print()
    print(f"  {_yellow('Reconciled:')}")
    print(f"    Total: {old_total} -> {actual_total}")
    print(f"    Correct: {old_correct} -> {actual_correct}")
    print(f"    Rate: {old_rate}% -> {actual_rate}%")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _cli() -> None:
    args = sys.argv[1:]

    if not args:
        _print_help()
        return

    cmd = args[0].lower()

    if cmd == "session":
        n = int(args[1]) if len(args) > 1 else None
        cmd_session(n)

    elif cmd == "record":
        if len(args) < 3:
            print(
                _red("Usage: melete record TOPIC RATING [-c C|U|G] [-n] [-N NOTE]"),
                file=sys.stderr,
            )
            sys.exit(1)
        topic = args[1]
        rating = args[2]
        confidence = None
        dry_run = False
        note = None
        i = 3
        while i < len(args):
            a = args[i]
            if a in ("-c", "--confidence") and i + 1 < len(args):
                confidence = args[i + 1]
                i += 2
            elif a in ("-n", "--dry-run"):
                dry_run = True
                i += 1
            elif a in ("-N", "--note") and i + 1 < len(args):
                note = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_record(topic, rating, confidence, dry_run, note)

    elif cmd == "void":
        if len(args) < 2:
            print(_red("Usage: melete void TOPIC [-n]"), file=sys.stderr)
            sys.exit(1)
        topic = args[1]
        dry_run = "-n" in args or "--dry-run" in args
        cmd_void(topic, dry_run)

    elif cmd == "end":
        cmd_end()

    elif cmd == "today":
        cmd_today()

    elif cmd == "stats":
        cmd_stats()

    elif cmd == "topics":
        cmd_topics()

    elif cmd == "due":
        cmd_due()

    elif cmd == "coverage":
        cmd_coverage()

    elif cmd == "reconcile":
        cmd_reconcile()

    else:
        print(_red(f"Unknown command: {cmd}"))
        _print_help()
        sys.exit(1)


def _print_help() -> None:
    print()
    print(_bold("melete -- GARP RAI spaced repetition"))
    print()
    print(f"  {_cyan('session')} [N]")
    print(f"  {_cyan('record')} TOPIC RATING [-c C|U|G] [-N NOTE]")
    print(f"  {_cyan('void')} TOPIC")
    print(f"  {_cyan('end')}")
    print(f"  {_cyan('today')}")
    print(f"  {_cyan('stats')}")
    print(f"  {_cyan('topics')}")
    print(f"  {_cyan('due')}")
    print(f"  {_cyan('coverage')}")
    print(f"  {_cyan('reconcile')}")
    print()


if __name__ == "__main__":
    _cli()
