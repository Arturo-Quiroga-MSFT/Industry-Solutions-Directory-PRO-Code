# Current Architecture - v2.8 (Production)

**Last Updated**: November 8, 2025  
**Version**: v2.8  
**Status**: ✅ Production Ready

## Overview

The Industry Solutions Directory Chat Assistant is deployed on Azure Container Apps with integrated vectorization for optimal performance and cost efficiency. This document describes the **current production architecture** as of v2.8.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Frontend (Streamlit)                              │
│                  indsolse-dev-frontend-vnet.azurecontainerapps.io       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Streamlit Chat Interface                                       │    │
│  │  - Real-time chat UI                                           │    │
│  │  - Session management                                          │    │
│  │  - Filter controls (industry, technology)                      │    │
│  │  - Citation display with relevance scores                      │    │
│  └─────────────────────────┬──────────────────────────────────────┘    │
└───────────────────────────┼───────────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                               │
│              indsolse-dev-backend-v2-vnet.azurecontainerapps.io         │
│                          Version: v2.8                                   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  FastAPI Application (Python 3.13)                             │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │  Endpoints:                                           │     │    │
│  │  │  • POST /api/chat (main chat endpoint)               │     │    │
│  │  │  • GET /api/chat/history/{session_id}               │     │    │
│  │  │  • GET /api/facets (filter options)                  │     │    │
│  │  │  • GET /api/health (health check)                    │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │  Services:                                            │     │    │
│  │  │  • search_service.py (REST API to Azure Search)      │     │    │
│  │  │  • openai_service.py (chat completions)              │     │    │
│  │  │  • cosmos_service.py (conversation storage)          │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────┬────────────────────┬────────────────────┬───────────────────────┘
      │ REST API           │ Azure SDK          │ Azure SDK
      │ (httpx)            │                    │
      ▼                    ▼                    ▼
┌──────────────────┐  ┌────────────────┐  ┌───────────────────────┐
│  Azure AI Search │  │ Azure OpenAI   │  │  Azure Cosmos DB      │
│  (Standard)      │  │                │  │  (NoSQL - Serverless) │
│                  │  │  Deployments:  │  │                       │
│  Index:          │  │  • gpt-4.1-mini│  │  Database:            │
│  partner-        │  │    (chat)      │  │  industry-solutions-db│
│  solutions-      │  │  • text-embed- │  │                       │
│  integrated      │  │    ding-3-     │  │  Container:           │
│                  │  │    large       │  │  chat-sessions        │
│  Documents: 535  │  │    (3072 dims) │  │                       │
│                  │  │                │  │  Features:            │
│  Features:       │  └────────────────┘  │  • Session storage    │
│  • Integrated    │         ▲            │  • Chat history       │
│    Vectorization │         │            │  • Analytics data     │
│  • Hybrid Search │         │            └───────────────────────┘
│  • OData Filters │         │
│                  │         │
│  Vectorizer:     │         │
│  openai-         │─────────┘
│  vectorizer      │  Managed Identity
│  (automatic      │  Authentication
│   query          │
│   vectorization) │
└──────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│     Azure Application Insights           │
│     (Monitoring & Observability)         │
│                                          │
│  • Request/response logging             │
│  • Error tracking                       │
│  • Performance metrics                  │
│  • Custom telemetry                     │
└──────────────────────────────────────────┘
```

## Key Architecture Decisions

### 1. REST API vs. Python SDK for Azure AI Search

**Decision**: Use direct REST API calls with `httpx` instead of `azure-search-documents` Python SDK.

**Rationale**:
- Python SDK (v11.6.0) had compatibility issues with integrated vectorization (VectorizableTextQuery)
- REST API with explicit `api-version=2024-07-01` provides reliable access to latest features
- Simpler code with better control over request format
- Easier debugging with full visibility into HTTP requests/responses

**Implementation**:
```python
# REST API approach (v2.8+)
request_body = {
    "search": query,
    "vectorQueries": [{
        "kind": "text",  # Integrated vectorization
        "text": query,
        "fields": "content_vector",
        "k": top_k
    }]
}

async with httpx.AsyncClient() as client:
    response = await client.post(url, json=request_body,
        headers={"Authorization": f"Bearer {token}"})
```

### 2. Integrated Vectorization

**Decision**: Use Azure AI Search's integrated vectorization feature instead of client-side embedding generation.

**Benefits**:
- ✅ Reduced latency: No separate API call to generate embeddings
- ✅ Lower cost: No token usage for query embeddings
- ✅ Simplified code: No need for OpenAI embedding service in query path
- ✅ Better reliability: Fewer external dependencies

**Configuration**:
- Vectorizer: `openai-vectorizer`
- Model: `text-embedding-3-large` (3072 dimensions)
- Authentication: Managed identity from Search to OpenAI
- Query format: `vectorQueries[].kind = "text"`

### 3. OData Filter Syntax

**Decision**: Use `search.ismatch()` function for filtering instead of collection-based `any/all` operators.

**Reason**: The `industries` and `technologies` fields are `Edm.String` (simple strings), not `Collection(Edm.String)`.

**Implementation**:
```python
# Correct syntax for Edm.String fields
filter_expr = "search.ismatch('Retail', 'industries')"

# NOT: industries/any(i: i eq 'Retail')  # Only for collections
```

### 4. Container Apps vs. App Service

**Decision**: Deploy on Azure Container Apps with VNet integration.

**Benefits**:
- Container-based deployment (Docker)
- Auto-scaling with KEDA
- VNet integration for secure communication
- Lower cost for variable workloads
- Easy multi-environment support

## Data Flow

### Chat Request Flow

1. **User sends message** via Streamlit frontend
2. **Frontend calls** `POST /api/chat` with message and optional filters
3. **Backend receives request**:
   - Validates input
   - Checks for existing session in Cosmos DB
4. **Search Service** makes REST API call to Azure AI Search:
   - Request includes: `search` text and `vectorQueries` with `kind="text"`
   - Azure Search automatically vectorizes query using integrated vectorizer
   - Performs hybrid search (vector + keyword)
   - Applies OData filters if specified
5. **Search returns** top 3-5 relevant solutions with relevance scores
6. **OpenAI Service** calls GPT-4.1-mini:
   - System prompt defines role and behavior
   - Context includes retrieved solutions
   - User message from request
7. **LLM generates response** with recommendations and citations
8. **Cosmos Service** saves conversation:
   - Stores user message, assistant response, citations
   - Updates session metadata
9. **Backend returns response** to frontend:
   - AI-generated response
   - Citation array with relevance scores
   - Session ID for history tracking
   - Follow-up question suggestions

## Environment Configuration

### Container App: Backend (v2.8)

**Container**: `indsolsedevacr.azurecr.io/industry-solutions-backend:v2.8`

**Environment Variables**:
```bash
AZURE_COSMOS_DB_ENDPOINT=<secret-ref>
AZURE_COSMOS_DB_NAME=industry-solutions-db
AZURE_SEARCH_ENDPOINT=https://indsolse-dev-srch-okumlm.search.windows.net
AZURE_SEARCH_INDEX_NAME=partner-solutions-integrated
AZURE_OPENAI_ENDPOINT=https://indsolse-dev-ai-okumlm.openai.azure.com/
AZURE_OPENAI_CHAT_MODEL=gpt-4.1-mini
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_COSMOS_ENDPOINT=https://indsolse-dev-db-okumlm.documents.azure.com:443/
```

**Authentication**: DefaultAzureCredential (managed identity)

**Resources**:
- CPU: 0.5 cores
- Memory: 1 GB
- Min replicas: 1
- Max replicas: 3

### Container App: Frontend

**Container**: `indsolsedevacr.azurecr.io/industry-solutions-frontend:latest`

**Environment Variables**:
```bash
API_BASE_URL=https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io
```

**Resources**:
- CPU: 0.5 cores
- Memory: 1 GB
- Min replicas: 1
- Max replicas: 2

## Search Index Configuration

### Index: partner-solutions-integrated

**Statistics**:
- Documents: 535
- Storage: ~50 MB
- Average relevance score: 0.015-0.020

**Key Fields**:
| Field | Type | Searchable | Filterable | Facetable |
|-------|------|-----------|-----------|-----------|
| id | Edm.String | ❌ | ❌ | ❌ |
| solution_name | Edm.String | ✅ | ❌ | ❌ |
| partner_name | Edm.String | ✅ | ✅ | ✅ |
| description | Edm.String | ✅ | ❌ | ❌ |
| industries | Edm.String | ✅ | ✅ | ✅ |
| technologies | Edm.String | ✅ | ✅ | ✅ |
| content_vector | Collection(Edm.Single) | ❌ | ❌ | ❌ |

**Vector Configuration**:
- Dimensions: 3072
- Profile: `integrated-vector-profile`
- Vectorizer: `openai-vectorizer`
  - Resource: https://indsolse-dev-ai-okumlm.openai.azure.com
  - Deployment: text-embedding-3-large
  - Model: text-embedding-3-large
  - Authentication: Managed identity

## Monitoring & Observability

### Application Insights

**Connected Services**:
- Backend API (FastAPI)
- Azure AI Search (via diagnostics)
- Azure OpenAI (via diagnostics)
- Azure Cosmos DB (via diagnostics)

**Key Metrics Tracked**:
1. **Request Metrics**:
   - Total requests
   - Response time (p50, p95, p99)
   - Error rate
   - Success rate

2. **Search Metrics**:
   - Search query count
   - Average relevance score
   - Filter usage patterns
   - Top searched terms

3. **LLM Metrics**:
   - Token usage (prompt + completion)
   - Average response time
   - Model version usage
   - Error rate

4. **Business Metrics**:
   - Active sessions
   - Messages per session
   - Industry/technology filter usage
   - Citation click-through rate

### Health Checks

**Endpoint**: `GET /api/health`

**Response Example**:
```json
{
  "status": "healthy",
  "version": "2.8.0",
  "services": {
    "search": "healthy",
    "openai": "healthy",
    "cosmos": "healthy"
  },
  "timestamp": "2025-11-08T17:50:00Z"
}
```

## Security

### Authentication & Authorization

1. **User to Frontend**: No authentication (public access)
2. **Frontend to Backend**: HTTPS with CORS validation
3. **Backend to Azure Services**: DefaultAzureCredential (managed identity)

### Network Security

- **VNet Integration**: Backend and frontend in same VNet
- **Private Endpoints**: Optional (currently using public endpoints)
- **CORS Policy**: Configured in backend for frontend domain
- **TLS**: Enforced on all HTTPS endpoints

### Data Privacy

- **Chat History**: Stored for 90 days, then auto-deleted
- **PII Handling**: No sensitive data collected
- **Logging**: Sensitive fields redacted in logs

## Cost Breakdown (Monthly Estimate)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| Azure Container Apps | 2 apps (backend + frontend) | $20-40 |
| Azure OpenAI (Chat) | GPT-4.1-mini (~300K tokens/day) | $100-150 |
| Azure OpenAI (Embeddings) | text-embedding-3-large (indexing only) | $5-10 |
| Azure AI Search | Standard S1 | $250 |
| Azure Cosmos DB | Serverless (5GB, 500K RUs) | $15-25 |
| Azure Container Registry | Standard | $5 |
| Application Insights | Basic | $5-10 |
| **Total** | | **$400-490/month** |

**Cost Optimizations Applied**:
- ✅ Integrated vectorization (no query embedding costs)
- ✅ Serverless Cosmos DB (pay per use)
- ✅ Container Apps (auto-scaling)
- ✅ Standard Search tier (sufficient for workload)

## Deployment History

### v2.8 (Current - November 8, 2025)
- ✅ **REST API implementation** for Azure AI Search
- ✅ **Integrated vectorization** working in production
- ✅ Fixed environment variable (`AZURE_SEARCH_INDEX_NAME`)
- ✅ Fixed OData filter syntax for string fields
- ✅ Comprehensive testing passed

### v2.4-v2.7 (Failed Attempts)
- ❌ Python SDK (azure-search-documents) with VectorizableTextQuery
- ❌ API version incompatibility with integrated vectorization
- ❌ "Field 'content_vector' does not have a vectorizer defined" error

### v2.3 and earlier
- Manual embedding generation for queries
- Higher latency and cost
- More complex code

## Future Enhancements

1. **Performance**:
   - Response caching for common queries
   - Streaming responses (SSE or WebSocket)
   - CDN for static assets

2. **Features**:
   - Multi-turn conversation context (currently basic)
   - User feedback collection (thumbs up/down)
   - Export conversation history
   - Voice interface (speech-to-text)

3. **Infrastructure**:
   - Private endpoints for all services
   - Multi-region deployment
   - Disaster recovery plan
   - Blue-green deployment

4. **Analytics**:
   - Power BI dashboards
   - User behavior analysis
   - A/B testing framework
   - Partner solution effectiveness tracking

## Troubleshooting Guide

### Common Issues

**Issue**: Search returns no results
- Check index name: `partner-solutions-integrated`
- Verify 535 documents indexed
- Test with simple query: "AI"

**Issue**: Slow response times
- Check Application Insights for bottlenecks
- Verify Azure AI Search performance tier
- Consider response caching

**Issue**: Authentication errors
- Verify managed identity has correct roles:
  - Search: `Search Index Data Reader`
  - OpenAI: `Cognitive Services OpenAI User`
  - Cosmos: `Cosmos DB Built-in Data Contributor`

**Issue**: Filter not working
- Verify OData syntax: `search.ismatch('value', 'fieldname')`
- Check field types (String vs Collection)

## References

- [Main README](../README.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [API Documentation](https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io/docs)
