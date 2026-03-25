---
name: pii-mask
description: Mask sensitive information before sending to external LLMs. Reference skill for Claude Code to use when delegating tasks.
user_invocable: false
---

# PII Mask

Mask personally identifiable information before sending prompts to external LLMs (OpenCode, ask-llms, etc.).

## When to Use

- **Delegating to external LLMs** with personal context (salary, phone, specific names)
- **Multi-model queries** where data goes through OpenRouter
- **Any prompt** containing info that doesn't need to leave Anthropic's servers

## When NOT to Use

- Prompts to Claude Code directly (same trust boundary)
- When the PII is essential for the task (e.g., "draft a message to John Smith" needs the name)
- Code-only prompts with no personal data

## What Gets Masked

| Entity | Example | Masked |
|--------|---------|--------|
| Phone numbers | 6187 2354, +852-6187-2354 | [REDACTED] |
| Email addresses | terry@example.com | [REDACTED] |
| Names | Terry Li | [REDACTED] |
| Credit cards | 4111-1111-1111-1111 | [REDACTED] |
| IP addresses | 192.168.1.1 | [REDACTED] |
| Locations | Hong Kong, Central | [REDACTED] |
| HK IDs | A123456(7) | [REDACTED] |

## Usage

### From Claude Code (recommended)

```bash
# Mask a prompt before delegation
cd /Users/terry/skills/pii-mask
masked=$(uv run mask.py "My salary is 2.5M HKD, call me at 6187 2354")
OPENCODE_HOME=~/.opencode-lean opencode run -m zhipuai-coding-plan/glm-5 --title "Task" "$masked"
```

### Dry-run (preview what gets masked)

```bash
uv run mask.py --dry-run "Contact Terry at terry@cncbi.com.hk or +852 6187 2354"
```

Output:
```json
{
  "original": "Contact Terry at terry@cncbi.com.hk or +852 6187 2354",
  "masked": "Contact [REDACTED] at [REDACTED] or [REDACTED]",
  "findings": [
    {"type": "PERSON", "text": "Terry", "score": 0.85},
    {"type": "EMAIL_ADDRESS", "text": "terry@cncbi.com.hk", "score": 1.0},
    {"type": "HK_PHONE", "text": "+852 6187 2354", "score": 0.9}
  ],
  "count": 3
}
```

### Pipe from stdin

```bash
cat prompt.txt | uv run mask.py
```

### Custom entities only

```bash
uv run mask.py --entities "PHONE_NUMBER,EMAIL_ADDRESS" "Call 6187 2354"
```

## Integration Pattern

When Claude Code delegates to external LLMs:

```
Claude receives prompt with PII
    ↓
Check: Does prompt contain personal info?
    ↓ Yes
Run through pii-mask
    ↓
Delegate masked prompt to OpenCode/ask-llms
    ↓
Receive response (may contain [REDACTED] placeholders)
    ↓
Claude interprets response with original context
```

## Entities Detected

Default entities (via Microsoft Presidio):
- `EMAIL_ADDRESS`
- `PHONE_NUMBER`
- `PERSON` (names)
- `CREDIT_CARD`
- `IBAN_CODE`
- `IP_ADDRESS`
- `LOCATION`
- `DATE_TIME`
- `URL`

HK-specific (custom patterns):
- `HK_PHONE` (+852 format)
- `HK_ID` (HKID format)

## Files

- Script: `/Users/terry/skills/pii-mask/mask.py`
- This skill: `/Users/terry/skills/pii-mask/SKILL.md`
