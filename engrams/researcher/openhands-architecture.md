# OpenHands Architecture Research (Feb 22, 2026)

Source: github.com/All-Hands-AI/OpenHands (64K stars)
Warning: V0 (current main) is deprecated; removal April 1, 2026. V1 SDK = github.com/OpenHands/software-agent-sdk

## Reliable Sources for This Topic
- Raw GitHub files: raw.githubusercontent.com/All-Hands-AI/OpenHands/main/openhands/**
- Deepwiki: deepwiki.com/All-Hands-AI/OpenHands (good structural summary)
- Arxiv SDK paper: arxiv.org/html/2511.03690v1 (V1 architecture detail)
- Condenser docs: docs.openhands.dev/sdk/arch/condenser (clean, WebFetch works)
- Runtime docs: docs.openhands.dev/openhands/usage/architecture/runtime

## 1. Event-Sourced State Model

### Files
- `openhands/events/event.py` — Event base class
- `openhands/events/stream.py` — EventStream (pub/sub + disk write)
- `openhands/events/event_store.py` — Replay and disk read

### Implementation
Every interaction is an **append-only Event**. Events have: `id` (sequential int), `timestamp`, `source` (AGENT/USER/ENVIRONMENT), `cause` (reference to causing event), `llm_metrics`. Two main subtypes: **Action** (intent) and **Observation** (result).

EventStream writes each event to disk as individual JSON files named by ID. Also maintains a page cache (25 events/page) for efficient batch reads. Sequential counter assigned under lock at `add_event()`.

**Pub/sub:** Subscribers register callbacks. A daemon thread processes a queue; callbacks execute in per-subscriber thread pools (isolated — one subscriber crash doesn't kill others).

**Replay:** `EventStore.search_events(start_id, end_id)` reads cache pages first, falls back to individual files. Events yield in order, matching optional filters. This is how session restoration works — read all stored events to reconstruct state.

### Key pattern
```python
# Every component posts to the single EventStream
event_stream.add_event(action, source=EventSource.AGENT)
# Subscribers get notified async
event_stream.subscribe(EventStreamSubscriber.AGENT_CONTROLLER, callback, sid)
```

## 2. Sandbox Architecture

### Files
- `openhands/runtime/base.py` — Runtime ABC
- `openhands/runtime/impl/docker/docker_runtime.py` — Docker implementation
- `openhands/runtime/action_execution_server.py` — Runs INSIDE the container

### Model: One Docker container per session
Container name pattern: `openhands-runtime-{session_id}`. Port ranges: bash/exec server 30000–39999, VSCode 40000–49999, app ports 50000–59999. File-locked port allocation prevents race conditions across parallel sessions.

### How bash/Jupyter/browser coexist
They all run inside the SAME container, managed by a single **ActionExecutor** (FastAPI server running inside the container). The container starts with `tini` as init process.

Action dispatch is duck-typed string routing:
```python
async def run_action(self, action) -> Observation:
    action_type = action.action   # e.g. "run", "run_ipython", "browse"
    observation = await getattr(self, action_type)(action)
    return observation
```

- **Bash**: `BashSession.execute()` — persistent bash state across commands
- **Jupyter**: `JupyterPlugin` — IPython kernel, syncs CWD with bash session
- **Browser**: `BrowserEnv` (Playwright Chromium) — lazy-initialized on first browse action
- **Files**: Direct filesystem I/O via `OHEditor`

Plugin system: `ALL_PLUGINS` dict maps name → plugin class. Loaded at container startup, async with 120s timeout protection.

### Runtime ABC (interface)
```python
# Must implement:
async def connect()
run(CmdRunAction) -> CmdOutputObservation
run_ipython(IPythonRunCellAction) -> IPythonRunCellObservation
browse(BrowseURLAction) -> BrowserObservation
read/write/edit(FileAction) -> FileObservation
call_tool_mcp(MCPAction) -> ToolObservation
```

Concrete impls: DockerRuntime, KubernetesRuntime, RemoteRuntime, E2BRuntime, ModalRuntime.

## 3. Anti-Looping / Context Management

### Files
- `openhands/controller/stuck.py` — StuckDetector
- `openhands/controller/agent_controller.py` — Integration + recovery
- `openhands/memory/condenser/condenser.py` — Condenser ABC
- Various condenser implementations under `openhands/memory/condenser/`

### Stuck Detection (5 patterns)
1. **Same action → same observation, 4× in a row** → stuck
2. **Same action → error, 3× in a row** (including IPython syntax errors) → stuck
3. **Monologue: agent sends same MessageAction to itself 3× with no observations** → stuck
4. **Alternating A-B-A-B-A-B pattern across 6 steps** → stuck
5. **10× consecutive AgentCondensationObservation with nothing else** → stuck

Comparison uses `_eq_no_pid()` — ignores PIDs in shell observations, compares commands + exit codes.

In headless mode: scans full history. In interactive mode: only scans since last user message.

### Recovery options (interactive mode)
- Option 1: Truncate to before the loop start (`_truncate_memory_to_point(recovery_point)` — clears `state.end_id`, cached first message)
- Option 2: Restart with last user message
- Option 3: Stop completely

### Context / Condenser
Condenser types:
- **NoOpCondenser** — pass-through (default)
- **LLMSummarizingCondenser** — triggers at `max_size=120` events; preserves first 4 + last N; LLM summarizes middle; wraps in `Condensation` event containing `forgotten_event_ids`
- **AmortizedForgettingCondenser** — same truncation without LLM summarization
- **RecentEventsCondenser** — sliding window (drops oldest)
- **PipelineCondenser** — chains multiple condensers sequentially

Trigger: `condenser.condense(view)` called every step. Can also be triggered manually via `CondensationRequestAction` when context window is hit. Post-condensation target: ~60 events (max_size/2).

**Scaling claim:** Quadratic → linear context growth. Condensation batches at a fixed threshold (not every turn), enabling prompt cache reuse.

## 4. step(state) → action Abstraction

### Files
- `openhands/controller/agent.py` — Agent base class
- `openhands/agenthub/codeact_agent/codeact_agent.py` — Main implementation
- `openhands/agenthub/codeact_agent/function_calling.py` — Tool call → Action conversion

### Agent base class
```python
class Agent:
    _registry: dict[str, type['Agent']] = {}

    @abstractmethod
    def step(self, state: State) -> Action:
        """One step toward the goal."""
        ...

    @classmethod
    def register(cls, name: str, agent_cls: type['Agent']): ...
    @classmethod
    def get_cls(cls, name: str) -> type['Agent']: ...
```

Registry pattern: string name → class. `AgentAlreadyRegisteredError` on duplicate.

### CodeActAgent.step() flow
1. Run condenser on `state.history` to get a bounded `View`
2. Call `ConversationMemory.process_events(view)` → list of LLM messages (tool calls preserved with `tool_call_id` for matching)
3. Add tool definitions (filtered by model capabilities)
4. `llm.completion(messages, tools)` — standard Chat Completions call
5. `response_to_actions()` — maps tool call names to Action classes:
   - `CmdRunTool` → `CmdRunAction`
   - `IPythonTool` → `IPythonRunCellAction`
   - `BrowserTool` → `BrowseInteractiveAction`
   - `FinishTool` → `AgentFinishAction`
   - `ThinkTool` → `AgentThinkAction`
   - File tools → `FileReadAction`/`FileEditAction`
   - MCP → `MCPAction` (dynamic)

### AgentController drives the loop
```python
# Controller's main loop trigger:
async def _step(self):
    if self.state != RUNNING or self._pending_action:
        return
    if self._is_stuck():
        raise AgentStuckInLoopError(...)
    action = self.agent.step(self.state)  # THE interface
    self.event_stream.add_event(action, source=AGENT)
    # pending_action set; cleared when observation arrives
```

`should_step(event)` guards: only step on user MessageAction, incoming Observations (not null/state-change), or delegation events.

### Existing agents
- `CodeActAgent` — main, code + bash + browser
- `BrowsingAgent` — web browsing focused
- `VerifierAgent` — task completion validation
- `RepoStudyAgent` — repository analysis
- `DummyAgent`, `LocAgent`, `ReadonlyAgent`, `VisualBrowsingAgent`

## 5. Session Persistence

### Files
- `openhands/server/session/agent_session.py` — restore logic
- `openhands/storage/conversation/file_conversation_store.py` — metadata store
- `openhands/controller/state/state.py` — State serialization
- `openhands/events/event_store.py` — Event replay

### Persistence layers (two separate things)

**State pickle:** `State` is pickled + base64-encoded → written to FileStore. Contains: iteration count, budget flags, agent state enum, user/session IDs, metrics. History list is NOT pickled (reconstructed from event store). `__setstate__` handles schema migrations.

**Event store:** Individual JSON files per event + page cache files (25/page). Named by event ID. These are the source of truth for replay.

### Resume flow
```python
# On session restart:
restored_state = State.restore_from_session(sid, file_store, user_id)
# If event_stream.get_latest_event_id() > 0 but restore fails → warning
# Controller restores from state + replays events from event_store
```

Resumable states: RUNNING, PAUSED, AWAITING_USER_INPUT, FINISHED. On restore, agent moves to LOADING first.

Conversation metadata (title, timestamps, config) stored separately in JSON via `FileConversationStore`. Pydantic model, handles deprecated field removal on load.

**V1 (new):** `ConversationState` = Pydantic model; metadata in `base_state.json`; events in individual files via `EventStore`. Lock-based FIFO for thread-safe writes. Recovery = load `base_state.json` + replay events from directory.

## Claude Code Adaptation Notes

### What's directly portable
1. **StuckDetector patterns** — implement as a Claude Code hook (PostToolUse) that counts consecutive identical tool calls. Thresholds: 4× same action+result, 3× same error, 10× condensation loop.
2. **Condenser trigger** — track token count in `WORKING.md`; at threshold, run a summarization pass before the next task.
3. **Event log** — append-only JSONL to a session file (already partially done in `~/.claude/history.jsonl`).

### What doesn't map cleanly
- **step(state)→action** is the entire Claude Code interface already (each turn IS a step). No separate abstraction needed.
- **Docker per session** is unnecessary for a single-user setup; the sandbox already exists (macOS + Claude Code hooks).
- **AgentController loop** is Claude Code itself.

### Useful ideas to extract
- **Pending action tracking** — "don't step until observation arrives" could translate to: don't start new autonomous task until previous background task completes. Track in WORKING.md.
- **Registry pattern for agents** — could use the skill system as an equivalent: `/delegate-to <skill>` dispatches to named implementations.
- **Structured loop recovery options** — when Claude Code detects it's repeating, offer 3 options: rollback to last checkpoint, retry from last user message, stop.
