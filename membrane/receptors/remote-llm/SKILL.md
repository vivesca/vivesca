---
name: remote-llm
description: Craft prompts for local/work LLMs when code can't be shared directly (e.g. proprietary code).
user_invocable: true
---

# Remote LLM Workflow

Use this pattern when Terry needs help with code he can't share directly (e.g., proprietary bank code). Claude crafts prompts, Terry runs them on a local/work LLM (like Qwen3-32B at CITIC), and shares results back.

## Workflow

1. **Discovery prompt** — Find the relevant code
   - Ask for file structure, class names, method signatures
   - Keep scope narrow to avoid overwhelming output

2. **Terry runs locally** — Pastes prompt + attaches files to work LLM

3. **Interpret results** — Understand what was found

4. **Modification prompt** — Make specific changes
   - Reference exact locations from discovery
   - Keep changes incremental

5. **Iterate** — Repeat until task complete

## Prompt Delivery

Create secret gists for easy copy-paste:
```bash
gh gist create -d "discovery prompt" -f "prompt.md" - <<'EOF'
[prompt content here]
EOF
```

**Always secret gists.** Never `-p` or `--public`. Delete after use.

## Prompt Structure Tips

- Start with clear context: "You are helping modify [system/module]..."
- Be explicit about output format: "Return only the modified function"
- For discovery: "List all methods in [class] with their signatures"
- For modification: "In [file], find [function], change [X] to [Y]"

## Model-Specific Notes

If Terry mentions which model, check vault for tips:
- Qwen3: See `[[Qwen3 Prompting Best Practices]]` — thinking mode, temperature settings
