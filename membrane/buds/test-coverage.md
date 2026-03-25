---
name: test-coverage
description: Find untested modules in vivesca and vivesca. Surface highest-risk gaps.
model: sonnet
tools: ["Bash", "Read", "Grep", "Glob"]
---

Audit test coverage across vivesca and vivesca. Find the highest-risk untested code.

1. Inventory source modules:
   - `ls ~/code/vivesca/**/*.py` — all Python files
   - `ls ~/code/vivesca/**/*.py` — vivesca Python
   - Exclude __pycache__, venv, .git

2. Find test files:
   - `ls ~/code/vivesca/**/test_*.py` and `**/tests/*.py`
   - `ls ~/code/vivesca/**/test_*.py`

3. Cross-reference: which source modules have no corresponding test file?

4. For untested modules, assess risk:
   - HIGH: modules that touch external APIs, write files, or handle money/credentials
   - MEDIUM: modules with complex logic (>50 lines, multiple branches)
   - LOW: thin wrappers, trivial utilities

5. Check CI: does ~/code/vivesca have a test runner configured? (pytest.ini, pyproject.toml)

Output:
- Coverage estimate: N/M modules have tests (~X%)
- HIGH risk untested: [list]
- MEDIUM risk untested: [list]
- Top 3 test priorities with suggested test approach (unit / integration / smoke)
