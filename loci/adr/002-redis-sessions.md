# ADR-002: Redis Session Management

**Status:** Accepted
**Date:** 2026-01-24
**Context:** Banking FAQ chatbot production deployment

---

## Context and Problem Statement

The current prototype uses in-memory dictionaries for session state (language preference, conversation history). This works for single-instance development but breaks in production:

**Production environment**:
- Railway (or on-prem) runs multiple backend instances behind a load balancer
- Requests from the same user may route to different instances
- In-memory state is not shared across instances

**Impact**:
- Session loss: User's language preference resets mid-conversation
- No conversation continuity: Each request treated as new session
- Restart/deployment wipes all sessions

## Decision

Migrate session storage from in-memory dictionaries to **Redis** with 30-minute TTL.

### Implementation
```python
import redis
import json

session_store = redis.Redis(
    host='<redis-host>',
    port=6379,
    db=0,
    decode_responses=True
)

# Store session
session_store.setex(
    f"session:{session_id}",
    1800,  # 30-minute TTL
    json.dumps(session_data)
)

# Retrieve session
session_json = session_store.get(f"session:{session_id}")
session_data = json.loads(session_json) if session_json else None
```

## Considered Alternatives

### Alternative 1: Sticky Sessions (Load Balancer Configuration)
**Approach**: Configure load balancer to route same user to same instance
**Pros**: No code changes, keeps in-memory state
**Cons**:
- Doesn't survive instance restarts/deployments
- Uneven load distribution (users stick to one instance)
- Doesn't work with Railway's default routing

**Why rejected**: Still loses sessions on deployment, violates stateless design.

### Alternative 2: Cookie-Based Sessions (Encrypted Client-Side Storage)
**Approach**: Store session state in encrypted cookies
**Pros**: Stateless backend, no DB dependency
**Cons**:
- Size limit (4KB cookie max) - conversation history may exceed
- Security concerns (even encrypted, client can delete/modify)
- Not suitable for server-side conversation memory

**Why rejected**: Banking app needs server-side session storage for audit trail.

### Alternative 3: PostgreSQL Sessions (Rails-Style)
**Approach**: Store sessions in PostgreSQL with ActiveRecord-style table
**Pros**: Persistent, transaction support, familiar SQL
**Cons**:
- Slower than Redis for ephemeral session data (30-minute TTL)
- Requires additional DB (or adds load to main DB)
- Overkill for simple key-value storage

**Why rejected**: Redis is purpose-built for ephemeral session storage.

### Alternative 4: Memcached
**Approach**: Similar to Redis, but simpler key-value cache
**Pros**: Faster than Redis for pure caching
**Cons**:
- No persistence (restarts lose all sessions)
- No TTL per key (global eviction policy only)
- Less feature-rich (no pub/sub for future needs)

**Why rejected**: Redis provides better guarantees and future flexibility.

## Rationale

### Why Redis
1. **Purpose-built for sessions**: Key-value store with TTL, fast reads/writes
2. **Production-proven**: Industry standard for session management
3. **Persistence**: Optional RDB/AOF for session recovery after restarts
4. **Multi-instance support**: Shared state across all backend instances
5. **Future-proof**: Pub/sub for real-time features, caching for embeddings

### Why 30-Minute TTL
- **User pattern**: Banking FAQ sessions are short (3-5 questions typical)
- **Balance**: Long enough for multi-question conversations, short enough to prevent memory bloat
- **Industry standard**: Most web sessions use 15-30 minutes
- **Auto-cleanup**: Expired sessions removed automatically

### Deployment Options
**Option A: Cloud Redis (Railway/Upstash)**
- Pros: Managed, zero ops, automatic backups
- Cons: Cost (~$10-30/month), data leaves on-prem

**Option B: On-Prem Redis**
- Pros: Data stays on-prem, lower cost (just compute)
- Cons: Requires ops team support, manual backups

**Decision deferred**: Depends on bank's security requirements (on-prem mandate?).

## Consequences

### Positive
- ✅ Multi-instance deployment support
- ✅ Session persistence across restarts/deployments
- ✅ Automatic cleanup (TTL)
- ✅ Foundation for future caching (embedding results, FAQ lookups)

### Negative
- ❌ Adds infrastructure dependency (Redis must be running)
- ❌ Network latency for session lookups (~1-5ms per request)
- ❌ Serialization overhead (JSON encode/decode)

### Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Redis down → all sessions lost | Service degradation | Graceful fallback: Treat as new session, warn user |
| Redis memory full → eviction | Session loss for active users | Monitor memory, set max memory policy (allkeys-lru) |
| Network latency → slower responses | +1-5ms per request | Acceptable for 2s p95 target |

## Migration Plan

### Phase 1: Implement Redis Adapter (2 days)
1. Install `redis-py`: `pip install redis`
2. Create `services/redis_session_store.py` wrapper
3. Implement session CRUD (create, read, update, delete)
4. Add TTL extension on each access (sliding window)

### Phase 2: Replace In-Memory Sessions (1 day)
1. Update `services/session_manager.py` to use Redis adapter
2. Migrate existing session schema (language, history, metadata)
3. Add fallback: If Redis unavailable, treat as new session (log warning)

### Phase 3: Testing (1 day)
1. Unit tests: Session CRUD, TTL expiry, serialization
2. Integration tests: Multi-instance load balancer test
3. Chaos test: Redis restart during active sessions

## Validation

### Success Criteria
- ✅ Same user's requests to different instances maintain session state
- ✅ Language preference persists across 30-minute conversation
- ✅ Deployment/restart does not lose active sessions
- ✅ Expired sessions removed automatically (no manual cleanup)

### Test Scenarios
1. **Multi-instance continuity**: User asks 3 questions, each routes to different instance → Same language maintained
2. **TTL extension**: User active for 45 minutes (queries every 10 min) → Session never expires (sliding window)
3. **TTL expiry**: User inactive for 31 minutes → Session expired, language re-detected on next query
4. **Redis restart**: Restart Redis, active users continue with new sessions (logged as "session not found")

## Monitoring

### Metrics to Track
- **Session creation rate**: Queries/hour creating new sessions
- **Session hit rate**: % of queries with existing session (should be >70%)
- **Redis memory usage**: Monitor approach to max memory limit
- **Session TTL distribution**: Histogram of session lifetimes (how long users stay)

### Alerts
- 🚨 **Redis down**: Alert on connection failures, page on-call
- 🚨 **Memory >80%**: Alert before eviction policy kicks in
- ⚠️ **Session hit rate <50%**: Investigate TTL too short or users not returning

## References

- **Problem identified by**: Performance oracle agent, architecture strategist agent
- **Industry best practices**: [Redis Session Store Best Practices](https://redis.io/docs/manual/keyspace/)
- **Alternative patterns**: [12-Factor App: Session Management](https://12factor.net/)
