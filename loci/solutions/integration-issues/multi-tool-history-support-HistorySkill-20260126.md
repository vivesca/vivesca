---
module: History Skill
date: 2026-01-26
problem_type: integration_issue
component: tooling
symptoms:
  - "History skill only showing Claude Code activity"
  - "Missing Codex and OpenCode chat history in consolidated view"
root_cause: incomplete_setup
resolution_type: tooling_addition
severity: medium
tags: [opencode, codex, chat-history, history-skill]
---

# Multi-Tool History Support for Chat History Skill

## Problem Statement
The existing `history` skill was designed exclusively for Claude Code, scanning only `~/.claude/history.jsonl`. This created a fragmented experience where activity from other CLI chatbot tools like **Codex** and **OpenCode** was invisible in the consolidated daily reflection and history views.

## Investigation Steps
1. **Source Discovery**: Verified storage locations for alternative tools.
   - **Codex**: Uses `~/.codex/history.jsonl` (identical format to Claude).
   - **OpenCode**: Uses a structured JSON hierarchy in `~/.local/share/opencode/storage/` (sessions, messages, and parts stored separately).
2. **Compatibility Check**: Observed that while OpenCode sometimes syncs to Claude's history file for compatibility, it doesn't capture all sessions there, and the linear log format misses the rich metadata available in its own storage.
3. **Storage Schema Analysis**: Parsed the OpenCode storage structure:
   - `session/[project]/[session_id].json`: Metadata (title, timestamps).
   - `message/[session_id]/msg_[id].json`: Role and timing.
   - `part/msg_[id]/prt_[id].json`: The actual text of the prompt or response.

## Root Cause
The `history` skill scanner was hardcoded to a single file path and format, failing to account for the diversity of chatbot tools in the environment and their distinct storage architectures.

## Working Solution
Enhanced `~/scripts/chat_history.py` to support a polymorphic scanning approach:

### 1. Multi-File JSONL Scanning
The script now scans both Claude and Codex history files if they exist.

### 2. OpenCode Structured Scanner
Implemented `scan_opencode()` to crawl the structured JSON hierarchy, extracting user prompts and reconstructing session timelines from disparate files.

### 3. Consolidated Timeline
Combined results from all tools into a single time-sorted list with explicit tool labeling.

### 4. Tool Filtering
Added a `--tool=` flag to allow users to focus on specific tool activity.

```python
# Updated scanning logic in ~/scripts/chat_history.py
def scan_opencode(start_ms: int, end_ms: int) -> list:
    # ... logic to crawl ~/.local/share/opencode/storage/ ...
    return prompts

def scan_history(target_date_str: str, limit: int = 50, tool: Optional[str] = None) -> Dict[str, Any]:
    # ... logic to scan JSONL files + call scan_opencode() ...
    prompts.sort(key=lambda x: x["timestamp"])
    return result
```

## Prevention
- **Abstract Storage**: When building tooling that interacts with external apps, design for multiple storage backends rather than assuming a single file path.
- **Label Sources**: Always include source metadata when consolidating data from multiple origins to prevent context confusion.

## Related Issues
No related issues documented yet.
