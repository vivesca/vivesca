#!/bin/bash
# Enzyme refactor — run each task via Goose sequentially
# Usage: ./run-enzyme-refactor.sh [start_task_number]
# Each task commits on success, stops on test failure.

set -euo pipefail
cd "$(dirname "$0")"

START=${1:-1}
SPEC="ENZYME_REFACTOR_SPEC.md"
TOTAL=11

run_task() {
    local n=$1
    echo "=========================================="
    echo "TASK $n of $TOTAL"
    echo "=========================================="

    # Extract task section from spec
    local task_text
    task_text=$(python3 -c "
import re
with open('$SPEC') as f:
    content = f.read()
# Find Task N section
pattern = r'## Task $n:.*?(?=## Task |\Z)'
match = re.search(pattern, content, re.DOTALL)
if match:
    print(match.group(0).strip())
else:
    print('ERROR: Task $n not found')
    exit(1)
")

    local prompt="You are refactoring the vivesca MCP server in ~/germline/.

CRITICAL RULES:
- After ANY file delete or rename, run: grep -r 'old_name' --include='*.py' --include='*.md' to find ALL stale references. Fix them ALL.
- After ALL changes, run: python3 -m pytest assays/ -x -q
- If tests fail, fix the issue before finishing.
- Do NOT rename any MCP tool names (the @tool(name=...) values). Only move/rename files.
- Commit your changes with a descriptive message when tests pass.

HERE IS YOUR TASK:

$task_text"

    echo "$prompt" | head -5
    echo "..."
    echo ""

    goose run -t "$prompt"

    # Verify tests pass after goose
    echo "--- Verifying tests ---"
    python3 -m pytest assays/ -x -q || {
        echo "TESTS FAILED after task $n — stopping"
        exit 1
    }
    echo "Task $n complete"
    echo ""
}

for n in $(seq "$START" "$TOTAL"); do
    run_task "$n"
done

echo "=========================================="
echo "ALL $TOTAL TASKS COMPLETE"
echo "=========================================="

# Final verification
echo "--- Final stale reference check ---"
grep -r "from metabolon.enzymes.electroreception\|from metabolon.enzymes.interphase\|from metabolon.enzymes.polymerization\|from metabolon.enzymes.signaling\|from metabolon.enzymes.mutation_sense\|from metabolon.enzymes.porta\|from metabolon.enzymes.fasti" --include='*.py' . && {
    echo "WARNING: Stale references found!"
    exit 1
} || echo "No stale references. Clean."

python3 -m pytest assays/ -q
echo "Done. Review with: git log --oneline -11"
