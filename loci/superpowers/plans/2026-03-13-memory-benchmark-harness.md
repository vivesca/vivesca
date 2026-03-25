# docima — AI Agent Memory Benchmark Harness

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified CLI (`docima`) that benchmarks 10 AI agent memory backends through a common interface, using real daily workflow data over a 2-week experiment.

**Architecture:** Python CLI with adapter pattern. Each backend implements `add()`, `query()`, `inspect()`. A harness layer runs identical operations across all backends and logs results. Backends are lazy-loaded — only instantiated when called. Data collection is passive (hooks replicate MEMORY.md changes to all backends automatically).

**Tech Stack:** Python 3.11+, uv, click, sentence-transformers (local embeddings), Ollama (local LLM for entity extraction), Kuzu (embedded graph).

**CLI name:** `docima` (Greek: "mindful/remembering" — available on crates.io)

---

## Backends (10)

| # | Backend | Hypothesis | Key dependency |
|---|---------|------------|---------------|
| 0 | markdown + grep | Curated text is enough | (none) |
| 1 | Graphiti + Kuzu | Temporal knowledge graph adds value | `graphiti-core[kuzu,sentence-transformers]` |
| 2 | Mem0 | Market leader justifies adoption | `mem0ai` |
| 3 | Cognee | Document graph enables multi-hop | `cognee[ollama,baml]` |
| 4 | Letta | Self-managing memory beats external | `letta-client` (server at :8283) |
| 5 | LangMem | Procedural memory (self-modifying prompts) | `langmem`, `langgraph` |
| 6 | MemoryScope | Bilingual design produces different results | `memoryscope` |
| 7 | SQLite-vec | Zero-infra floor — is this good enough? | `sqlite-vec` |
| 8 | pgvector | Existing bank infra is sufficient | `psycopg[binary]`, `pgvector` |
| 9 | Neo4j raw | How much value does Graphiti add over bare graph? | `neo4j` |

**Line-drawing principle:** One backend per distinct hypothesis. Adding backend 11 requires articulating a hypothesis not tested by 0-9. The adapter pattern makes future additions trivial (one file).

---

## Experimental Protocol

### Phase 0: Build (Days -2 to 0)
Build the CLI and all 10 backend adapters. Delegated — see Delegation Strategy below.

### Phase 1: Seed (Day 1)
```bash
# Import identical seed data to all backends
docima import ~/.claude/projects/-Users-terry/memory/MEMORY.md --backend all
docima import ~/docs/solutions/ --backend all --format directory
docima benchmark --quick  # smoke test: 10 facts, 5 queries
```
Record: initial memory count, seed latency per backend, baseline benchmark scores.

### Phase 2: Passive Collection (Days 2-14)
**User changes nothing.** MEMORY.md + grep remains the primary system.

**Automated hooks:**
- Claude Code PostToolUse hook on MEMORY.md writes → `docima add "<new entry>" --backend all --silent`
- Nightly legatus job: `docima benchmark --daily` — runs standard query battery, logs to `~/.local/share/docima/results/YYYY-MM-DD.json`
- Nightly: `docima drift` — compares what each backend returns for the same 10 standard queries, logs divergence

**What we measure daily:**
| Metric | How |
|--------|-----|
| Add latency (p50, p95) | Timed during hook replication |
| Query latency (p50, p95) | Timed during nightly benchmark |
| Recall@5 | Does the correct answer appear in top 5 results? |
| Precision@5 | What fraction of top 5 results are relevant? |
| Memory count | `docima count --backend all` |
| Divergence score | How differently do backends rank the same query? |
| Storage size | Disk usage per backend |

### Phase 3: Blind Evaluation (Day 15)
```bash
docima eval --blind
# Presents 20 queries, shows retrieval results from random backends without labels
# User rates each result set: 1-5 quality score
# Reveals backend labels after rating
```

### Phase 4: Analysis + Write-up (Day 16)
```bash
docima report
# Generates comparison table from 14 days of logged data
# Outputs: markdown table, JSON, and chart-ready CSV
```

**Outputs:**
1. Garden post — "I Ran 10 Memory Backends for 2 Weeks. Here's What Actually Matters."
2. Capco whitepaper — "Memory Architecture for Enterprise AI Agents" (with empirical data)
3. Consulting demo — live `docima query --backend all` in client meetings
4. Possibly: conference talk, arXiv preprint

### Controls & Fairness
- All backends receive identical inputs (same hook, same timestamp)
- Embedding model is consistent across raw DB backends (sentence-transformers `all-MiniLM-L6-v2`)
- Framework backends use their own extraction/embedding (that's part of what we're testing)
- Markdown baseline uses keyword grep (no embeddings) — deliberately unfair, tests whether embeddings even matter for small memory stores

### Known Biases to Acknowledge
- Data is text-heavy (extracted from markdown) — may favour text-native backends
- Memory store is small (~200 entries over 2 weeks) — doesn't test scale
- Single user, single domain — not generalisable without further study
- Passive replication means frameworks that benefit from richer input (e.g., full conversation context for Letta) are disadvantaged

---

## Chunk 1: Core Architecture + Baseline Backend

### Task 1: Project scaffold

**Files:**
- Create: `~/code/docima/pyproject.toml`
- Create: `~/code/docima/src/docima/__init__.py`
- Create: `~/code/docima/src/docima/cli.py`
- Create: `~/code/docima/src/docima/backend.py`
- Create: `~/code/docima/src/docima/types.py`
- Create: `~/code/docima/src/docima/registry.py`
- Create: `~/code/docima/src/docima/config.py`

- [ ] **Step 1: Create project with uv**

```bash
cd ~/code && uv init docima --lib
cd docima
```

- [ ] **Step 2: Define pyproject.toml**

```toml
[project]
name = "docima"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
    "tabulate>=0.9",
]

[project.optional-dependencies]
graphiti = ["graphiti-core[kuzu,sentence-transformers]"]
mem0 = ["mem0ai"]
cognee = ["cognee[ollama,baml]"]
letta = ["letta-client"]
langmem = ["langmem", "langgraph"]
memoryscope = ["memoryscope"]
sqlite-vec = ["sqlite-vec"]
pgvector = ["psycopg[binary]", "pgvector"]
neo4j = ["neo4j"]
embeddings = ["sentence-transformers"]
all = ["docima[graphiti,mem0,cognee,letta,langmem,memoryscope,sqlite-vec,pgvector,neo4j,embeddings]"]

[project.scripts]
docima = "docima.cli:main"
```

- [ ] **Step 3: Define base types**

```python
# src/docima/types.py
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Memory:
    content: str
    backend: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    score: float | None = None

@dataclass
class QueryResult:
    memories: list[Memory]
    latency_ms: float
    backend: str
```

- [ ] **Step 4: Define abstract backend interface**

```python
# src/docima/backend.py
from abc import ABC, abstractmethod
from docima.types import Memory, QueryResult

class MemoryBackend(ABC):
    name: str

    @abstractmethod
    async def add(self, content: str, metadata: dict | None = None) -> Memory: ...

    @abstractmethod
    async def query(self, query: str, limit: int = 10) -> QueryResult: ...

    @abstractmethod
    async def inspect(self, limit: int = 10) -> list[Memory]: ...

    @abstractmethod
    async def clear(self) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def setup(self) -> None:
        """One-time init (create tables, indices, etc.)."""
        ...
```

- [ ] **Step 5: Define backend registry with lazy loading**

```python
# src/docima/registry.py
BACKENDS: dict[str, str] = {
    "markdown": "docima.backends.markdown.MarkdownBackend",
    "graphiti": "docima.backends.graphiti_backend.GraphitiBackend",
    "mem0": "docima.backends.mem0_backend.Mem0Backend",
    "cognee": "docima.backends.cognee_backend.CogneeBackend",
    "letta": "docima.backends.letta_backend.LettaBackend",
    "langmem": "docima.backends.langmem_backend.LangMemBackend",
    "memoryscope": "docima.backends.memoryscope_backend.MemoryScopeBackend",
    "sqlite-vec": "docima.backends.sqlite_vec_backend.SqliteVecBackend",
    "pgvector": "docima.backends.pgvector_backend.PgvectorBackend",
    "neo4j": "docima.backends.neo4j_backend.Neo4jBackend",
}

def load_backend(name: str) -> "MemoryBackend":
    import importlib
    if name not in BACKENDS:
        raise ValueError(f"Unknown backend: {name}. Available: {list(BACKENDS.keys())}")
    module_path, class_name = BACKENDS[name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()
```

- [ ] **Step 6: Write CLI skeleton**

Core commands: `add`, `query`, `inspect`, `backends`, `benchmark`, `import`, `eval`, `report`, `count`, `drift`.

```python
# src/docima/cli.py
import asyncio
import click
from docima.registry import load_backend, BACKENDS

@click.group()
def main():
    """docima — AI agent memory benchmark harness."""
    pass

@main.command()
@click.argument("content")
@click.option("--backend", "-b", default="markdown", help="Backend name or 'all'")
@click.option("--silent", is_flag=True, help="Suppress output (for hooks)")
def add(content: str, backend: str, silent: bool):
    """Add a memory to one or all backends."""
    async def _add():
        targets = BACKENDS.keys() if backend == "all" else [backend]
        for name in targets:
            try:
                b = load_backend(name)
                await b.setup()
                await b.add(content)
                if not silent:
                    click.echo(f"  [{name}] added")
            except Exception as e:
                if not silent:
                    click.echo(f"  [{name}] error: {e}")
    asyncio.run(_add())

@main.command()
@click.argument("query_text")
@click.option("--backend", "-b", default="markdown", help="Backend name or 'all'")
@click.option("--limit", "-n", default=5)
def query(query_text: str, backend: str, limit: int):
    """Query memories from one or all backends."""
    async def _query():
        if backend == "all":
            from tabulate import tabulate
            rows = []
            for name in BACKENDS:
                try:
                    b = load_backend(name)
                    await b.setup()
                    result = await b.query(query_text, limit=limit)
                    top = result.memories[0].content[:60] if result.memories else "(empty)"
                    rows.append([name, len(result.memories), f"{result.latency_ms:.0f}ms", top])
                except Exception as e:
                    rows.append([name, "ERR", "-", str(e)[:60]])
            click.echo(tabulate(rows, headers=["Backend", "Results", "Latency", "Top Result"]))
        else:
            b = load_backend(backend)
            await b.setup()
            result = await b.query(query_text, limit=limit)
            for m in result.memories:
                click.echo(f"  [{m.score or '-'}] {m.content}")
            click.echo(f"  ({result.latency_ms:.0f}ms, {len(result.memories)} results)")
    asyncio.run(_query())

@main.command()
def backends():
    """List available backends and installation status."""
    for name in sorted(BACKENDS):
        try:
            load_backend(name)
            click.echo(f"  + {name}")
        except Exception:
            click.echo(f"  - {name} (not installed)")
```

- [ ] **Step 7: Commit scaffold**

```bash
git add -A && git commit -m "feat: docima scaffold — CLI + backend interface + registry"
```

### Task 2: Backend 0 — Markdown + grep (baseline)

**Files:**
- Create: `~/code/docima/src/docima/backends/__init__.py`
- Create: `~/code/docima/src/docima/backends/markdown.py`
- Create: `~/code/docima/tests/test_markdown.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_markdown.py
import pytest
import asyncio
from docima.backends.markdown import MarkdownBackend

@pytest.fixture
def backend(tmp_path):
    return MarkdownBackend(path=tmp_path / "test-memory.md")

def test_add_and_query(backend):
    async def _test():
        await backend.setup()
        await backend.add("Alice is CTO of Acme Corp")
        await backend.add("Bob prefers async communication")
        result = await backend.query("CTO")
        assert len(result.memories) >= 1
        assert "Alice" in result.memories[0].content
    asyncio.run(_test())

def test_count(backend):
    async def _test():
        await backend.setup()
        assert await backend.count() == 0
        await backend.add("fact one")
        assert await backend.count() == 1
    asyncio.run(_test())
```

- [ ] **Step 2: Run test — verify fails**

```bash
cd ~/code/docima && uv run pytest tests/test_markdown.py -v
# Expected: ImportError — MarkdownBackend doesn't exist yet
```

- [ ] **Step 3: Implement MarkdownBackend**

```python
# src/docima/backends/markdown.py
import re
import time
from datetime import datetime
from pathlib import Path
from docima.backend import MemoryBackend
from docima.types import Memory, QueryResult

class MarkdownBackend(MemoryBackend):
    name = "markdown"

    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".local/share/docima/memories.md"

    async def setup(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("# Mnemon Memories\n\n")

    async def add(self, content: str, metadata: dict | None = None) -> Memory:
        ts = datetime.now()
        entry = f"- [{ts:%Y-%m-%d %H:%M}] {content}\n"
        with open(self.path, "a") as f:
            f.write(entry)
        return Memory(content=content, backend=self.name, timestamp=ts, metadata=metadata or {})

    async def query(self, query: str, limit: int = 10) -> QueryResult:
        start = time.monotonic()
        pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None
        memories = []
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                ts_match = re.match(r"- \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] (.+)", line)
                if ts_match and (pattern is None or pattern.search(line)):
                    memories.append(Memory(
                        content=ts_match.group(2),
                        backend=self.name,
                        timestamp=datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M"),
                    ))
        elapsed = (time.monotonic() - start) * 1000
        return QueryResult(memories=memories[:limit], latency_ms=elapsed, backend=self.name)

    async def inspect(self, limit: int = 10) -> list[Memory]:
        result = await self.query("", limit=9999)
        return result.memories[-limit:]

    async def clear(self):
        if self.path.exists():
            self.path.write_text("# Mnemon Memories\n\n")

    async def count(self) -> int:
        if not self.path.exists():
            return 0
        return sum(1 for line in self.path.read_text().splitlines() if line.startswith("- ["))
```

- [ ] **Step 4: Run test — verify passes**

```bash
cd ~/code/docima && uv run pytest tests/test_markdown.py -v
# Expected: 2 passed
```

- [ ] **Step 5: Smoke test CLI**

```bash
cd ~/code/docima && uv run docima add "test fact" -b markdown
uv run docima query "test" -b markdown
uv run docima inspect -b markdown
uv run docima backends
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: markdown backend (baseline) + tests"
```

---

## Chunk 2: Framework Backends (Graphiti, Mem0, Cognee, Letta, LangMem, MemoryScope)

Each backend follows the same contract: implement `MemoryBackend`, write test, verify. These are **independent files — fully parallelisable**.

### Task 3: Backend 1 — Graphiti + Kuzu

**Files:**
- Create: `src/docima/backends/graphiti_backend.py`
- Create: `tests/test_graphiti.py`

**Key details:**
- `pip install graphiti-core[kuzu,sentence-transformers]`
- Kuzu is embedded (no server). DB path: `~/.local/share/docima/graphiti.kuzu`
- Local embeddings: sentence-transformers `all-MiniLM-L6-v2`
- LLM for entity extraction: Ollama via `OpenAIGenericClient` (needs 14B+ model — small models fail JSON extraction)
- Wrap `add_episode()` → `add()`, `search()` → `query()`

- [ ] **Step 1:** Write test (same add/query/count contract)
- [ ] **Step 2:** Implement adapter
- [ ] **Step 3:** Verify tests pass
- [ ] **Step 4:** Commit

### Task 4: Backend 2 — Mem0

**Files:**
- Create: `src/docima/backends/mem0_backend.py`
- Create: `tests/test_mem0.py`

**Key details:**
- For local: configure Qdrant + Ollama embeddings (no OpenAI calls)
- For cloud: `MEM0_API_KEY` env var
- **Gotcha:** "local" mode still phones home for embeddings unless explicitly configured with local embedder

- [ ] **Steps 1-4:** Same pattern

### Task 5: Backend 3 — Cognee

**Files:**
- Create: `src/docima/backends/cognee_backend.py`
- Create: `tests/test_cognee.py`

**Key details:**
- Default local stack: SQLite + LanceDB + Kuzu (no external DB needed)
- **Gotcha:** Set BOTH LLM and embedding config — partial config silently falls back to OpenAI
- **Gotcha:** `[baml]` extra required for Ollama (undocumented but practically necessary)
- `cognify()` is expensive — batch adds, trigger cognify on `setup()` or explicit command

- [ ] **Steps 1-4:** Same pattern

### Task 6: Backend 4 — Letta

**Files:**
- Create: `src/docima/backends/letta_backend.py`
- Create: `tests/test_letta.py`

**Key details:**
- Letta is a **server**, not a library. Requires `letta server` running at localhost:8283
- Memory is agent-scoped — create one "docima" agent on first `setup()`, reuse its ID
- Store via archival memory (`client.agents.archival.insert()`), retrieve via archival search
- Tests should `@pytest.mark.skipif` when server is unreachable
- **Gotcha:** SQLite schema migrations not supported between Letta versions

- [ ] **Steps 1-4:** Same pattern

### Task 7: Backend 5 — LangMem

**Files:**
- Create: `src/docima/backends/langmem_backend.py`
- Create: `tests/test_langmem.py`

**Key details:**
- Three memory types: semantic, episodic, procedural. Use semantic for this adapter.
- **Gotcha:** Default storage is in-memory (lost on restart). Use SQLiteStore or PostgresStore for persistence.
- Requires LangGraph runtime + embedding model

- [ ] **Steps 1-4:** Same pattern

### Task 8: Backend 6 — MemoryScope

**Files:**
- Create: `src/docima/backends/memoryscope_backend.py`
- Create: `tests/test_memoryscope.py`

**Key details:**
- Alibaba/Tongyi Lab. Docs may be Chinese-first — delegate should search GitHub issues + Chinese dev blogs if stuck
- Bilingual (Chinese + English) — test with both languages in corpus

- [ ] **Steps 1-4:** Same pattern

- [ ] **Chunk 2 commit:**

```bash
git add -A && git commit -m "feat: framework backends — graphiti, mem0, cognee, letta, langmem, memoryscope"
```

---

## Chunk 3: Database Backends (SQLite-vec, pgvector, Neo4j) + Shared Embeddings

These are "raw" backends — no framework, just DB with vector/graph operations. They share a common embedding step.

### Task 9: Shared embedding helper

**Files:**
- Create: `src/docima/embeddings.py`

```python
from sentence_transformers import SentenceTransformer

_model = None

def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(text: str) -> list[float]:
    return get_embedder().encode(text).tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts).tolist()
```

### Task 10: Backend 7 — SQLite-vec

**Files:**
- Create: `src/docima/backends/sqlite_vec_backend.py`
- Create: `tests/test_sqlite_vec.py`

**Key details:**
- DB path: `~/.local/share/docima/sqlite.db`
- Use shared `embed()` for consistent comparison
- Schema: `memories(id, content, timestamp, embedding vec[384])`

- [ ] **Steps 1-4:** test → implement → verify → commit

### Task 11: Backend 8 — pgvector

**Files:**
- Create: `src/docima/backends/pgvector_backend.py`
- Create: `tests/test_pgvector.py`

**Key details:**
- Requires local PostgreSQL with `pgvector` extension
- DSN from config: `postgresql://localhost/docima`
- Tests should `@pytest.mark.skipif` when Postgres is unreachable

- [ ] **Steps 1-4:** Same pattern

### Task 12: Backend 9 — Neo4j raw

**Files:**
- Create: `src/docima/backends/neo4j_backend.py`
- Create: `tests/test_neo4j.py`

**Key details:**
- Requires local Neo4j (Docker: `docker run -p 7687:7687 neo4j:5`)
- No Graphiti framework — raw Cypher queries for nodes + relationships
- Tests what Graphiti adds over DIY graph memory
- Schema: `(:Memory {content, timestamp, embedding})` with cosine similarity for retrieval

- [ ] **Steps 1-4:** Same pattern

- [ ] **Chunk 3 commit:**

```bash
git add -A && git commit -m "feat: database backends — sqlite-vec, pgvector, neo4j-raw + shared embeddings"
```

---

## Chunk 4: Benchmark Harness + Experiment Infrastructure

### Task 13: Standard test corpus

**Files:**
- Create: `data/corpus.yaml`
- Create: `data/queries.yaml`

50 facts spanning: people/roles, regulations, preferences, metrics, dates, technical decisions, bilingual content.
20 queries with expected retrieval targets and difficulty ratings (exact match, semantic, multi-hop, temporal).

- [ ] **Step 1:** Write corpus file
- [ ] **Step 2:** Write queries file with expected answers

### Task 14: Benchmark runner

**Files:**
- Create: `src/docima/benchmark.py`
- Create: `tests/test_benchmark.py`

Commands:
```bash
docima benchmark --quick          # 10 facts, 5 queries — smoke test
docima benchmark --full           # full corpus + all queries
docima benchmark --daily          # nightly automated run, append to results log
docima benchmark --corpus X --queries Y  # custom corpus
```

Output: JSON to `~/.local/share/docima/results/YYYY-MM-DD.json` + human-readable table to stdout.

- [ ] **Steps 1-4:** test → implement → verify → commit

### Task 15: Drift detector

**Files:**
- Create: `src/docima/drift.py`

```bash
docima drift
# Runs 10 standard queries against all backends
# Compares ranking order — how differently do backends rank the same query?
# Outputs: divergence matrix (which backends agree/disagree most)
```

- [ ] **Steps 1-4:** Same pattern

### Task 16: Blind evaluator

**Files:**
- Create: `src/docima/eval.py`

```bash
docima eval --blind
# Interactive: presents query + results from random backend (no label)
# User rates 1-5
# After all queries: reveals labels + aggregates scores per backend
```

- [ ] **Steps 1-4:** Same pattern

### Task 17: Report generator

**Files:**
- Create: `src/docima/report.py`

```bash
docima report
# Reads all results from ~/.local/share/docima/results/
# Generates: markdown comparison table, JSON summary, chart-ready CSV
# Includes: latency trends, recall@5, precision@5, divergence, blind eval scores
```

- [ ] **Steps 1-4:** Same pattern

- [ ] **Chunk 4 commit:**

```bash
git add -A && git commit -m "feat: benchmark harness — corpus, runner, drift, eval, report"
```

---

## Chunk 5: Experiment Setup + Polish

### Task 18: Config file

**Files:**
- Create: `src/docima/config.py`

```yaml
# ~/.config/docima/config.yaml
default_backend: markdown
data_dir: ~/.local/share/docima
backends:
  graphiti:
    db_path: ~/.local/share/docima/graphiti.kuzu
    llm: ollama/qwen2.5:14b
    embedder: sentence-transformers/all-MiniLM-L6-v2
  mem0:
    mode: local
  letta:
    server_url: http://localhost:8283
  pgvector:
    dsn: postgresql://localhost/docima
  neo4j:
    uri: bolt://localhost:7687
    auth: [neo4j, password]
```

### Task 19: Import command

```bash
docima import <file-or-dir> --backend all
# Parses markdown files, extracts entries, adds to all backends
# Supports: single .md file, directory of .md files
```

### Task 20: MEMORY.md replication hook

**Files:**
- Create: `~/.claude/hooks/docima-replicate.py` (PostToolUse hook)

Trigger: when Edit/Write tool modifies `MEMORY.md`, extract new entries and run `docima add --backend all --silent`.

### Task 21: Nightly legatus job

Add to `~/code/epigenome/chromatin/agent-queue.yaml`:
```yaml
- name: docima-benchmark
  enabled: true
  backend: opencode
  timeout: 600
  schedule: "02:50 daily"
  prompt: |
    Run the nightly docima benchmark.
    cd ~/code/docima && uv run docima benchmark --daily
    Then run: uv run docima drift
    Check exit codes. If any backend errors, note which ones.
    Write nothing — output goes to ~/.local/share/docima/results/ automatically.
```

### Task 22: GitHub repo + companion skill

- [ ] **Step 1: Create private repo**

```bash
cd ~/code/docima && git init && git add -A && git commit -m "init: docima"
gh repo create terry-li-hm/docima --private --source . --push
```

- [ ] **Step 2: Create companion skill**

```bash
mkdir -p ~/skills/docima
# Write SKILL.md with: commands, backend list, experiment protocol, gotchas
cd ~/skills && git add docima/SKILL.md && git commit -m "feat: add docima skill" && git push
```

- [ ] **Chunk 5 commit:**

```bash
git add -A && git commit -m "feat: experiment infrastructure — config, import, hook, legatus job, skill"
```

---

## Delegation Strategy

| Chunk | Delegate | Rationale |
|-------|----------|-----------|
| 1 (scaffold + markdown) | Gemini | Clear spec, Python, single-file |
| 2 (6 framework backends) | 6 parallel Gemini/Codex | Independent files, one per backend |
| 3 (3 DB backends + embeddings) | 3 parallel Gemini | Independent files, shared embedding helper built first |
| 4 (benchmark harness) | Gemini | Multi-file but sequential (runner depends on corpus) |
| 5 (experiment setup) | In-session | Config, hooks, legatus — orchestration work |

**Chunk 1 must complete first** (scaffold provides the interface for all backends).
**Chunks 2 and 3 are fully parallelisable** — 9 independent backend files.
**Chunk 4 depends on at least 2 backends being functional** (needs real data to test).

---

## Success Criteria

1. `docima backends` shows `+` for all 10 backends
2. `docima add "fact" -b all` writes to every backend without error
3. `docima query "fact" -b all` returns comparison table with latency
4. `docima benchmark --quick` completes across all installed backends
5. `docima drift` produces divergence matrix
6. `docima eval --blind` runs interactive blind evaluation
7. `docima report` generates publishable comparison table
8. 14 days of nightly benchmark data collected automatically
9. Results inform garden post + Capco whitepaper

---

## Open Questions (for consilium review)

1. Is 2 weeks enough for meaningful results?
2. Is passive collection (replicate from MEMORY.md) fair to all backends?
3. Should we incorporate established benchmarks (LoCoMo, LongMemEval) alongside custom corpus?
4. What metrics beyond latency/recall matter?
5. Is this publishable (arXiv, conference)?
6. Biggest risk that could make the experiment worthless?
