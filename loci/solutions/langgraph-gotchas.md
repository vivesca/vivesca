# LangGraph Gotchas

## LRN-20260312-001: interrupt() behavior changed in LangGraph 1.1

In LangGraph 1.0, `interrupt()` inside a node caused `ainvoke()` to raise `GraphInterrupt`.
In LangGraph 1.1+, `ainvoke()` **returns normally** with `__interrupt__` key in the result dict.

```python
result = await graph.ainvoke(state, config=config)
interrupted = bool(result.get("__interrupt__"))  # ← correct for 1.1+
findings = result.get("findings", [])
```

Catching `GraphInterrupt` by exception name silently fails — `ainvoke()` never raises, so the except block is never hit and `interrupted` stays False.

## LRN-20260312-002: services in GapState break MemorySaver checkpointing

MemorySaver serialises the entire state via msgpack on every checkpoint. Non-serialisable objects (VectorStore, LLMService, MagicMock in tests) cause `TypeError` at checkpoint time.

Fix: remove service objects from TypedDict state entirely. Pass via `config["configurable"]` — LangGraph never serialises configurable. Access inside nodes with `get_config()["configurable"]`.

```python
from langgraph.config import get_config

async def my_node(state):
    cfg = get_config()["configurable"]
    vector_store = cfg["vector_store"]
```

## LRN-20260312-003: claude-sonnet-4.6 appends trailing content after JSON

The model sometimes outputs valid JSON followed by a newline and explanation text. `json.loads()` raises `JSONDecodeError: Extra data`. Fix: use `raw_decode` which stops at the first complete JSON value, and trim to the first `{` first (model may prepend a list like `[0]` before the object).

```python
brace_idx = text.find('{')
if brace_idx > 0:
    text = text[brace_idx:]
try:
    obj, _ = json.JSONDecoder().raw_decode(text)
    return json.dumps(obj)
except json.JSONDecodeError:
    return text
```
