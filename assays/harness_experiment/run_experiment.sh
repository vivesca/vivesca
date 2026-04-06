#!/usr/bin/env bash
# harness-experiment — run 5 task types through CC, Droid, and Goose.
# Run directly on ganglion (not via mtor — avoids env pollution).
set -uo pipefail
# No set -e: individual task failures must not kill the experiment

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_FILE="${HOME}/.local/share/vivesca/harness-experiment.jsonl"
OUTPUTS_DIR="${HOME}/.local/share/vivesca/harness-outputs"
RUNS="${1:-1}"  # number of runs per combination (default 1, use 3 for significance)
TIMEOUT=300     # 300s — enough for droid's 30s ARM startup + long tasks
HARNESSES=(zhipu droid goose)
RIBOSOME="$(dirname "$SCRIPT_DIR")/../effectors/ribosome"

mkdir -p "$(dirname "$RESULTS_FILE")" "$OUTPUTS_DIR"

log() { echo "[$(date +%H:%M:%S)] $*" >&2; }

run_task() {
  local task_name="$1" harness="$2" work_dir="$3" prompt="$4" run_num="${5:-1}"
  local start end elapsed exit_code tests_pass tests_fail py_files output_dir

  # Preserve output for inspection
  output_dir="$OUTPUTS_DIR/${task_name}_${harness}_run${run_num}"
  mkdir -p "$output_dir"

  start=$(date +%s)
  # Capture exit code without triggering set -e
  timeout "$TIMEOUT" bash "$RIBOSOME" --provider "$harness" "$prompt" \
    > "$output_dir/stdout.txt" 2> "$output_dir/stderr.txt" \
    && exit_code=0 || exit_code=$?
  end=$(date +%s)
  elapsed=$((end - start))

  # Copy work dir contents for inspection
  cp "$work_dir"/*.py "$output_dir/" 2>/dev/null || true
  cp "$work_dir"/*.txt "$output_dir/" 2>/dev/null || true
  cp "$work_dir"/*.md "$output_dir/" 2>/dev/null || true

  # Count .py files created (exclude seeded test files)
  py_files=$(find "$work_dir" -name '*.py' -newer "$work_dir/.timestamp" 2>/dev/null | wc -l)

  # Run pytest if test files exist
  tests_pass=0
  tests_fail=0
  if ls "$work_dir"/test_*.py >/dev/null 2>&1; then
    local pytest_output
    pytest_output=$(cd "$work_dir" && python3 -m pytest -v --tb=short -q 2>&1 || true)
    echo "$pytest_output" > "$output_dir/pytest.txt"
    tests_pass=$(echo "$pytest_output" | grep -oP '\d+ passed' | grep -oP '\d+' || echo 0)
    tests_fail=$(echo "$pytest_output" | grep -oP '\d+ failed' | grep -oP '\d+' || echo 0)
  fi

  # Write result (HKT timestamps)
  printf '{"task":"%s","harness":"%s","run":%d,"time_s":%d,"exit":%d,"py_files":%d,"tests_pass":%s,"tests_fail":%s,"ts":"%s"}\n' \
    "$task_name" "$harness" "$run_num" "$elapsed" "$exit_code" "$py_files" \
    "${tests_pass:-0}" "${tests_fail:-0}" "$(date +%Y-%m-%dT%H:%M:%S%z)" \
    >> "$RESULTS_FILE"

  log "$task_name/$harness/r${run_num}: ${elapsed}s exit=$exit_code pass=${tests_pass:-0} fail=${tests_fail:-0}"
}

run_with_harness() {
  local harness="$1" run_num="$2"

  # Task 1: Simple implementation
  log "=== Task 1: simple_impl ($harness r$run_num) ==="
  local dir1=$(mktemp -d)
  cp "$SCRIPT_DIR/task1_simple_impl/test_stack.py" "$dir1/"
  touch "$dir1/.timestamp"
  (cd "$dir1" && run_task "simple_impl" "$harness" "$dir1" \
    "Read test_stack.py. Implement stack.py with a Stack class that passes all tests. Run pytest to verify." "$run_num")

  # Task 2: Exploration
  log "=== Task 2: exploration ($harness r$run_num) ==="
  local dir2=$(mktemp -d)
  cp "$SCRIPT_DIR/task2_exploration/"*.py "$dir2/"
  cp "$SCRIPT_DIR/task2_exploration/expected_answers.txt" "$dir2/"
  touch "$dir2/.timestamp"
  (cd "$dir2" && run_task "exploration" "$harness" "$dir2" \
    "Read all .py files in this directory. Write a file called analysis.txt answering: (1) What design pattern is used? Name it. (2) List ALL public method names across all classes. (3) What is the dependency graph between files (which imports which)?" "$run_num")
  # Finer-grained exploration scoring
  local score=0 max_score=6
  if [ -f "$dir2/analysis.txt" ]; then
    grep -qi "abstract.*factory\|factory.*pattern" "$dir2/analysis.txt" && score=$((score + 1))  # correct pattern name
    grep -qi "factory" "$dir2/analysis.txt" && score=$((score + 1))                               # mentions factory at all
    grep -qi "send" "$dir2/analysis.txt" && grep -qi "validate" "$dir2/analysis.txt" && score=$((score + 1))  # both Notification methods
    grep -qi "notify\|bulk_notify" "$dir2/analysis.txt" && score=$((score + 1))                   # Service methods
    grep -qi "create\|register\|available" "$dir2/analysis.txt" && score=$((score + 1))           # Factory methods
    grep -qi "service.*import.*factory\|service.*depends.*factory\|service.*->.*factory" "$dir2/analysis.txt" && score=$((score + 1))  # dependency direction
    printf '{"task":"exploration_score","harness":"%s","run":%d,"score":%d,"max":%d,"ts":"%s"}\n' \
      "$harness" "$run_num" "$score" "$max_score" "$(date +%Y-%m-%dT%H:%M:%S%z)" >> "$RESULTS_FILE"
  else
    printf '{"task":"exploration_score","harness":"%s","run":%d,"score":0,"max":%d,"ts":"%s"}\n' \
      "$harness" "$run_num" "$max_score" "$(date +%Y-%m-%dT%H:%M:%S%z)" >> "$RESULTS_FILE"
  fi

  # Task 3: Multi-file refactor
  log "=== Task 3: refactor ($harness r$run_num) ==="
  local dir3=$(mktemp -d)
  cp "$SCRIPT_DIR/task3_refactor/"*.py "$dir3/"
  touch "$dir3/.timestamp"
  (cd "$dir3" && run_task "refactor" "$harness" "$dir3" \
    "Rename the class UserManager to AccountService in ALL files. Update all imports, references, type annotations, docstrings, and test fixtures. The file user_manager.py should be renamed to account_service.py. Update test_user_manager.py to test_account_service.py. Run pytest to verify everything passes." "$run_num")
  # Check refactor completeness
  local old_refs new_file
  old_refs=$(grep -rl "UserManager\|user_manager" "$dir3/" 2>/dev/null | wc -l)
  old_refs=${old_refs:-0}
  new_file=0; [ -f "$dir3/account_service.py" ] && new_file=1
  printf '{"task":"refactor_quality","harness":"%s","run":%d,"old_refs":%d,"new_file_exists":%d,"ts":"%s"}\n' \
    "$harness" "$run_num" "$old_refs" "$new_file" "$(date +%Y-%m-%dT%H:%M:%S%z)" >> "$RESULTS_FILE"

  # Task 4: Bug diagnosis + fix
  log "=== Task 4: bugfix ($harness r$run_num) ==="
  local dir4=$(mktemp -d)
  cp "$SCRIPT_DIR/task4_bugfix/"*.py "$dir4/"
  touch "$dir4/.timestamp"
  (cd "$dir4" && run_task "bugfix" "$harness" "$dir4" \
    "test_calc.py has failing tests. Read both test_calc.py and calc.py. Diagnose the bugs in calc.py, fix them, and run pytest to verify all tests pass. Do NOT modify test_calc.py." "$run_num")

  # Task 5: Test generation from spec
  log "=== Task 5: test_gen ($harness r$run_num) ==="
  local dir5=$(mktemp -d)
  cp "$SCRIPT_DIR/task5_test_gen/SPEC.md" "$dir5/"
  touch "$dir5/.timestamp"
  (cd "$dir5" && run_task "test_gen" "$harness" "$dir5" \
    "Read SPEC.md describing a URL shortener module. Write comprehensive pytest tests in test_shortener.py. Write at least 8 test functions covering all methods, edge cases (empty URL, invalid URL, missing code, idempotent shorten, delete then expand). Do NOT implement shortener.py — only write tests." "$run_num")
  # Count test functions
  if [ -f "$dir5/test_shortener.py" ]; then
    local test_count
    test_count=$(grep -c 'def test_' "$dir5/test_shortener.py" || echo 0)
    printf '{"task":"test_gen_count","harness":"%s","run":%d,"test_functions":%d,"ts":"%s"}\n' \
      "$harness" "$run_num" "$test_count" "$(date +%Y-%m-%dT%H:%M:%S%z)" >> "$RESULTS_FILE"
  fi
}

log "Starting harness experiment (runs=$RUNS, timeout=${TIMEOUT}s, harnesses=${HARNESSES[*]})"
for run in $(seq 1 "$RUNS"); do
  log "========== Run $run/$RUNS =========="
  for harness in "${HARNESSES[@]}"; do
    log "=== Harness: $harness (run $run) ==="
    run_with_harness "$harness" "$run"
  done
done

log "=== Summary ==="
python3 -c "
import json, sys, statistics
from collections import defaultdict

with open('$RESULTS_FILE') as fh:
    records = [json.loads(line) for line in fh if line.strip()]

# Group by task+harness
groups = defaultdict(list)
for rec in records:
    if 'time_s' in rec:
        key = (rec['task'], rec['harness'])
        groups[key].append(rec)

print(f\"{'Task':<20} {'Harness':<8} {'Runs':>4} {'Time':>8} {'Pass':>6} {'Fail':>5} {'Exit':>5}\")
print('-' * 62)
for key in sorted(groups.keys()):
    recs = groups[key]
    times = [r['time_s'] for r in recs]
    passes = [r.get('tests_pass', 0) for r in recs]
    fails = [r.get('tests_fail', 0) for r in recs]
    exits = [r['exit'] for r in recs]
    avg_t = statistics.mean(times)
    avg_p = statistics.mean(passes)
    avg_f = statistics.mean(fails)
    task, harness = key
    print(f'{task:<20} {harness:<8} {len(recs):>4} {avg_t:>7.0f}s {avg_p:>5.0f} {avg_f:>5.0f} {exits[0]:>5}')

# Score summaries
scores = defaultdict(list)
for rec in records:
    if 'score' in rec:
        scores[(rec['task'], rec['harness'])].append(rec['score'])
if scores:
    print()
    for key in sorted(scores.keys()):
        vals = scores[key]
        print(f'{key[0]:<20} {key[1]:<8} score={statistics.mean(vals):.1f}/{records[0].get(\"max\", \"?\") if \"max\" in records[0] else \"?\"}')
" 2>&1 || true
log "Done. Results: $RESULTS_FILE  Outputs: $OUTPUTS_DIR"
