#!/usr/bin/env python3
"""Run the context-window-governance experiment.

3 tasks × 5 context tiers × 10 runs = 150 calls via max20 sonnet.
Outputs raw results to ~/epigenome/chromatin/Consulting/Experiments/results/

Usage:
    python3 run-experiment.py
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# --- Paths ---
EXPERIMENTS = Path.home() / "code/epigenome/chromatin/Consulting/Experiments"
TIERS_FILE = EXPERIMENTS / "context-tiers.md"
TASKS_FILE = EXPERIMENTS / "experiment-tasks.md"
RESULTS_DIR = EXPERIMENTS / "results"
MAX20 = "max20"

RUNS_PER_COMBO = 10


def parse_tiers(path: Path) -> dict[int, str]:
    """Parse context-tiers.md into {tier_num: text}."""
    content = path.read_text()
    tiers = {}
    current_tier = None
    current_lines = []

    for line in content.splitlines():
        if line.startswith("## Tier "):
            if current_tier is not None:
                tiers[current_tier] = "\n".join(current_lines).strip()
            current_tier = int(line.split("Tier ")[1][0])
            current_lines = []
        elif current_tier is not None:
            current_lines.append(line)

    if current_tier is not None:
        tiers[current_tier] = "\n".join(current_lines).strip()

    return tiers


def parse_tasks(path: Path) -> dict[str, dict]:
    """Parse experiment-tasks.md into {task_id: {prompt, rubric}}."""
    content = path.read_text()
    tasks = {}
    current_task = None
    current_section = None
    sections = {}

    for line in content.splitlines():
        if line.startswith("## Task "):
            if current_task and sections:
                tasks[current_task] = sections
            current_task = line.split("## ")[1].strip()
            sections = {}
            current_section = None
        elif line.startswith("### "):
            current_section = line.strip("# ").strip()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)

    if current_task and sections:
        tasks[current_task] = sections

    # Join section lines
    for task_id in tasks:
        for section in tasks[task_id]:
            tasks[task_id][section] = "\n".join(tasks[task_id][section]).strip()

    return tasks


def run_task(task_prompt: str, governance_context: str, tier: int) -> dict:
    """Run a single task with governance context via max20."""
    if tier == 0 or not governance_context:
        full_prompt = task_prompt
    else:
        full_prompt = (
            f"## Governance Documentation\n\n"
            f"You must follow these governance guidelines:\n\n"
            f"{governance_context}\n\n"
            f"---\n\n"
            f"## Task\n\n{task_prompt}"
        )

    token_count = len(full_prompt.split())  # rough word count as proxy

    start = time.time()
    result = subprocess.run(
        [MAX20, "sonnet", "-p", full_prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    elapsed = time.time() - start

    return {
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None,
        "elapsed_seconds": round(elapsed, 2),
        "prompt_words": token_count,
        "returncode": result.returncode,
        "refused": "I cannot" in result.stdout or "I'm unable" in result.stdout,
    }


def main():
    # Validate inputs
    if not TIERS_FILE.exists():
        print(f"ERROR: {TIERS_FILE} not found. Run doc-fetcher first.", file=sys.stderr)
        sys.exit(1)
    if not TASKS_FILE.exists():
        print(f"ERROR: {TASKS_FILE} not found. Run task-designer first.", file=sys.stderr)
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    tiers = parse_tiers(TIERS_FILE)
    tasks = parse_tasks(TASKS_FILE)

    print(f"Loaded {len(tiers)} tiers, {len(tasks)} tasks")
    print(
        f"Total runs: {len(tiers)} × {len(tasks)} × {RUNS_PER_COMBO} = {len(tiers) * len(tasks) * RUNS_PER_COMBO}"
    )

    # Extract task prompts
    task_prompts = {}
    for task_id, sections in tasks.items():
        # Find the task prompt section
        for key in sections:
            if "prompt" in key.lower():
                task_prompts[task_id] = sections[key]
                break

    results = []
    total = len(tiers) * len(task_prompts) * RUNS_PER_COMBO
    count = 0

    for tier_num in sorted(tiers.keys()):
        for task_id, prompt in task_prompts.items():
            for run in range(RUNS_PER_COMBO):
                count += 1
                task_short = task_id[:20]
                print(
                    f"[{count}/{total}] Tier {tier_num} | {task_short} | Run {run + 1}/{RUNS_PER_COMBO}",
                    end=" ... ",
                    flush=True,
                )

                try:
                    result = run_task(prompt, tiers[tier_num], tier_num)
                    result["tier"] = tier_num
                    result["task"] = task_id
                    result["run"] = run + 1
                    result["timestamp"] = datetime.now().isoformat()
                    results.append(result)
                    status = (
                        "REFUSED" if result["refused"] else ("ERROR" if result["error"] else "OK")
                    )
                    print(f"{status} ({result['elapsed_seconds']}s)")
                except subprocess.TimeoutExpired:
                    print("TIMEOUT")
                    results.append(
                        {
                            "tier": tier_num,
                            "task": task_id,
                            "run": run + 1,
                            "error": "timeout",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except Exception as e:
                    print(f"EXCEPTION: {e}")
                    results.append(
                        {
                            "tier": tier_num,
                            "task": task_id,
                            "run": run + 1,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

    # Save results
    outfile = RESULTS_DIR / f"raw-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    outfile.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {outfile}")
    print(
        f"Total: {len(results)} runs, {sum(1 for r in results if r.get('error'))} errors, {sum(1 for r in results if r.get('refused'))} refusals"
    )


if __name__ == "__main__":
    main()
