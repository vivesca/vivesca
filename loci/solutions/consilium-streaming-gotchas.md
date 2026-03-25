# Consilium Streaming Gotchas

## is_thinking_model Gate (REMOVED in v0.13.0)

Previously, `query_model()` with `stream=verbose` checked `is_thinking_model()` and fell back to non-streaming. Since ALL council models are thinking models, this effectively disabled streaming everywhere. Gate removed — streaming now works for all models. The `<think>` block filtering in `query_model_streaming()` handles thinking content.

## OpenRouter Reasoning Token Formats

Two different formats depending on model family — both handled differently:

- **DeepSeek-R1, QwQ**: thinking tokens appear in `choices[0].delta.content` wrapped in `<think>...</think>` tags. Must filter inline.
- **OpenAI models (GPT-5.2-pro, o3, etc.)**: reasoning in `choices[0].delta.reasoning_details` (separate field). Never appears in `content` — no filtering needed.

Our SSE parser reads only `delta.content`, so OpenAI reasoning is automatically invisible.

## RichLog + Markdown Rendering (TUI)

`RichLog.write()` accepts `rich.markdown.Markdown` renderables directly. Pattern for streaming + markdown:

1. Buffer body lines while model response streams
2. Show rolling preview in a separate Static widget during streaming
3. On block boundary (next model header, separator, phase banner), flush buffer as `Markdown(content)` into RichLog
4. RichLog renders headers, bold, lists, code blocks with syntax highlighting

Don't write lines individually AND as markdown — you'll get duplicate content.

## LiveWriter atexit Ordering

`atexit` handlers run before Python's final `sys.stdout` flush during shutdown. If LiveWriter wraps stdout and the underlying file is closed in atexit, the final flush raises `ValueError: I/O operation on closed file`. Guard both `write()` and `flush()`:

```python
if not self._file.closed:
    self._file.write(data)
```

## Concurrent Live Files

Multiple consilium processes writing to the same `live.md` truncate each other. Solution: per-PID files with symlink.

- Each process writes `live-{pid}.md`
- Symlink `live.md` → `live-{pid}.md` (latest wins, which is fine)
- `--watch`/`--tui` follow the symlink and detect rotation
- atexit cleans up the PID file

## Colored Output (v0.1.3+)

StdoutOutput and TeeOutput do line-buffered color rendering. Key pattern:
- Buffer partial lines (streaming chunks don't end on newlines)
- On newline: classify via `watch::classify()`, render with crossterm styles
- Partial lines flush immediately as plain text (`flushed_partial` flag prevents double-print on subsequent newline)
- TeeOutput: file always gets plain text, stdout gets colored
- Auto-disabled when stdout is not a terminal (`IsTerminal` trait) or `NO_COLOR` env set

## Context Compression (v0.1.4+)

Multi-round debates compress prior rounds via cheap model (Llama 3.3 70B).
- Only for convergence modes (council, discuss). NOT oxford/redteam/socratic.
- Compressed summaries replace full prior-round entries in context building.
- Judge synthesis always gets full transcripts, not summaries.
- `--thorough` disables both compression and consensus early exit.
- Fallback: if compression model fails (`[Error:` prefix), silently uses full context.
- Conversation vec only contains debate entries (blind claims go into separate `blind_context` string), so `round_num * council_config.len()` indexing is correct.
