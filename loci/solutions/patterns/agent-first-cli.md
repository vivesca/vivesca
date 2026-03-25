# Agent-First CLI Design

## Pattern

Design CLI output for agent consumption by default. Give humans the pretty version via TTY detection — not the other way around.

**Traditional assumption:** CLI output is for humans. Add `--json` or `--plain` as an afterthought for scripting.

**Agent-first inversion:** CLI output is read by agents as often as by humans. Make plain/structured output the default. TTY detection gives humans colour and box art automatically — no flag needed.

## Implementation (Rust)

```rust
use std::io::IsTerminal;

fn is_tty() -> bool {
    std::io::stdout().is_terminal()
}

fn print_panel(title: &str) {
    if is_tty() {
        let w = title.chars().count() + 2;
        println!("╭{}╮", "─".repeat(w));
        println!("│ {} │", title.bold());
        println!("╰{}╯", "─".repeat(w));
    } else {
        println!("## {title}");
    }
}
```

The `colored` crate already auto-strips ANSI codes when stdout is not a TTY. Only box art needs explicit handling.

## Why It Matters

When an agent runs `melete session`, it reads the output as context. ANSI escape codes are noise. Box art (╭─╮) is noise. `## Session Plan` is clean markdown the agent can parse directly.

When a human runs it in terminal: full colour, box art, visual hierarchy.

Zero flags. Zero configuration. The environment self-selects.

## Generalisation

Any CLI that will be invoked by agents should follow this pattern:
- Plain text / markdown by default (agent-readable)
- TTY detection for human-friendly formatting
- `--color=always` escape hatch if needed

This applies to `melete`, `oura`, `rai.py` successors, and any tool the morning brief or skills invoke.

## Origin

Emerged from porting `rai.py` → `melete` (Rust). Claude Code reads session output as context; ANSI codes burned tokens and degraded parsing. TTY detection solved it without any interface change.
