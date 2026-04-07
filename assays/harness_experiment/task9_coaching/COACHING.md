# Coaching Constraints (MANDATORY)

You MUST follow ALL of these rules. Violations = failure.

1. **pathlib only** — use `from pathlib import Path`, never `os.path`
2. **Type hints on every function** — all params and return types annotated
3. **No bare except** — always catch specific exception types, never `except:` or `except Exception:`
4. **Docstrings required** — every public function needs a one-line docstring
5. **urllib only** — use `urllib.request`, never `requests` or `httpx`
6. **Constants uppercase** — any module-level constants must be UPPER_SNAKE_CASE
7. **No print()** — use logging or raise exceptions, never print()
