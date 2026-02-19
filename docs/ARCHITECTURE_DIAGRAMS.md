# Architecture Diagrams

**Last Updated:** February 19, 2026
**Architecture Version:** v3.0 — Multi-Agent NL2SQL Pipeline

> ⚠️ **Note:** This document reflects the current production architecture. The previous RAG / Azure AI Search approach has been replaced by the NL2SQL multi-agent pipeline described here.

This document contains visual representations of the Industry Solutions Chat Assistant architecture.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│              React 19 + TypeScript (Vite, Tailwind CSS)          │
│                                                                  │
│  Components:                                                     │
│  • Chat input/output with SSE streaming                         │
│  • Chart and Table tabs for data visualization                  │
│  • Dual mode: Seller (internal) / Customer (external)           │
│  • Conversation export (JSON, Markdown, HTML)                   │
│  • URL-based mode switching (?mode=seller | ?mode=customer)     │
│  • Follow-up question suggestions                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │ POST /api/query/stream (SSE)
                          │ POST /api/query (REST)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 BACKEND API (FastAPI, Python 3.11+)              │
│             Container: Azure Container Apps (Sweden Central)     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ REST / SSE Endpoints                                      │  │
│  │ • POST /api/query/stream  ← SSE streaming (primary)      │  │
│  │ • POST /api/query         ← REST fallback                │  │
│  │ • GET  /api/health                                       │  │
│  │ • GET  /api/examples                                     │  │
│  │ • POST /api/conversation/export                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Multi-Agent Pipeline (multi_agent_pipeline.py)           │  │
│  │                                                          │  │
│  │  Agent 1: QueryPlanner (gpt-4.1)                        │  │
│  │  ├─ analyze_intent()  — classifies user intent          │  │
│  │  └─ Responses API · JSON Schema strict output           │  │
│  │                          │                              │  │
│  │  Agent 2: NL2SQL (gpt-5.2, low reasoning)              │  │
│  │  ├─ generate_sql()    — NL → SQL with phrase precision  │  │
│  │  ├─ execute_sql()     — pyodbc, READ-ONLY               │  │
│  │  └─ Responses API · JSON Schema strict output           │  │
│  │                          │                              │  │
│  │  Agent 3: InsightAnalyzer (gpt-4.1)                    │  │
│  │  ├─ analyze_results() — patterns, stats, citations      │  │
│  │  └─ Dual mode: seller (partner names) / customer mode  │  │
│  │                          │                              │  │
│  │  Agent 4: ResponseFormatter (gpt-4.1)                  │  │
│  │  ├─ format_response_stream() — SSE token-by-token       │  │
│  │  └─ Seller mode: web_search_preview tool enabled        │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────┬───────────────────┘
                        │                     │
                        ▼                     ▼
         ┌──────────────────────┐   ┌──────────────────────────┐
         │  AZURE OPENAI        │   │  SQL SERVER (Production)  │
         │  (Responses API)     │   │  mssoldir-prd-sql         │
         │                      │   │                           │
         │  gpt-4.1             │   │  View:                    │
         │  • Query Planner     │   │  dbo.vw_ISDSolution_All   │
         │  • Insight Analyzer  │   │  • ~5,100+ solutions      │
         │  • Resp. Formatter   │   │  • 174 partners           │
         │                      │   │  • 10 industries          │
         │  gpt-5.2 (reasoning) │   │  • 3 solution areas       │
         │  • NL2SQL Executor   │   │  READ-ONLY via pyodbc     │
         │                      │   │  4-layer SQL validation   │
         │  web_search_preview  │   │                           │
         │  (Seller mode only)  │   │                           │
         └──────────────────────┘   └──────────────────────────┘

         ┌───────────────────────────────────────────────────┐
         │      AZURE COSMOS DB (NoSQL Serverless)           │
         │      Database: industry-solutions-db              │
         │      Container: chat-sessions                     │
         │      • Partition Key: sessionId                   │
         │      • TTL: 90 days                               │
         │                                                   │
         │  Stores:                                          │
         │  • Full conversation history                      │
         │  • User messages + assistant responses            │
         │  • Response IDs (Responses API chaining)         │
         │  • Session metadata                               │
         └───────────────────────────────────────────────────┘
```

---

## Data Flow — Chat Request (Streaming)

```
┌────────┐
│  USER  │
└────┬───┘
     │ 1. Sends question: "What partners offer healthcare AI solutions?"
     ▼
┌──────────────────────────────────────────────────────┐
│  REACT 19 FRONTEND                                   │
│  (Seller or Customer mode)                           │
└──────┬───────────────────────────────────────────────┘
       │ 2. POST /api/query/stream
       │    { "question": "...", "conversation_id": "uuid" }
       ▼
┌──────────────────────────────────────────────────────┐
│  FASTAPI BACKEND                                     │
│                                                       │
│  3. Load conversation history from Cosmos DB         │
│     (previous_response_ids for Responses API chain)  │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  AGENT 1: Query Planner (gpt-4.1)                    │
│  Responses API — JSON Schema strict output            │
│                                                       │
│  4. Classify intent:                                 │
│     {                                                 │
│       "intent": "query",                             │
│       "needs_new_query": true,                       │
│       "query_type": "specific",                      │
│       "reasoning": "User requesting new data"        │
│     }                                                 │
│                                                       │
│  NOTE: Skipped on first turn (always new query)      │
└──────┬───────────────────────────────────────────────┘
       │ → SSE: { "type": "status", "phase": "planning" }
       ▼
┌──────────────────────────────────────────────────────┐
│  AGENT 2: NL2SQL Executor (gpt-5.2, low reasoning)  │
│  Responses API — JSON Schema strict output            │
│                                                       │
│  5. Generate SQL with phrase precision rules:        │
│     SELECT DISTINCT v.solutionName, v.orgName,       │
│       v.industryName, v.solutionAreaName             │
│     FROM dbo.vw_ISDSolution_All AS v                │
│     WHERE v.solutionStatus = 'Approved'             │
│       AND (COALESCE(v.industryName,'')              │
│             LIKE '%healthcare%')                     │
│       AND (COALESCE(v.solutionAreaName,'')          │
│             LIKE '%AI%'                              │
│          OR COALESCE(v.solutionPlayName,'')         │
│             LIKE '%artificial intelligence%')        │
│     ORDER BY v.orgName                               │
│                                                       │
│  6. Validate SQL (4 layers: syntax, read-only,       │
│     injection, schema) then execute via pyodbc       │
└──────┬───────────────────────────────────────────────┘
       │ → SSE: { "type": "status", "phase": "querying_database" }
       ▼
┌──────────────────────────────────────────────────────┐
│  SQL SERVER (mssoldir-prd-sql)                        │
│  dbo.vw_ISDSolution_All — READ-ONLY                  │
│                                                       │
│  7. Returns result rows:                             │
│     [                                                 │
│       { solutionName: "...", orgName: "...",         │
│         industryName: "Healthcare", score: null },   │
│       ...                                             │
│     ]                                                 │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  AGENT 3: Insight Analyzer (gpt-4.1)                 │
│                                                       │
│  8. Compute statistics (partners, industries,        │
│     solution areas) from result set                  │
│                                                       │
│  9. Generate structured insights JSON:               │
│     {                                                 │
│       "overview": "...",                             │
│       "key_findings": [...],                         │
│       "patterns": [...],                             │
│       "statistics": { "top_partners": {...} },       │
│       "follow_up_questions": [...],                  │
│       "citations": [...]                             │
│     }                                                 │
│                                                       │
│  CUSTOMER MODE: removes orgName / partner rankings   │
│  SELLER MODE:   includes partner names & rankings    │
└──────┬───────────────────────────────────────────────┘
       │ → SSE: { "type": "metadata", insights: {...}, data: {...} }
       ▼
┌──────────────────────────────────────────────────────┐
│  AGENT 4: Response Formatter (gpt-4.1)               │
│                                                       │
│  10. Stream executive narrative token-by-token       │
│      SELLER MODE: web_search_preview tool active     │
│      → enriches narrative with real-world news       │
│                                                       │
│  11. Yields SSE delta chunks:                        │
│      { "type": "delta", "content": "The healthcare " }
│      { "type": "delta", "content": "AI landscape..." }
│      ...                                              │
│      { "type": "done",                               │
│        "web_sources": [...],                         │
│        "usage_stats": {...},                         │
│        "elapsed_time": 26.4 }                        │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  FASTAPI BACKEND                                     │
│                                                       │
│  12. Save conversation to Cosmos DB                  │
│      (question, intent, summary, raw_results,        │
│       last_response_id for chaining)                 │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  REACT 19 FRONTEND                                  │
│                                                      │
│  13. Render streaming narrative in chat bubble      │
│      Display data table + charts in tabbed view     │
│      Show follow-up suggestion chips                │
│      Show web source citations (seller mode)        │
└──────┬──────────────────────────────────────────────┘
       │
       ▼
┌────────┐
│  USER  │  Sees a streaming executive narrative + data!
└────────┘
```

---

## Multi-Agent Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-AGENT PIPELINE                           │
│              (multi_agent_pipeline.py)                           │
│                                                                  │
│                                                                  │
│   Question ──────────────────────────────────────────────────┐  │
│                                                               │  │
│   ┌───────────────────────────────────────────────────────┐  │  │
│   │  Agent 1: Query Planner                               │  │  │
│   │  Model: gpt-4.1 (Responses API)                       │  │  │
│   │                                                       │  │  │
│   │  Input:  question + conversation history              │  │  │
│   │  Output: { intent, needs_new_query, query_type }      │  │  │
│   │                                                       │  │  │
│   │  Key logic:                                           │  │  │
│   │  • ALWAYS skipped on first turn (saves ~3s)           │  │  │
│   │  • intent=query ALWAYS forces needs_new_query=true    │  │  │
│   │  • previous_response_id chaining across turns         │  │  │
│   └───────────────────────────────────────────────────────┘  │  │
│                          │ intent info                          │  │
│                          ▼                                      │  │
│   ┌───────────────────────────────────────────────────────┐  │  │
│   │  Agent 2: NL2SQL Executor                             │  │  │
│   │  Model: gpt-5.2 (low reasoning, Responses API)        │  │  │
│   │                                                       │  │  │
│   │  Input:  user question + schema context               │  │  │
│   │  Output: validated SQL query                          │  │  │
│   │                                                       │  │  │
│   │  SQL Quality features (gpt-5.2 reasoning):            │  │  │
│   │  • Phrase precision (keeps "campus management"        │  │  │
│   │    as a phrase, not split into generic words)         │  │  │
│   │  • Domain synonyms (AML → KYC, sanctions, etc.)       │  │  │
│   │  • COALESCE() for NULL safety                         │  │  │
│   │  • Syntax retry (1 auto-retry on SQL error)           │  │  │
│   │  • 4-layer validation (syntax, read-only,             │  │  │
│   │    injection, schema)                                 │  │  │
│   │                                                       │  │  │
│   │  Skipped when needs_new_query=false                   │  │  │
│   │  (reuses cached results from previous turn)           │  │  │
│   └───────────────────────────────────────────────────────┘  │  │
│                          │ SQL execution via pyodbc             │  │
│                          ▼                                      │  │
│              ┌───────────────────────┐                         │  │
│              │  SQL Server (prod)    │                         │  │
│              │  dbo.vw_ISDSolution_All  READ-ONLY              │  │
│              └───────────┬───────────┘                         │  │
│                          │ result rows                          │  │
│                          ▼                                      │  │
│   ┌───────────────────────────────────────────────────────┐  │  │
│   │  Agent 3: Insight Analyzer                            │  │  │
│   │  Model: gpt-4.1 (Responses API)                       │  │  │
│   │                                                       │  │  │
│   │  Input:  raw result rows + columns                    │  │  │
│   │  Output: structured insights JSON                     │  │  │
│   │                                                       │  │  │
│   │  Pre-computes statistics locally (partner counts,     │  │  │
│   │  solution areas, industry distribution) before LLM   │  │  │
│   │                                                       │  │  │
│   │  SELLER mode:   includes partner names, rankings      │  │  │
│   │  CUSTOMER mode: strips orgName, no rankings           │  │  │
│   └───────────────────────────────────────────────────────┘  │  │
│                          │ insights JSON                        │  │
│                          ▼                                      │  │
│   ┌───────────────────────────────────────────────────────┐  │  │
│   │  Agent 4: Response Formatter                          │  │  │
│   │  Model: gpt-4.1 (Responses API, stream=True)          │  │  │
│   │                                                       │  │  │
│   │  Input:  insights + original question                 │  │  │
│   │  Output: executive narrative (markdown SSE stream)    │  │  │
│   │                                                       │  │  │
│   │  Structure: Executive Summary → Market Landscape →   │  │  │
│   │             Key Discoveries → Strategic Insights →   │  │  │
│   │             Next Steps                                │  │  │
│   │                                                       │  │  │
│   │  SELLER mode only: web_search_preview tool enabled   │  │  │
│   │  → adds real-world partner news to narrative         │  │  │
│   │  → streams web source citations in done event        │  │  │
│   └───────────────────────────────────────────────────────┘  │  │
│                                                               │  │
└───────────────────────────────────────────────────────────────┘  │
```

---

## Dual Mode Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      DUAL MODE                                 │
│          Controlled by APP_MODE environment variable          │
└───────────────────┬───────────────────────┬───────────────────┘
                    │                       │
        ┌───────────▼───────┐   ┌───────────▼───────────┐
        │   SELLER MODE     │   │   CUSTOMER MODE        │
        │  (Internal use)   │   │   (External / public)  │
        │                   │   │                        │
        │  • Partner names  │   │  • No partner names    │
        │  • Rankings       │   │  • No rankings         │
        │  • Competitive    │   │  • Capability-focused  │
        │    insights       │   │  • Vendor-neutral      │
        │  • Web search     │   │  • No web search       │
        │    enabled        │   │                        │
        │  • "orgName" shown│   │  • "orgName" stripped  │
        │    in data table  │   │    from results        │
        │                   │   │                        │
        │  URL:             │   │  URL:                  │
        │  ?mode=seller     │   │  ?mode=customer        │
        └───────────────────┘   └────────────────────────┘

Teams Tab Apps (same backends, separate manifests):
  • Seller Teams App  → seller mode frontend
  • Customer Teams App → customer mode frontend
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Container Registry                                   │
│  indsolsedevacr.azurecr.io                                 │
│                                                             │
│  Images:                                                    │
│  • isd-chat-backend:v3.0-responses-api    ← Current        │
│  • isd-chat-seller-frontend:latest                         │
│  • isd-chat-customer-frontend:latest                       │
│  • isd-mcp-server:latest                                   │
│  • isd-updatemon:latest                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Pull images
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure Container Apps Environment                           │
│  Sweden Central Region                                      │
│  kindfield-353d98ed.swedencentral.azurecontainerapps.io    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Container App: Backend                             │  │
│  │  isd-chat-backend                                  │  │
│  │  Image: isd-chat-backend:v3.0-responses-api        │  │
│  │  Port: 8000  |  CPU: 1 core  |  Memory: 2 GB       │  │
│  │  Env: APP_MODE (overridden per frontend)            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Container App: Seller Frontend                     │  │
│  │  isd-chat-seller-frontend                          │  │
│  │  Image: isd-chat-seller-frontend:latest            │  │
│  │  Port: 80  |  CPU: 0.5 cores  |  Memory: 1 GB      │  │
│  │  FQDN: isd-chat-seller-frontend.kindfield-353d98ed │  │
│  │        .swedencentral.azurecontainerapps.io        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Container App: Customer Frontend                   │  │
│  │  isd-chat-customer-frontend                        │  │
│  │  Image: isd-chat-customer-frontend:latest          │  │
│  │  Port: 80  |  CPU: 0.5 cores  |  Memory: 1 GB      │  │
│  │  FQDN: isd-chat-customer-frontend.kindfield-353d98ed│  │
│  │        .swedencentral.azurecontainerapps.io        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Container App: MCP Server (separate component)     │  │
│  │  isd-mcp-server                                    │  │
│  │  For: VS Code, Claude Desktop, AI dev tools        │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Supporting Azure Resources:
  • Azure OpenAI  — gpt-4.1 + gpt-5.2 (Sweden Central)
  • SQL Server    — mssoldir-prd-sql (existing ISD production DB)
  • Cosmos DB     — Serverless, conversation history
  • App Insights  — Monitoring and diagnostics
  • Key Vault     — Secrets management
  • VNet          — Network isolation
```

---

**Legend**:
- `→` : Synchronous call
- `⇢` : Asynchronous / streaming
- `[n]` : Step number in sequence
- `✅` : Success / active feature
- `❌` : Deprecated / not used
