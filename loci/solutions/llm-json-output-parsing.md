
## extract_json — brace-matching required (LRN-20260311-001)

Simple code-fence stripping is not enough. `claude-haiku-4-5` sometimes outputs
valid JSON followed by trailing prose (e.g. a JSON object then a blank line then
"Here is the analysis..."). `json.loads()` raises JSONDecodeError: Extra data.

**Fix:** After stripping fences, find the first complete JSON object by depth-counting:

```python
def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    text = text.strip()
    if text.startswith("{"):
        depth, end = 0, 0
        for i, ch in enumerate(text):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end:
            text = text[:end]
    return json.loads(text)
```

Applies to all eval harnesses and any workflow using Haiku for structured JSON output.
Source: eval_judge_calibration.py, eval_speculor_triage.py (Mar 2026)
