
## ERR-20260306-001: tmux-namer silent failure — Anthropic API balance depleted
Hook caught all exceptions silently (bare `except: pass`). Symptom: hook runs, installs deps, exits 0, but window not renamed. Diagnosis: run the API call directly outside the hook to see the real error.
Fix: switched to OpenRouter (httpx + google/gemini-3-flash-preview). OPENROUTER_API_KEY injected via 1Password template.
Lesson: hooks that swallow all exceptions need a debug path (e.g. log to /tmp on failure).
