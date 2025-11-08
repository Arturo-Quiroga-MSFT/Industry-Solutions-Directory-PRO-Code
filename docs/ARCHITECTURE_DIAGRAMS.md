# Architecture Diagrams

This document contains visual representations of the Industry Solutions Chat Assistant architecture.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                   (Streamlit Web Application)                    │
│                                                                  │
│  Components:                                                     │
│  • Chat input/output                                            │
│  • Industry filter dropdown                                     │
│  • Technology filter dropdown                                   │
│  • Session history sidebar                                      │
│  • Citation cards with relevance scores                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS POST /api/chat
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND API (FastAPI)                        │
│                Container: indsolsedevacr.azurecr.io/             │
│                industry-solutions-backend:v2.8                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ REST API Endpoints                                        │  │
│  │ • POST /api/chat                                         │  │
│  │ • GET /api/chat/history/{session_id}                     │  │
│  │ • GET /api/facets                                        │  │
│  │ • GET /api/health                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Service Layer                                            │  │
│  │                                                          │  │
│  │  search_service.py                                       │  │
│  │  ├─ hybrid_search() ──────────────────┐                 │  │
│  │  ├─ semantic_hybrid_search()          │                 │  │
│  │  ├─ get_facets()                      │                 │  │
│  │  └─ _build_filter_expression()        │                 │  │
│  │                                        │                 │  │
│  │  openai_service.py                    │                 │  │
│  │  ├─ generate_chat_response() ─────────┼────┐            │  │
│  │  └─ format_context()                  │    │            │  │
│  │                                        │    │            │  │
│  │  cosmos_service.py                    │    │            │  │
│  │  ├─ save_conversation() ──────────────┼────┼───┐        │  │
│  │  ├─ get_conversation_history()        │    │   │        │  │
│  │  └─ create_session()                  │    │   │        │  │
│  └────────────────────────────────────────┼────┼───┼────────┘  │
└───────────────────────────────────────────┼────┼───┼───────────┘
                                            │    │   │
                    ┌───────────────────────┘    │   │
                    │    ┌───────────────────────┘   │
                    │    │    ┌──────────────────────┘
                    ▼    ▼    ▼
         ┌──────────────────────────────────────────────────┐
         │         AZURE AI SEARCH (Standard S1)             │
         │         indsolse-dev-srch-okumlm                  │
         │                                                   │
         │  Index: partner-solutions-integrated             │
         │  • 535 documents                                 │
         │  • 3072-dimension vectors                        │
         │                                                   │
         │  ┌──────────────────────────────────────────┐   │
         │  │ Integrated Vectorization                 │   │
         │  │                                          │   │
         │  │ Vectorizer: openai-vectorizer           │   │
         │  │ • Model: text-embedding-3-large         │   │
         │  │ • Deployment: text-embedding-3-large    │   │
         │  │ • Auth: Managed Identity                │   │
         │  │                                          │   │
         │  │ When query arrives:                     │   │
         │  │ 1. Automatically vectorize query text   │   │
         │  │ 2. Perform hybrid search (vector+BM25)  │   │
         │  │ 3. Apply OData filters                  │   │
         │  │ 4. Return top K results                 │   │
         │  └──────────────────────────────────────────┘   │
         │         ▲                                         │
         │         │ Managed Identity                       │
         │         │ Authentication                          │
         └─────────┼─────────────────────────────────────────┘
                   │
         ┌─────────▼─────────────────────────────────────────┐
         │      AZURE OPENAI (GPT-4.1-mini)                  │
         │      indsolse-dev-ai-okumlm                       │
         │                                                   │
         │  Deployments:                                     │
         │  • gpt-4.1-mini (chat completions)               │
         │  • text-embedding-3-large (for indexing)         │
         │                                                   │
         │  Used by:                                         │
         │  1. Search vectorizer (automatic)                 │
         │  2. Chat completions (backend API)                │
         └───────────────────────────────────────────────────┘

         ┌───────────────────────────────────────────────────┐
         │      AZURE COSMOS DB (NoSQL Serverless)           │
         │      indsolse-dev-db-okumlm                       │
         │                                                   │
         │  Database: industry-solutions-db                  │
         │  Container: chat-sessions                         │
         │  • Partition Key: sessionId                       │
         │  • TTL: 90 days                                   │
         │                                                   │
         │  Stores:                                          │
         │  • Conversation history                           │
         │  • User messages                                  │
         │  • Assistant responses                            │
         │  • Citations                                      │
         │  • Session metadata                               │
         └───────────────────────────────────────────────────┘
```

## Data Flow - Chat Request

```
┌────────┐
│  USER  │
└────┬───┘
     │ 1. Sends message: "What healthcare AI solutions are available?"
     ▼
┌─────────────────────┐
│  STREAMLIT FRONTEND │
│  indsolse-dev-      │
│  frontend-vnet      │
└──────┬──────────────┘
       │ 2. POST /api/chat
       │    {
       │      "message": "What healthcare AI solutions...",
       │      "conversation_id": "uuid",
       │      "filters": {"industries": ["Healthcare"]}
       │    }
       ▼
┌──────────────────────────────────────────────────────┐
│  BACKEND API (search_service.py)                     │
│                                                       │
│  3. Build REST API request:                          │
│     {                                                 │
│       "search": "healthcare AI solutions",           │
│       "vectorQueries": [{                            │
│         "kind": "text",  ← Integrated vectorization  │
│         "text": "healthcare AI solutions",           │
│         "fields": "content_vector",                  │
│         "k": 3                                        │
│       }],                                             │
│       "filter": "search.ismatch('Healthcare',...)",  │
│       "top": 3                                        │
│     }                                                 │
│                                                       │
│  4. Send REST API call:                              │
│     POST https://...search.windows.net/indexes/      │
│          partner-solutions-integrated/docs/search    │
│          ?api-version=2024-07-01                     │
│     Headers: Authorization: Bearer <token>           │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  AZURE AI SEARCH                                     │
│                                                       │
│  5. Integrated vectorizer:                           │
│     • Calls Azure OpenAI text-embedding-3-large     │
│     • Generates 3072-dim vector for query           │
│     • Uses managed identity (no API key)            │
│                                                       │
│  6. Hybrid search:                                   │
│     • Vector search (semantic similarity)           │
│     • BM25 keyword search                            │
│     • Apply filter: industries = Healthcare         │
│                                                       │
│  7. Returns results:                                 │
│     [                                                 │
│       {                                               │
│         "solution_name": "Lightbeam Health...",      │
│         "partner_name": "Lightbeam Health...",       │
│         "@search.score": 0.0167,                     │
│         "description": "AI-powered population..."    │
│       },                                              │
│       {                                               │
│         "solution_name": "Andor Health",             │
│         "@search.score": 0.0159,                     │
│         ...                                           │
│       }                                               │
│     ]                                                 │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  BACKEND API (openai_service.py)                     │
│                                                       │
│  8. Build LLM prompt:                                │
│     System: "You are an expert assistant..."         │
│     Context: [Search results with descriptions]      │
│     User: "What healthcare AI solutions..."          │
│                                                       │
│  9. Call Azure OpenAI:                               │
│     POST https://...openai.azure.com/openai/         │
│          deployments/gpt-4.1-mini/chat/completions   │
│     {                                                 │
│       "messages": [                                   │
│         {"role": "system", "content": "..."},        │
│         {"role": "user", "content": "..."}           │
│       ],                                              │
│       "temperature": 0.7                              │
│     }                                                 │
│                                                       │
│  10. GPT-4.1-mini generates response:                │
│      "Here's a summary of healthcare AI solutions    │
│       available:\n\n### 1. Lightbeam Health..."      │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  BACKEND API (cosmos_service.py)                     │
│                                                       │
│  11. Save to Cosmos DB:                              │
│      {                                                │
│        "sessionId": "uuid",                          │
│        "messages": [                                  │
│          {                                            │
│            "role": "user",                           │
│            "content": "What healthcare AI...",       │
│            "timestamp": "2025-11-08T17:47:00Z"       │
│          },                                           │
│          {                                            │
│            "role": "assistant",                      │
│            "content": "Here's a summary...",         │
│            "citations": [...],                       │
│            "timestamp": "2025-11-08T17:47:03Z"       │
│          }                                            │
│        ]                                              │
│      }                                                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  BACKEND API Response                                │
│                                                       │
│  12. Return to frontend:                             │
│      {                                                │
│        "response": "Here's a summary of healthcare   │
│                     AI solutions...",                 │
│        "session_id": "uuid",                         │
│        "citations": [                                 │
│          {                                            │
│            "solution_name": "Lightbeam Health...",   │
│            "partner_name": "Lightbeam Health...",    │
│            "relevance_score": 0.0167,                │
│            "url": "https://solutions.microsoft..."   │
│          }                                            │
│        ],                                             │
│        "follow_up_questions": [...]                  │
│      }                                                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│  STREAMLIT FRONTEND │
│                     │
│  13. Display:       │
│  • AI response      │
│  • Citation cards   │
│  • Follow-ups       │
└──────┬──────────────┘
       │
       ▼
┌────────┐
│  USER  │ Sees results!
└────────┘
```

## REST API vs SDK Comparison

### Before v2.8 (Failed)

```
┌──────────────────────┐
│  Backend API         │
│                      │
│  azure-search-       │
│  documents SDK       │
│  v11.6.0             │
└──────┬───────────────┘
       │ VectorizableTextQuery
       │ (uses older API version)
       ▼
┌──────────────────────┐
│  Azure AI Search     │
│                      │
│  Error: "Field       │
│  'content_vector'    │
│  does not have a     │
│  vectorizer defined" │
└──────────────────────┘
```

### After v2.8 (Success)

```
┌──────────────────────┐
│  Backend API         │
│                      │
│  httpx + REST API    │
│  api-version=        │
│  2024-07-01          │
└──────┬───────────────┘
       │ Direct REST call:
       │ {
       │   "vectorQueries": [{
       │     "kind": "text",
       │     "text": "query",
       │     ...
       │   }]
       │ }
       ▼
┌──────────────────────┐
│  Azure AI Search     │
│                      │
│  ✅ Integrated       │
│  vectorization       │
│  working             │
└──────────────────────┘
```

## Integrated Vectorization Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Traditional Approach (Client-Side Embeddings)              │
│                                                             │
│  User Query                                                 │
│      ↓                                                      │
│  [1] Call Azure OpenAI Embeddings API                      │
│      POST /deployments/text-embedding-3-large/embeddings   │
│      Cost: ~$0.0001 per query                              │
│      Time: ~100-200ms                                       │
│      ↓                                                      │
│  [2] Get 3072-dim vector                                   │
│      ↓                                                      │
│  [3] Call Azure AI Search with vector                      │
│      POST /indexes/{index}/docs/search                     │
│      Time: ~100-200ms                                       │
│      ↓                                                      │
│  [4] Get results                                           │
│                                                             │
│  Total Time: ~200-400ms                                    │
│  Total Cost: $0.0001 per query                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Integrated Vectorization (v2.8)                           │
│                                                             │
│  User Query                                                 │
│      ↓                                                      │
│  [1] Call Azure AI Search with query TEXT                  │
│      POST /indexes/{index}/docs/search                     │
│      {                                                      │
│        "vectorQueries": [{                                  │
│          "kind": "text",  ← Search service handles this    │
│          "text": "user query"                              │
│        }]                                                   │
│      }                                                      │
│      │                                                      │
│      └─→ Search service calls its vectorizer automatically │
│          (uses managed identity, no client API key needed) │
│      ↓                                                      │
│  [2] Get results with vectors already computed             │
│                                                             │
│  Total Time: ~100-200ms (50% faster)                       │
│  Total Cost: $0 for query embeddings                       │
│                                                             │
│  Benefits:                                                  │
│  ✅ Reduced latency                                        │
│  ✅ Lower cost                                             │
│  ✅ Simpler code                                           │
│  ✅ Fewer API dependencies                                 │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Container Registry                                   │
│  indsolsedevacr.azurecr.io                                 │
│                                                             │
│  Images:                                                    │
│  • industry-solutions-backend:v2.8 ← Current               │
│  • industry-solutions-backend:v2.7 (old)                   │
│  • industry-solutions-frontend:latest                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ Pull images
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure Container Apps Environment                           │
│  Sweden Central Region                                      │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  Virtual Network (VNet)                           │    │
│  │  indsolse-dev-vnet                                │    │
│  │                                                   │    │
│  │  ┌─────────────────────────────────────────┐     │    │
│  │  │  Container App: Backend                 │     │    │
│  │  │  indsolse-dev-backend-v2-vnet          │     │    │
│  │  │                                         │     │    │
│  │  │  Image: backend:v2.8                   │     │    │
│  │  │  Replicas: 1-3 (auto-scale)           │     │    │
│  │  │  CPU: 0.5 cores                        │     │    │
│  │  │  Memory: 1 GB                          │     │    │
│  │  │  Port: 8000                            │     │    │
│  │  │                                         │     │    │
│  │  │  FQDN: indsolse-dev-backend-v2-vnet.  │     │    │
│  │  │        icyplant-dd879251.swedencentral.│     │    │
│  │  │        azurecontainerapps.io          │     │    │
│  │  └─────────────────────────────────────────┘     │    │
│  │                                                   │    │
│  │  ┌─────────────────────────────────────────┐     │    │
│  │  │  Container App: Frontend                │     │    │
│  │  │  indsolse-dev-frontend-vnet            │     │    │
│  │  │                                         │     │    │
│  │  │  Image: frontend:latest                │     │    │
│  │  │  Replicas: 1-2 (auto-scale)           │     │    │
│  │  │  CPU: 0.5 cores                        │     │    │
│  │  │  Memory: 1 GB                          │     │    │
│  │  │  Port: 8501 (Streamlit)               │     │    │
│  │  │                                         │     │    │
│  │  │  FQDN: indsolse-dev-frontend-vnet.    │     │    │
│  │  │        icyplant-dd879251.swedencentral.│     │    │
│  │  │        azurecontainerapps.io          │     │    │
│  │  └─────────────────────────────────────────┘     │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

**Legend**:
- `→` : Synchronous API call
- `⇢` : Asynchronous operation
- `[n]` : Step number in sequence
- `✅` : Success/Working
- `❌` : Failed/Not working
