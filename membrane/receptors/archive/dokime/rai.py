#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["fsrs", "rich"]
# ///
"""
GARP RAI Spaced Repetition CLI

    rai session [N]      Generate a session plan
    rai record TOPIC R   Record a review (again/hard/good/easy)
    rai end              Increment session count after last question
    rai today            Today's activity and quota status
    rai stats            Overall stats and weak topics
    rai topics           All topics with accuracy and drill coverage
    rai due              Topics due for review
    rai reconcile        Fix summary counter drift from actual data
"""

import contextlib
import json
import os
import re
import sys
import tempfile
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

from fsrs import Card, Rating, Scheduler
from rich import box
from rich.console import Console
from rich.panel import Panel

# --- Config ---
TRACKER_PATH = Path.home() / "notes" / "GARP RAI Quiz Tracker.md"
STATE_PATH = Path.home() / "notes" / ".garp-fsrs-state.json"
EXAM_DATE = datetime(2026, 4, 4, tzinfo=timezone(timedelta(hours=8)))
HKT = timezone(timedelta(hours=8))

MODULE_FILES = {
    str(i): Path.home() / "notes" / f"GARP RAI Module {i} - Raw Content.md" for i in range(1, 6)
}

RATING_MAP = {
    "again": Rating.Again,
    "miss": Rating.Again,
    "hard": Rating.Hard,
    "guess": Rating.Hard,
    "good": Rating.Good,
    "ok": Rating.Good,
    "easy": Rating.Easy,
    "confident": Rating.Easy,
}

MODE_THRESHOLDS = [(0.60, "drill"), (0.70, "free-recall"), (1.01, "MCQ")]

# Topic → search terms for finding source material in module files
SEARCH_TERMS = {
    "M1-classical-ai": ["Classical AI", "GOFAI", "Limits of Classical"],
    "M1-ml-types": ["Types of Machine Learning", "Four Types"],
    "M1-ai-risks": ["Risks of Inscrutability", "Risks of Over-Reliance"],
    "M2-intro-tools": ["Machine Learning, Classical Statistics"],
    "M2-data-prep": ["Data Scaling", "normalization", "standardization"],
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

GARP_RAI_SYLLABUS = sorted(
    [
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
)

console = Console()
scheduler = Scheduler()


def atomic_write(path: Path, content: str):
    """Write to a temp file then rename — atomic on same filesystem."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def now_hkt() -> datetime:
    return datetime.now(HKT)


def today_hkt() -> date:
    return now_hkt().date()


def days_until_exam() -> int:
    return (EXAM_DATE - now_hkt()).days


def get_phase() -> tuple[int, str]:
    d = today_hkt()
    if d <= date(2026, 3, 13):
        return 1, "Cruise"
    elif d <= date(2026, 3, 28):
        return 2, "Ramp"
    else:
        return 3, "Peak"


def default_count() -> int:
    phase, _ = get_phase()
    return {1: 5, 2: 15, 3: 20}[phase]


def get_mode(rate: float) -> str:
    for threshold, label in MODE_THRESHOLDS:
        if rate < threshold:
            return label
    return "MCQ"


# --- State I/O ---


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text())
            cards = {}
            for t, cj in data.get("cards", {}).items():
                try:
                    cards[t] = Card.from_json(cj)
                except Exception:
                    console.print(f"[yellow]Warning: skipping corrupt card for {t}[/yellow]")
            data["cards"] = cards
            return data
        except json.JSONDecodeError:
            console.print("[red]Warning: corrupt state file, starting fresh[/red]")
    return {"cards": {}, "review_log": []}


def save_state(state: dict):
    # Prune review log to last 90 days
    cutoff = (now_hkt() - timedelta(days=90)).isoformat()
    log = [e for e in state.get("review_log", []) if e.get("date", "") >= cutoff]
    out = {
        "cards": {t: c.to_json() for t, c in state["cards"].items()},
        "review_log": log,
    }
    atomic_write(STATE_PATH, json.dumps(out, indent=2, default=str))


# --- Tracker Markdown ---


def parse_tracker() -> dict:
    if not TRACKER_PATH.exists():
        return {"summary": {}, "topics": {}, "recent_misses": []}

    text = TRACKER_PATH.read_text()

    # Topics
    topics = {}
    for m in re.finditer(
        r"^\|\s*(M\d-[\w-]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d—-]+%?)\s*\|",
        text,
        re.MULTILINE,
    ):
        rate_str = m.group(4)
        topics[m.group(1)] = {
            "attempts": int(m.group(2)),
            "correct": int(m.group(3)),
            "rate": 0.0 if rate_str in ("—", "-") else float(rate_str.rstrip("%")) / 100,
        }

    # Summary
    summary = {}
    sm = re.search(
        r"^\|\s*Total Questions\s*\|\s*(\d+)\s*\|.*?"
        r"^\|\s*Correct\s*\|\s*(\d+)\s*\|.*?"
        r"^\|\s*Rate\s*\|\s*(\d+)%\s*\|.*?"
        r"^\|\s*Sessions\s*\|\s*(\d+)\s*\|",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if sm:
        summary = {
            "total": int(sm.group(1)),
            "correct": int(sm.group(2)),
            "rate": int(sm.group(3)),
            "sessions": int(sm.group(4)),
        }

    # Recent misses
    recent_misses = []
    in_misses = False
    for line in text.split("\n"):
        if "## Recent Misses" in line:
            in_misses = True
            continue
        if in_misses and line.startswith("## "):
            break
        if in_misses:
            m = re.match(r"^\|\s*([\d-]+)\s*\|\s*(M\d-[\w-]+)\s*\|\s*(.+?)\s*\|", line)
            if m and "Date" not in m.group(1):
                recent_misses.append(
                    {
                        "date": m.group(1),
                        "topic": m.group(2),
                        "concept": m.group(3).strip(),
                    }
                )

    if not topics and TRACKER_PATH.exists():
        console.print(
            "[yellow]Warning: No topics parsed from tracker. Check markdown format.[/yellow]"
        )

    return {"summary": summary, "topics": topics, "recent_misses": recent_misses}


def update_tracker_record(topic: str, rating: Rating):
    if not TRACKER_PATH.exists():
        return

    text = TRACKER_PATH.read_text()
    is_correct = rating in (Rating.Good, Rating.Easy)

    # Summary counters
    m_total = re.search(r"(\|\s*Total Questions\s*\|\s*)(\d+)(\s*\|)", text)
    m_correct = re.search(r"(\|\s*Correct\s*\|\s*)(\d+)(\s*\|)", text)
    if m_total and m_correct:
        new_total = int(m_total.group(2)) + 1
        new_correct = int(m_correct.group(2)) + (1 if is_correct else 0)
        new_rate = round(new_correct / new_total * 100)
        text = re.sub(r"(\|\s*Total Questions\s*\|\s*)\d+(\s*\|)", rf"\g<1>{new_total}\2", text)
        text = re.sub(r"(\|\s*Correct\s*\|\s*)\d+(\s*\|)", rf"\g<1>{new_correct}\2", text)
        text = re.sub(r"(\|\s*Rate\s*\|\s*)\d+(%\s*\|)", rf"\g<1>{new_rate}\2", text)

    # Topic row
    topic_row = re.compile(
        rf"(\|\s*{re.escape(topic)}\s*\|\s*)(\d+)(\s*\|\s*)(\d+)(\s*\|\s*)([\d—-]+%?)(\s*\|)"
    )
    m_topic = topic_row.search(text)
    if m_topic:
        na = int(m_topic.group(2)) + 1
        nc = int(m_topic.group(4)) + (1 if is_correct else 0)
        text = topic_row.sub(rf"\g<1>{na}\g<3>{nc}\g<5>{round(nc / na * 100)}%\g<7>", text)

    # History append
    result_str = {
        Rating.Again: "MISS",
        Rating.Hard: "OK-GUESS",
        Rating.Good: "OK",
        Rating.Easy: "OK",
    }[rating]
    history_line = (
        f"| {now_hkt().strftime('%Y-%m-%d')} | {topic} | {result_str} | (recorded via rai) |"
    )

    lines = text.split("\n")
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
        # History section exists but has no table rows yet — append after header
        for i, line in enumerate(lines):
            if "## History" in line:
                lines.insert(i + 1, history_line)
                break

    atomic_write(TRACKER_PATH, "\n".join(lines))


# --- Drill Coverage ---

DRILLS_PATH = Path.home() / "notes" / "GARP RAI Definition Drills.md"


def topics_with_drills() -> set[str]:
    """Scan Definition Drills headers for topic tags like (M2-data-prep, ...)."""
    if not DRILLS_PATH.exists():
        return set()
    found = set()
    for line in DRILLS_PATH.read_text().split("\n"):
        if line.startswith("## "):
            m = re.search(r"\((M\d-[\w-]+)", line)
            if m:
                found.add(m.group(1))
    return found


# --- Source Location ---


def find_source_location(topic: str) -> str | None:
    module_file = MODULE_FILES.get(topic[1])
    if not module_file or not module_file.exists():
        return None

    terms = SEARCH_TERMS.get(topic)
    if not terms:
        suffix = topic.split("-", 1)[1] if "-" in topic else topic
        terms = [w.capitalize() for w in suffix.split("-") if len(w) > 2]

    file_lines = module_file.read_text().split("\n")

    # Find ## headers matching terms (deduplicated)
    seen, hits = set(), []
    for i, line in enumerate(file_lines):
        if line.startswith("##"):
            for term in terms:
                if term.lower() in line.lower():
                    h = line.strip()
                    if h not in seen:
                        seen.add(h)
                        hits.append(i)
                    break

    # Fallback: content search, skip TOC entries
    if not hits:
        for i, line in enumerate(file_lines):
            for term in terms:
                if term.lower() in line.lower():
                    if any(
                        len(file_lines[j]) > 80 for j in range(i + 1, min(i + 6, len(file_lines)))
                    ):
                        hits.append(max(0, i - 2))
                    break
            if len(hits) >= 2:
                break

    if not hits:
        return None

    start = hits[0]
    end = min(start + 80, len(file_lines))
    for i in range(start + 4, end):
        if file_lines[i].startswith("## "):
            end = i
            break

    return f"{module_file}:{start + 1}-{end}"


# --- Commands ---


def resolve_topic(topic: str, tracker: dict) -> str | None:
    if topic in tracker["topics"]:
        return topic
    matches = [t for t in tracker["topics"] if topic.lower() in t.lower()]
    if len(matches) == 1:
        console.print(f"[dim]Matched: {matches[0]}[/dim]")
        return matches[0]
    if matches:
        console.print("[yellow]Ambiguous:[/yellow]")
        for m in matches:
            console.print(f"  • {m}")
    else:
        console.print(f"[red]Unknown topic: {topic}[/red]")
    return None


def cmd_session(count: int | None = None):
    state = load_state()
    tracker = parse_tracker()
    now = now_hkt()
    days_left = days_until_exam()
    phase_num, phase_name = get_phase()
    n = count or default_count()

    # Same-day cooldown
    today_str = today_hkt().isoformat()
    today_reviews = [
        e for e in state.get("review_log", []) if e.get("date", "").startswith(today_str)
    ]
    tested_today = {e["topic"] for e in today_reviews}

    # Quota banner
    q_per_session = get_daily_quota()
    if len(today_reviews) >= q_per_session:
        console.print()
        console.print(
            f"  [green]✓ Already done {len(today_reviews)} questions today ({len(tested_today)} topics). Quota met.[/green]"
        )
        console.print("  [dim]Continuing with unreviewed topics...[/dim]")
        console.print()

    # Due topics (excluding tested today)
    due = []
    for topic, info in tracker["topics"].items():
        if topic in tested_today:
            continue
        card = state["cards"].get(topic)
        if card is None:
            due.append((topic, info, 999))
            continue
        due_dt = card.due if card.due.tzinfo else card.due.replace(tzinfo=UTC)
        if due_dt.astimezone(HKT) <= now:
            due.append((topic, info, (now - due_dt.astimezone(HKT)).days))

    due.sort(key=lambda x: (-x[2], x[1]["rate"]))

    # Composition: weak <60%, rest consolidation
    weak = [(t, i, o) for t, i, o in due if i["rate"] < 0.60]
    strong = [(t, i, o) for t, i, o in due if i["rate"] >= 0.60]
    max_weak = min(len(weak), max(1, int(n * 0.6)))
    selected = weak[:max_weak] + strong[: n - max_weak]
    if len(selected) < n:
        used = {s[0] for s in selected}
        selected += [x for x in due if x[0] not in used][: n - len(selected)]
    selected = selected[:n]

    # Interleave: no more than 2 consecutive topics from the same module
    interleaved = []
    remaining = list(selected)
    while remaining:
        if len(interleaved) >= 2:
            last_mod = interleaved[-1][0][:2]
            prev_mod = interleaved[-2][0][:2]
            if last_mod == prev_mod:
                # Find first topic from a different module
                for j, item in enumerate(remaining):
                    if item[0][:2] != last_mod:
                        interleaved.append(remaining.pop(j))
                        break
                else:
                    interleaved.append(remaining.pop(0))
                continue
        interleaved.append(remaining.pop(0))
    selected = interleaved

    # Output
    summary = tracker.get("summary", {})
    console.print()
    console.print(
        Panel(
            f"[bold]Session Plan[/bold]  |  Phase {phase_num} ({phase_name})  |  {days_left} days to exam",
            box=box.ROUNDED,
        )
    )
    console.print(
        f"  Overall: {summary.get('correct', 0)}/{summary.get('total', 0)} ({summary.get('rate', 0)}%)  |  {summary.get('sessions', 0)} sessions"
    )

    m12 = sum(1 for t, _, _ in selected if t.startswith(("M1-", "M2-")))
    if selected and m12 / len(selected) < 0.30:
        console.print(f"  [yellow]M1/M2 quota: {m12}/{len(selected)} (target ≥30%)[/yellow]")
    console.print()

    misses = tracker.get("recent_misses", [])
    if misses:
        console.print("[bold]Recent misses:[/bold]")
        for m in misses[-5:]:
            console.print(f"  - {m['concept']} ({m['date']})")
        console.print()

    drilled = topics_with_drills()
    console.print(f"[bold]Questions ({len(selected)}):[/bold]")
    console.print()
    colors = {"drill": "red", "free-recall": "yellow", "MCQ": "green"}
    for i, (topic, info, overdue) in enumerate(selected, 1):
        mode = get_mode(info["rate"])
        source = find_source_location(topic) or "not found"
        c = colors.get(mode, "white")
        drill_tag = " [cyan][drill][/cyan]" if topic in drilled else ""
        console.print(
            f"  Q{i}: [{c} bold]{topic}[/{c} bold]  |  {mode} ({info['rate']:.0%})  |  overdue {overdue}d{drill_tag}"
        )
        console.print(f"      [dim]{source}[/dim]")
    console.print()


def cmd_record(topic: str, rating_str: str):
    rating = RATING_MAP.get(rating_str.lower())
    if rating is None:
        console.print(f"[red]Unknown rating: {rating_str}. Valid: {', '.join(RATING_MAP)}[/red]")
        return

    state = load_state()
    tracker = parse_tracker()

    topic = resolve_topic(topic, tracker)
    if not topic:
        return

    # Acquisition cap: enforce at CLI level (hard gate, not just skill instructions)
    # Topics <60% accuracy: cap good/easy to hard to prevent lucky-guess promotion
    topic_info = tracker["topics"].get(topic, {})
    topic_rate = topic_info.get("rate", 0.0)
    if topic_rate < 0.60 and rating in (Rating.Good, Rating.Easy):
        console.print(
            f"  [yellow]Acquisition cap: {topic} at {topic_rate:.0%} — capping {rating_str} → hard[/yellow]"
        )
        rating = Rating.Hard
        rating_str = "hard"

    card = state["cards"].get(topic, Card())
    card, _ = scheduler.review_card(card, rating)

    state["cards"][topic] = card
    state.setdefault("review_log", []).append(
        {
            "topic": topic,
            "rating": rating_str.lower(),
            "date": now_hkt().isoformat(),
        }
    )
    save_state(state)
    update_tracker_record(topic, rating)

    due_raw = card.due if card.due.tzinfo else card.due.replace(tzinfo=UTC)
    due_date = due_raw.astimezone(HKT)
    display = {
        Rating.Again: "[red]Again (miss)[/red]",
        Rating.Hard: "[yellow]Hard (guess)[/yellow]",
        Rating.Good: "[green]Good[/green]",
        Rating.Easy: "[bright_green]Easy[/bright_green]",
    }[rating]

    console.print()
    console.print(f"  {display}  [bold]{topic}[/bold]")
    console.print(
        f"  Next: [cyan]{due_date.strftime('%b %d')}[/cyan] ({(due_date - now_hkt()).days}d)  |  {card.state.name}"
    )
    console.print()


def cmd_stats():
    tracker = parse_tracker()
    summary = tracker.get("summary", {})
    phase_num, phase_name = get_phase()
    days_left = days_until_exam()
    drilled = topics_with_drills()

    console.print()
    console.print(
        Panel(
            f"[bold]Stats[/bold]  |  Phase {phase_num} ({phase_name})  |  {days_left} days to exam",
            box=box.ROUNDED,
        )
    )
    console.print(
        f"  Total: {summary.get('total', 0)} questions across {summary.get('sessions', 0)} sessions"
    )
    console.print(
        f"  Rate: {summary.get('rate', 0)}%  ({summary.get('correct', 0)}/{summary.get('total', 0)})"
    )
    console.print(f"  Drill coverage: {len(drilled)} topics have Definition Drills entries")
    console.print()

    # Weak topics
    weak = [(t, i) for t, i in tracker["topics"].items() if i["rate"] < 0.60]
    weak.sort(key=lambda x: x[1]["rate"])
    if weak:
        console.print("[bold]Weak topics (<60%):[/bold]")
        for t, i in weak:
            tag = " [cyan][drill][/cyan]" if t in drilled else " [dim][no drill][/dim]"
            console.print(f"  {t}: {i['rate']:.0%} ({i['correct']}/{i['attempts']}){tag}")
        console.print()


def cmd_topics():
    tracker = parse_tracker()
    drilled = topics_with_drills()
    topics = sorted(tracker["topics"].items(), key=lambda x: x[1]["rate"])

    console.print()
    console.print("[bold]All topics:[/bold]")
    console.print()
    for t, i in topics:
        rate_str = f"{i['rate']:.0%}" if i["attempts"] > 0 else "—"
        tag = " [cyan][drill][/cyan]" if t in drilled else ""
        c = "red" if i["rate"] < 0.60 else "yellow" if i["rate"] < 0.70 else "green"
        console.print(f"  [{c}]{t}[/{c}]: {rate_str} ({i['correct']}/{i['attempts']}){tag}")
    console.print()


def cmd_due():
    state = load_state()
    tracker = parse_tracker()
    now = now_hkt()

    due_topics = []
    for topic in tracker["topics"]:
        card = state["cards"].get(topic)
        if card is None:
            due_topics.append((topic, 999, "new"))
        else:
            due_dt = card.due if card.due.tzinfo else card.due.replace(tzinfo=UTC)
            if due_dt.astimezone(HKT) > now:
                continue
            days = (now - due_dt.astimezone(HKT)).days
            due_topics.append((topic, days, card.state.name))

    due_topics.sort(key=lambda x: -x[1])

    console.print()
    console.print(f"[bold]{len(due_topics)} topics due:[/bold]")
    console.print()
    for t, overdue, st in due_topics:
        console.print(f"  {t}: overdue {overdue}d ({st})")
    console.print()


def get_today_reviews(state: dict) -> list[dict]:
    """Get all review log entries from today (HKT)."""
    today_str = today_hkt().isoformat()
    return [e for e in state.get("review_log", []) if e.get("date", "").startswith(today_str)]


def get_daily_quota() -> int:
    """Return questions-per-session for current phase."""
    phase, _ = get_phase()
    return {1: 5, 2: 15, 3: 20}[phase]


def cmd_today():
    """Show today's quiz activity and whether daily quota is met."""
    state = load_state()
    parse_tracker()
    phase_num, phase_name = get_phase()
    today_reviews = get_today_reviews(state)
    q_per_session = get_daily_quota()

    # Count today's questions and distinct topics
    topics_today = set()
    correct_today = 0
    miss_today = 0
    for r in today_reviews:
        topics_today.add(r["topic"])
        if r["rating"] in ("good", "ok", "easy", "confident"):
            correct_today += 1
        elif r["rating"] in ("again", "miss"):
            miss_today += 1

    total_today = len(today_reviews)

    # Estimate sessions: bursts separated by >30 min
    sessions_today = 0
    if today_reviews:
        sessions_today = 1
        sorted_reviews = sorted(today_reviews, key=lambda x: x["date"])
        for i in range(1, len(sorted_reviews)):
            try:
                prev = datetime.fromisoformat(sorted_reviews[i - 1]["date"])
                curr = datetime.fromisoformat(sorted_reviews[i]["date"])
                if (curr - prev).total_seconds() > 1800:
                    sessions_today += 1
            except (ValueError, TypeError):
                continue

    # Quota check: at least one session's worth of questions done today
    quota_met = total_today >= q_per_session

    console.print()
    console.print(
        Panel(
            f"[bold]Today[/bold]  |  Phase {phase_num} ({phase_name})  |  {days_until_exam()} days to exam",
            box=box.ROUNDED,
        )
    )

    if total_today == 0:
        console.print("  [dim]No reviews today.[/dim]")
    else:
        rate = round(correct_today / total_today * 100) if total_today else 0
        console.print(
            f"  Questions: {total_today}  |  Correct: {correct_today}  |  Missed: {miss_today}  |  Rate: {rate}%"
        )
        console.print(f"  Sessions: ~{sessions_today}  |  Topics: {len(topics_today)}")

        if quota_met:
            console.print(f"  [green]✓ Daily quota met ({q_per_session}+ questions)[/green]")
        else:
            remaining = q_per_session - total_today
            console.print(
                f"  [yellow]◯ {remaining} more questions to meet daily quota ({q_per_session})[/yellow]"
            )

    # Show today's topic breakdown
    if today_reviews:
        console.print()
        console.print("[bold]Topics reviewed today:[/bold]")
        topic_results: dict[str, list[str]] = {}
        for r in today_reviews:
            topic_results.setdefault(r["topic"], []).append(r["rating"])
        for t, ratings in sorted(topic_results.items()):
            rating_str = ", ".join(ratings)
            console.print(f"  {t}: {rating_str}")

    console.print()


def cmd_end_session():
    """Increment session count in tracker. Run after last question."""
    if not TRACKER_PATH.exists():
        console.print("[red]Tracker not found[/red]")
        return

    text = TRACKER_PATH.read_text()
    m = re.search(r"(\|\s*Sessions\s*\|\s*)(\d+)(\s*\|)", text)
    if not m:
        console.print("[red]Sessions row not found in tracker[/red]")
        return

    old = int(m.group(2))
    new = old + 1
    text = re.sub(r"(\|\s*Sessions\s*\|\s*)\d+(\s*\|)", rf"\g<1>{new}\2", text)
    atomic_write(TRACKER_PATH, text)

    console.print()
    console.print(f"  Session [bold]{new}[/bold] recorded (was {old})")
    console.print()


def cmd_reconcile():
    """Fix summary counter drift by recomputing from topic rows (source of truth)."""
    if not TRACKER_PATH.exists():
        console.print("[red]Tracker not found[/red]")
        return

    tracker = parse_tracker()
    topics = tracker["topics"]

    if len(topics) < 10:
        console.print(
            f"  [red]Abort: only {len(topics)} topics parsed (expected ~34). Check tracker format.[/red]"
        )
        return

    # Recompute from topic rows
    actual_total = sum(t["attempts"] for t in topics.values())
    actual_correct = sum(t["correct"] for t in topics.values())
    actual_rate = round(actual_correct / actual_total * 100) if actual_total else 0

    summary = tracker.get("summary", {})
    old_total = summary.get("total", 0)
    old_correct = summary.get("correct", 0)

    if old_total == actual_total and old_correct == actual_correct:
        console.print()
        console.print("  [green]Summary is in sync. No changes needed.[/green]")
        console.print()
        return

    text = TRACKER_PATH.read_text()
    text = re.sub(r"(\|\s*Total Questions\s*\|\s*)\d+(\s*\|)", rf"\g<1>{actual_total}\2", text)
    text = re.sub(r"(\|\s*Correct\s*\|\s*)\d+(\s*\|)", rf"\g<1>{actual_correct}\2", text)
    text = re.sub(r"(\|\s*Rate\s*\|\s*)\d+(%\s*\|)", rf"\g<1>{actual_rate}\2", text)
    atomic_write(TRACKER_PATH, text)

    console.print()
    console.print("  [yellow]Reconciled:[/yellow]")
    console.print(f"    Total: {old_total} → {actual_total}")
    console.print(f"    Correct: {old_correct} → {actual_correct}")
    console.print(f"    Rate: {summary.get('rate', 0)}% → {actual_rate}%")
    console.print()


def cmd_coverage():
    """Compare tracked topics against the GARP RAI syllabus."""
    tracker = parse_tracker()
    tracked = tracker["topics"]

    tracked_set = set(tracked.keys())
    syllabus_set = set(GARP_RAI_SYLLABUS)

    missing = sorted(syllabus_set - tracked_set)
    never_attempted = sorted(t for t, i in tracked.items() if i["attempts"] == 0)
    low_coverage = sorted(
        (t for t, i in tracked.items() if i["attempts"] > 0 and i["attempts"] < 3),
        key=lambda x: tracked[x]["attempts"],
    )

    tracked_in_syllabus = tracked_set & syllabus_set
    coverage_pct = (
        len(tracked_in_syllabus) / len(GARP_RAI_SYLLABUS) * 100 if GARP_RAI_SYLLABUS else 0
    )

    console.print()
    console.print(
        Panel(
            f"[bold]Coverage Report[/bold]  |  {len(GARP_RAI_SYLLABUS)} syllabus topics",
            box=box.ROUNDED,
        )
    )
    console.print(
        f"  Tracked: {len(tracked_in_syllabus)}/{len(GARP_RAI_SYLLABUS)} ({coverage_pct:.0f}%)"
    )

    if missing:
        console.print()
        console.print(
            f"[bold red]MISSING ({len(missing)}):[/bold red] [dim]in syllabus but not in tracker[/dim]"
        )
        for t in missing:
            console.print(f"  {t}")

    if never_attempted:
        console.print()
        console.print(
            f"[bold yellow]NEVER ATTEMPTED ({len(never_attempted)}):[/bold yellow] [dim]in tracker but 0 attempts[/dim]"
        )
        for t in never_attempted:
            console.print(f"  {t}")

    if low_coverage:
        console.print()
        console.print(
            f"[bold cyan]LOW COVERAGE ({len(low_coverage)}):[/bold cyan] [dim]<3 attempts[/dim]"
        )
        for t in low_coverage:
            console.print(f"  {t}: {tracked[t]['attempts']} attempts ({tracked[t]['rate']:.0%})")

    if not missing and not never_attempted and not low_coverage:
        console.print()
        console.print("  [green]All syllabus topics covered with adequate attempts.[/green]")

    console.print()


# --- Main ---

HELP = """
[bold]rai[/bold] — GARP RAI spaced repetition

  [cyan]session[/cyan] [N]           Session plan (N questions, default: phase-based)
  [cyan]record[/cyan] TOPIC RATING   Record result (again/hard/good/easy)
  [cyan]end[/cyan]                   Increment session count (run after last question)
  [cyan]today[/cyan]                 Today's activity and quota status
  [cyan]stats[/cyan]                 Overall stats and weak topics
  [cyan]topics[/cyan]                All topics with accuracy and drill coverage
  [cyan]due[/cyan]                   Topics due for review
  [cyan]coverage[/cyan]              Compare tracked topics against syllabus
  [cyan]reconcile[/cyan]             Fix summary counter drift from actual data

[bold]Examples:[/bold]
  rai session
  rai session 10
  rai record fairness miss
  rai record M2-data-prep good
  rai today
  rai coverage
"""


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        console.print(HELP)
        return

    cmd = args[0].lower()
    if cmd == "session":
        n = None
        if len(args) > 1:
            try:
                n = int(args[1])
                if n < 1:
                    console.print("[red]Session count must be positive[/red]")
                    return
            except ValueError:
                console.print(f"[red]Invalid count: {args[1]}[/red]")
                return
        cmd_session(n)
    elif cmd == "record":
        if len(args) < 3:
            console.print("[red]Usage: rai record TOPIC RATING[/red]")
            return
        cmd_record(args[1], args[2])
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "topics":
        cmd_topics()
    elif cmd == "due":
        cmd_due()
    elif cmd == "end":
        cmd_end_session()
    elif cmd == "today":
        cmd_today()
    elif cmd == "reconcile":
        cmd_reconcile()
    elif cmd == "coverage":
        cmd_coverage()
    else:
        console.print(f"[red]Unknown: {cmd}[/red]")
        console.print(HELP)


if __name__ == "__main__":
    main()
