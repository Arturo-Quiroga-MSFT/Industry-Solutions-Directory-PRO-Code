

## Root Causes of 3–60s Latency

Your pipeline runs **4 sequential LLM calls** before the user sees anything:

| Step | Agent | Model | Purpose |
|------|-------|-------|---------|
| 1 | Query Planner | gpt-4.1 | Intent classification |
| 2 | NL2SQL | gpt-5.2 (reasoning) | SQL generation |
| 3 | Insight Analyzer | gpt-4.1 | Pattern extraction |
| 4 | Response Formatter | gpt-4.1 + web search | Narrative + sources |

And critically: **the frontend doesn't use the existing SSE streaming endpoint** — it waits for the full JSON response.

---

## Recommendations (ranked by impact)

### 1. Wire up streaming end-to-end (HIGH IMPACT, LOW EFFORT)
The backend already has `/api/query/stream` with SSE. The React frontend only calls `/api/query` via axios. Switching the frontend to consume SSE means users see Agent 4's narrative **token-by-token** while it generates — cutting perceived wait from 60s to ~20s+first-token.

### 2. Send progressive status events (HIGH IMPACT, LOW EFFORT)
Even before Agent 4 streams text, emit SSE status events like `{"phase": "planning"}`, `{"phase": "querying database"}`, `{"phase": "analyzing 47 results"}`. The frontend shows a progress indicator so users know it's working, not stuck.

### 3. Eliminate Agent 1 (Query Planner) for first messages (MEDIUM IMPACT, LOW EFFORT)
The first message in a conversation **always** needs a new SQL query — the planner adds ~2-4s for zero value. Only invoke it on follow-up turns where intent is ambiguous. On first turn, default to `{intent: "query", needs_new_query: true}`.

### 4. Downgrade NL2SQL model (MEDIUM IMPACT, TRIVIAL EFFORT)
Agent 2 uses `gpt-5.2` (a reasoning model). Reasoning models are slower. For NL2SQL against a single denormalized view, `gpt-4.1` with good prompting is likely sufficient and much faster. Set `MODEL_NL2SQL=gpt-4.1` and test quality.

### 5. Cache SQL results for repeated/similar queries (MEDIUM IMPACT, MEDIUM EFFORT)
No caching exists today. Add an LRU cache keyed on normalized SQL — if the same query was run <5 min ago, skip the DB round-trip and re-use results. Even a simple `@lru_cache` or dict-based TTL cache helps.

### 6. Parallelize Agents 3 & 4 (MEDIUM IMPACT, MEDIUM EFFORT)
Currently Agent 4 waits for Agent 3's insights JSON. Instead, start Agent 4's narrative generation concurrently with Agent 3, and inject insights as they arrive (or merge afterward). This saves one full LLM call's latency.

### 7. Remove web search from Agent 4 in non-critical paths (LOW IMPACT, TRIVIAL)
The `web_search_preview` tool in seller mode adds external network calls. Make it optional or async — most queries about the ISD database don't benefit from web results.

### 8. Use `gpt-4.1-mini` or `gpt-4.1-nano` for Agents 1 & 3 (MEDIUM IMPACT, TRIVIAL)
Intent classification and statistics extraction don't need the full gpt-4.1. Smaller models respond 2-5x faster for these structured-output tasks.

---

## Recommended Implementation Order

| Priority | Change | Est. Latency Reduction |
|----------|--------|----------------------|
| **P0** | Wire frontend to SSE streaming endpoint | Perceived: -30-40s |
| **P0** | Progressive status events during pipeline | Perceived: dramatic |
| **P1** | Skip Query Planner on first message | -2-4s actual |
| **P1** | Switch NL2SQL to gpt-4.1 | -5-15s actual |
| **P2** | Use mini models for Agents 1 & 3 | -3-6s actual |
| **P2** | Result caching (LRU + TTL) | -100% for repeat queries |
| **P3** | Parallelize Agents 3 & 4 | -3-5s actual |

Want me to start implementing any of these?