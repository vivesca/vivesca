"""quorum — multi-model deliberation engine.

Quorum sensing: bacteria coordinate behavior by accumulating signal molecules
until a threshold triggers collective action. Here, frontier LLMs accumulate
perspectives until a judge synthesizes a recommendation.

Four modes:
  quick    — parallel blind query + synthesis ($0, flat-rate CLIs)
  council  — blind → debate×2 → judge → critic ($0, flat-rate CLIs)
  redteam  — adversarial stress-test ($0, flat-rate CLIs)
  deep     — blind → debate×2 → cross-examine → judge → critic ($0, flat-rate CLIs)

Usage:
    from metabolon.organelles.quorum import deliberate
    result = deliberate("Should we use Kafka or Redis Streams?", mode="quick")
"""

import json
import textwrap
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from metabolon.locus import chromatin
from metabolon.symbiont import parallel_transduce, parallel_transduce_multi, transduce

if TYPE_CHECKING:
    from pathlib import Path

# ── panel configuration ──────────────────────────────────────

COUNCIL_DIR = chromatin / "Councils"

# Default panelists — all flat-rate, zero marginal cost
PANEL_QUICK = ["gemini", "claude", "goose"]
PANEL_COUNCIL = ["gemini", "claude", "codex", "goose", "droid"]
PANEL_REDTEAM = ["gemini", "claude", "goose", "droid", "goose-4.7"]
PANEL_DEEP = ["gemini", "claude", "codex", "goose", "droid", "goose-4.7", "droid-4.7"]

JUDGE_MODEL = "gemini"
CRITIC_MODEL = "claude"


# ── data types ───────────────────────────────────────────────


@dataclass
class Contribution:
    model: str
    content: str
    phase: str  # "blind", "debate", "attack", "defend", "judge", "critic"


@dataclass
class Deliberation:
    question: str
    mode: str
    contributions: list[Contribution] = field(default_factory=list)
    decision: str = ""
    dissents: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0
    persona: str = ""

    def summary(self) -> str:
        parts = [f"## Decision\n\n{self.decision}"]
        if self.dissents:
            parts.append("## Dissents\n\n" + "\n".join(f"- {d}" for d in self.dissents))
        parts.append(f"\n_Mode: {self.mode} | {self.elapsed_s:.1f}s_")
        return "\n\n".join(parts)

    def transcript(self) -> str:
        lines = [f"# Quorum: {self.question}\n"]
        if self.persona:
            lines.append(f"_Persona: {self.persona}_\n")
        for c in self.contributions:
            lines.append(f"## [{c.phase}] {c.model}\n\n{c.content}\n")
        lines.append(f"---\n\n{self.summary()}")
        return "\n".join(lines)

    def save(self, path: Path | None = None) -> Path:
        COUNCIL_DIR.mkdir(parents=True, exist_ok=True)
        slug = self.question[:60].replace(" ", "-").replace("/", "-").lower()
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        ts = time.strftime("%Y%m%d-%H%M%S")
        out = path or COUNCIL_DIR / f"{ts}-{slug}.md"
        out.write_text(self.transcript(), encoding="utf-8")
        return out


# ── prompt templates ─────────────────────────────────────────


def _blind_prompt(question: str, persona: str = "") -> str:
    ctx = f"\nContext about the questioner: {persona}" if persona else ""
    return textwrap.dedent(f"""\
        Answer this question independently. Be concise and direct.
        Give your honest assessment, not a hedged non-answer.{ctx}

        Question: {question}""")


def _debate_prompt(question: str, prior_answers: list[Contribution], model: str) -> str:
    others = "\n\n".join(f"**{c.model}**: {c.content}" for c in prior_answers if c.model != model)
    return textwrap.dedent(f"""\
        You previously answered this question blind. Now you can see other perspectives.
        Update, strengthen, or change your answer. Be specific about where you agree/disagree.

        Question: {question}

        Other answers:
        {others}""")


def _debate_round2_prompt(question: str, round1_debates: list[Contribution], model: str) -> str:
    others = "\n\n".join(f"**{c.model}**: {c.content}" for c in round1_debates if c.model != model)
    return textwrap.dedent(f"""\
        This is round 2. You've seen everyone's revised positions.
        Converge where possible. Sharpen remaining disagreements. Be specific.

        Question: {question}

        Round 1 revised positions:
        {others}""")


def _judge_prompt(question: str, contributions: list[Contribution], persona: str = "") -> str:
    answers = "\n\n".join(f"**{c.model}** [{c.phase}]: {c.content}" for c in contributions)
    ctx = f"\nThe questioner's context: {persona}" if persona else ""
    return textwrap.dedent(f"""\
        You are the judge in a multi-model deliberation. Synthesize a clear recommendation.

        Structure your response as:
        [DECISION] One clear recommendation (1-2 sentences)
        [REASONING] Key factors that drove the decision (bullet points)
        [DISSENT] Any strong counterarguments worth noting{ctx}

        Question: {question}

        Deliberation:
        {answers}""")


def _redteam_attack_prompt(question: str, position: str) -> str:
    return textwrap.dedent(f"""\
        You are a red team adversary. Find the strongest objections, failure modes,
        and blind spots in this position. Be ruthless but specific.

        Question: {question}
        Position being defended: {position}""")


def _redteam_defend_prompt(_question: str, position: str, attacks: list[Contribution]) -> str:
    attacks_text = "\n\n".join(f"**{a.model}**: {a.content}" for a in attacks)
    return textwrap.dedent(f"""\
        Your position is under attack. Address each objection directly.
        Concede where the attacks are valid. Strengthen where they're wrong.

        Original position: {position}

        Attacks:
        {attacks_text}""")


def _cross_examine_prompt(question: str, all_contributions: list[Contribution], model: str) -> str:
    answers = "\n\n".join(
        f"**{c.model}** [{c.phase}]: {c.content}" for c in all_contributions if c.model != model
    )
    return textwrap.dedent(f"""\
        Review all positions. Identify the single weakest argument.
        Attack it specifically. One paragraph, ruthless.

        Question: {question}

        All positions:
        {answers}""")


# ── parsing ──────────────────────────────────────────────────


def _parse_judge(text: str) -> tuple[str, list[str]]:
    """Extract decision and dissents from judge output."""
    decision = ""
    dissents: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[DECISION]"):
            decision = stripped[len("[DECISION]") :].strip()
        elif stripped.startswith("[DISSENT]"):
            d = stripped[len("[DISSENT]") :].strip()
            if d and d.lower() not in ("none", "n/a", "none noted"):
                dissents.append(d)
    if not decision:
        # Fallback: first non-empty line
        for line in text.splitlines():
            if line.strip():
                decision = line.strip()
                break
    return decision, dissents


# ── modes ────────────────────────────────────────────────────


def _mode_quick(question: str, panel: list[str], persona: str, timeout: int) -> Deliberation:
    """Parallel blind query + judge synthesis."""
    delib = Deliberation(question=question, mode="quick", persona=persona)

    prompt = _blind_prompt(question, persona)
    results = parallel_transduce(panel, prompt, timeout=timeout)
    for model, content in results:
        delib.contributions.append(Contribution(model=model, content=content, phase="blind"))

    judge_text = transduce(
        JUDGE_MODEL, _judge_prompt(question, delib.contributions, persona), timeout=timeout
    )
    delib.contributions.append(Contribution(model=JUDGE_MODEL, content=judge_text, phase="judge"))
    delib.decision, delib.dissents = _parse_judge(judge_text)
    return delib


def _mode_council(question: str, panel: list[str], persona: str, timeout: int) -> Deliberation:
    """Blind → debate → judge → critic."""
    delib = Deliberation(question=question, mode="council", persona=persona)

    # Phase 1: Blind
    prompt = _blind_prompt(question, persona)
    results = parallel_transduce(panel, prompt, timeout=timeout)
    blind = []
    for model, content in results:
        c = Contribution(model=model, content=content, phase="blind")
        delib.contributions.append(c)
        blind.append(c)

    # Phase 2: Debate round 1 — parallel (each model sees others' blind answers)
    debate_tasks = [(model, _debate_prompt(question, blind, model)) for model in panel]
    debate_results = parallel_transduce_multi(debate_tasks, timeout=timeout)
    round1_debates = []
    for model, content in debate_results:
        c = Contribution(model=model, content=content, phase="debate")
        delib.contributions.append(c)
        round1_debates.append(c)

    # Phase 2b: Debate round 2 — parallel (each model sees round 1 revised positions)
    round2_tasks = [
        (model, _debate_round2_prompt(question, round1_debates, model)) for model in panel
    ]
    round2_results = parallel_transduce_multi(round2_tasks, timeout=timeout)
    for model, content in round2_results:
        delib.contributions.append(Contribution(model=model, content=content, phase="debate-2"))

    # Phase 3: Judge
    judge_text = transduce(
        JUDGE_MODEL, _judge_prompt(question, delib.contributions, persona), timeout=timeout
    )
    delib.contributions.append(Contribution(model=JUDGE_MODEL, content=judge_text, phase="judge"))

    # Phase 4: Critic (different model challenges the judge)
    critic_prompt = textwrap.dedent(f"""\
        A judge has synthesized this decision from a multi-model deliberation.
        Challenge it: what did the judge miss? What's the strongest counterargument?
        Be brief and specific.

        Decision: {judge_text}
        Original question: {question}""")
    try:
        critic_text = transduce(CRITIC_MODEL, critic_prompt, timeout=timeout)
        delib.contributions.append(
            Contribution(model=CRITIC_MODEL, content=critic_text, phase="critic")
        )
    except Exception:
        pass

    delib.decision, delib.dissents = _parse_judge(judge_text)
    return delib


def _mode_redteam(question: str, panel: list[str], persona: str, timeout: int) -> Deliberation:
    """Adversarial stress-test: position → attack → defend."""
    delib = Deliberation(question=question, mode="redteam", persona=persona)

    # Phase 1: Initial position (single model)
    position_text = transduce(panel[0], _blind_prompt(question, persona), timeout=timeout)
    delib.contributions.append(Contribution(model=panel[0], content=position_text, phase="blind"))

    # Phase 2: Attack (other models)
    attackers = panel[1:]
    attack_results = parallel_transduce(
        attackers, _redteam_attack_prompt(question, position_text), timeout=timeout
    )
    attacks = []
    for model, content in attack_results:
        c = Contribution(model=model, content=content, phase="attack")
        delib.contributions.append(c)
        attacks.append(c)

    # Phase 3: Defend
    defend_text = transduce(
        panel[0],
        _redteam_defend_prompt(question, position_text, attacks),
        timeout=timeout,
    )
    delib.contributions.append(Contribution(model=panel[0], content=defend_text, phase="defend"))

    # Phase 4: Judge
    judge_text = transduce(
        JUDGE_MODEL, _judge_prompt(question, delib.contributions, persona), timeout=timeout
    )
    delib.contributions.append(Contribution(model=JUDGE_MODEL, content=judge_text, phase="judge"))
    delib.decision, delib.dissents = _parse_judge(judge_text)
    return delib


def _mode_deep(question: str, panel: list[str], persona: str, timeout: int) -> Deliberation:
    """Deep deliberation: blind → debate×2 → cross-examine → judge → critic."""
    delib = Deliberation(question=question, mode="deep", persona=persona)

    # Phase 1: Blind (parallel)
    prompt = _blind_prompt(question, persona)
    results = parallel_transduce(panel, prompt, timeout=timeout)
    blind = []
    for model, content in results:
        c = Contribution(model=model, content=content, phase="blind")
        delib.contributions.append(c)
        blind.append(c)

    # Phase 2: Debate round 1 (parallel)
    debate1_tasks = [(model, _debate_prompt(question, blind, model)) for model in panel]
    debate1_results = parallel_transduce_multi(debate1_tasks, timeout=timeout)
    round1_debates = []
    for model, content in debate1_results:
        c = Contribution(model=model, content=content, phase="debate")
        delib.contributions.append(c)
        round1_debates.append(c)

    # Phase 3: Debate round 2 (parallel)
    debate2_tasks = [
        (model, _debate_round2_prompt(question, round1_debates, model)) for model in panel
    ]
    debate2_results = parallel_transduce_multi(debate2_tasks, timeout=timeout)
    for model, content in debate2_results:
        delib.contributions.append(Contribution(model=model, content=content, phase="debate-2"))

    # Phase 4: Cross-examination (parallel — each model attacks weakest position)
    cross_tasks = [
        (model, _cross_examine_prompt(question, delib.contributions, model)) for model in panel
    ]
    cross_results = parallel_transduce_multi(cross_tasks, timeout=timeout)
    for model, content in cross_results:
        delib.contributions.append(
            Contribution(model=model, content=content, phase="cross-examine")
        )

    # Phase 5: Judge
    judge_text = transduce(
        JUDGE_MODEL, _judge_prompt(question, delib.contributions, persona), timeout=timeout
    )
    delib.contributions.append(Contribution(model=JUDGE_MODEL, content=judge_text, phase="judge"))

    # Phase 6: Critic
    critic_prompt = textwrap.dedent(f"""\
        A judge has synthesized this decision from a deep multi-model deliberation
        including two rounds of debate and cross-examination.
        Challenge it: what did the judge miss? What's the strongest counterargument?
        Be brief and specific.

        Decision: {judge_text}
        Original question: {question}""")
    try:
        critic_text = transduce(CRITIC_MODEL, critic_prompt, timeout=timeout)
        delib.contributions.append(
            Contribution(model=CRITIC_MODEL, content=critic_text, phase="critic")
        )
    except Exception:
        pass

    delib.decision, delib.dissents = _parse_judge(judge_text)
    return delib


# ── public API ───────────────────────────────────────────────


def deliberate(
    question: str,
    mode: str = "quick",
    panel: list[str] | None = None,
    persona: str = "",
    timeout: int = 180,
    save: bool = True,
) -> Deliberation:
    """Run a multi-model deliberation.

    Args:
        question: The question or decision to deliberate
        mode: "quick", "council", or "redteam"
        panel: Override default model panel
        persona: Context about the questioner
        timeout: Per-model timeout in seconds
        save: Auto-save transcript to chromatin
    """
    default_panels = {
        "quick": PANEL_QUICK,
        "council": PANEL_COUNCIL,
        "redteam": PANEL_REDTEAM,
        "deep": PANEL_DEEP,
    }
    if mode not in default_panels:
        raise ValueError(f"Unknown mode: {mode}. Use: quick, council, redteam, deep")

    active_panel = panel or default_panels[mode]
    t0 = time.time()

    dispatch = {
        "quick": _mode_quick,
        "council": _mode_council,
        "redteam": _mode_redteam,
        "deep": _mode_deep,
    }
    delib = dispatch[mode](question, active_panel, persona, timeout)
    delib.elapsed_s = time.time() - t0

    if save:
        delib.save()

    return delib


# ── CLI entry point ──────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Multi-model deliberation")
    parser.add_argument("question", help="Question to deliberate")
    parser.add_argument("--mode", choices=["quick", "council", "redteam", "deep"], default="quick")
    parser.add_argument("--persona", default="")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = deliberate(
        args.question,
        mode=args.mode,
        persona=args.persona,
        timeout=args.timeout,
        save=not args.no_save,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "decision": result.decision,
                    "dissents": result.dissents,
                    "mode": result.mode,
                    "elapsed_s": result.elapsed_s,
                    "contributions": [
                        {"model": c.model, "phase": c.phase, "content": c.content}
                        for c in result.contributions
                    ],
                },
                indent=2,
            )
        )
    else:
        print(result.summary())


if __name__ == "__main__":
    main()
