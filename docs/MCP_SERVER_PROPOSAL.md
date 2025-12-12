# MCP Server Proposal for Industry Solutions Directory
**Author**: Arturo Quiroga, Principal Industry Solutions Architect  
**Date**: December 12, 2025  
**Purpose**: Evaluate Model Context Protocol (MCP) server integration for ISD  
**Audience**: PSA Team Discussion

---

## Executive Summary

This document explores replacing or augmenting our current Azure AI Search-based architecture with an MCP server that wraps the Industry Solutions Directory (ISD) API. The goal is to evaluate whether direct tool-based access to ISD data could improve our solution's performance, cost-efficiency, and data freshness.

**Key Recommendation**: Hybrid approach - combine MCP server for structured queries with vector search for semantic/similarity queries.

---

## Current Architecture

### System Overview
```
ISD Website API
    ↓
Blob Storage (JSON documents)
    ↓
Azure AI Search Indexer
    ↓
Vector Index (text-embedding-3-large)
    ↓
Chat Backend (GPT-4o-mini)
    ↓
User Interface (Streamlit/Gradio)
```

### Current Capabilities
- **490 indexed solutions** with embeddings
- **Semantic search**: "Find solutions similar to X"
- **Dual browsing**: Industry AND Technology dimensions
- **Vector similarity**: Natural language understanding
- **Offline resilience**: Search works even if ISD API is down
- **Fast queries**: Sub-100ms search responses
- **Session management**: Cosmos DB for conversation history

### Current Pain Points
1. **Data freshness lag**: Periodic indexing (currently manual triggers)
2. **Infrastructure costs**: AI Search service ~$250-500/month
3. **ETL complexity**: Export → Blob → Index pipeline with 49 solutions showing warnings
4. **Duplicate management**: 700 API entries → 539 unique solutions (manual de-duplication)
5. **Schema mismatch**: Industries/technologies stored as strings vs collections

---

## Proposed: MCP Server Approach

### What is MCP?
Model Context Protocol (MCP) enables AI models to interact with external systems through structured tools. Instead of searching an index, the AI directly calls API functions.

### MCP Server Architecture
```
ISD Website API
    ↓
MCP Server (Python/TypeScript)
    ├── Tool: list_solutions_by_industry(industry: string)
    ├── Tool: list_solutions_by_technology(technology: string)
    ├── Tool: get_solution_details(solution_id: string)
    ├── Tool: search_solutions(query: string, filters: object)
    └── Tool: get_partner_info(partner_name: string)
    ↓
Chat Backend (GPT-4o-mini with tool calling)
    ↓
User Interface
```

### Example MCP Tool Definitions
```python
# Tool: list_solutions_by_technology
{
    "name": "list_solutions_by_technology",
    "description": "Get all partner solutions for a specific technology area",
    "parameters": {
        "technology": {
            "type": "string",
            "enum": ["AI Business Solutions", "Cloud & AI Platforms", 
                     "Security", "Data & Analytics", "Modern Work", ...]
        },
        "limit": {"type": "integer", "default": 10}
    }
}

# Tool: search_solutions
{
    "name": "search_solutions",
    "description": "Search solutions by keyword with optional industry/technology filters",
    "parameters": {
        "query": {"type": "string"},
        "industry": {"type": "string", "optional": true},
        "technology": {"type": "string", "optional": true}
    }
}
```

### User Experience Example
**User**: "Show me AI Business Solutions"

**Current System**: 
1. Vector search on "AI Business Solutions"
2. Filter by technology field (string contains)
3. Return ranked results with embeddings

**With MCP**:
1. AI selects `list_solutions_by_technology(technology="AI Business Solutions")`
2. Direct API call to ISD
3. Return structured JSON response

---

## Comparative Analysis

| Aspect | Current (AI Search) | MCP Server | Hybrid Approach |
|--------|-------------------|------------|-----------------|
| **Data Freshness** | Periodic (lag) | Real-time | Real-time + semantic |
| **Semantic Search** | ✅ Excellent | ❌ Limited to keyword | ✅ Best of both |
| **Query Performance** | ~50-100ms | ~200-500ms (API dependent) | Smart routing |
| **Infrastructure Cost** | ~$300/month (Search) | ~$50/month (Container App) | ~$250/month |
| **Dependency on ISD API** | Low (offline cache) | High (live dependency) | Medium |
| **Tool Calling Support** | Manual RAG | ✅ Native tools | ✅ Native tools |
| **Setup Complexity** | High (ETL pipeline) | Low (API wrapper) | Medium |
| **Vector Similarity** | ✅ Excellent | ❌ None | ✅ Available |
| **Structured Queries** | Manual filtering | ✅ Natural API calls | ✅ Natural API calls |
| **Rate Limiting Risk** | None (self-hosted) | Potential issue | Mitigated by cache |

---

## Benefits of MCP Approach

### 1. Real-Time Data Access
- **Zero lag**: No indexing delay between ISD updates and user queries
- **Always current**: Solutions reflect website immediately
- **No de-duplication needed**: ISD API handles data consistency

### 2. Cost Reduction
- **Eliminate Azure AI Search**: Save ~$250-500/month
- **Eliminate Blob Storage**: Minor savings ~$10/month
- **Simpler deployment**: Fewer moving parts

### 3. Simplified Architecture
- **No ETL pipeline**: Remove 01_export_to_blob.py, indexer configuration
- **No schema management**: Let ISD API define structure
- **Fewer failure points**: Direct API vs multi-stage pipeline

### 4. Native Tool Calling
- **GPT-4 optimization**: Models excel at structured tool use
- **Better debugging**: See exactly which API calls are made
- **Flexible queries**: Combine multiple tools in one conversation

### 5. Leverages ISD API Capabilities
- **Advanced filtering**: Use ISD's own query capabilities
- **Future-proof**: Automatically benefit from ISD API improvements
- **Canonical source**: No schema translation issues

---

## Limitations of MCP Approach

### 1. Loss of Semantic Search
- **No vector similarity**: Can't do "find solutions like X"
- **Keyword-only**: Limited to exact/partial string matches
- **No contextual understanding**: "solutions for reducing churn" won't work without keywords

### 2. Performance Concerns
- **API latency**: 200-500ms vs 50ms index lookup
- **Rate limiting**: Subject to ISD API quotas
- **Network dependency**: Requires live internet connection

### 3. Limited by ISD API Design
- **Only available endpoints**: Can't query beyond API's capabilities
- **No custom aggregations**: Can't do complex analytics without API support
- **Pagination constraints**: May limit large result sets

### 4. Production Dependency
- **ISD API uptime**: Your app's availability tied to their SLA
- **Breaking changes**: API updates could break your integration
- **No offline mode**: Can't serve users if ISD is down

---

## ISD Team Involvement

### Technical Feasibility: **Can be done independently**
- ISD API appears to be public (mssoldir-app-prd.azurewebsites.net)
- No authentication required for GET operations
- Can wrap existing endpoints in MCP server

### Why Collaborate with ISD Team?

#### 1. **Production SLA**
- Understand uptime guarantees
- Get support commitment for critical issues
- Align on deprecation/versioning policies

#### 2. **Rate Limiting**
- Current limits unknown
- Need higher quotas for production traffic
- Avoid throttling during peak usage

#### 3. **Optimized Endpoints**
- Request batch query capabilities: Get 50 solutions in one call vs 50 calls
- Semantic search at source: They could add vector search to their API
- Custom filters: Technology + Industry + Partner size/location

#### 4. **Change Notifications**
- **Webhooks**: Real-time updates when solutions change
- **Event streaming**: Subscribe to solution additions/updates/deletions
- **Hybrid optimization**: Use webhooks to trigger selective index updates

#### 5. **Data Quality**
- Resolve 49 solutions with missing descriptions at source
- Fix duplicate solution appearances (700 entries, 539 unique)
- Validate industry/technology taxonomy consistency

#### 6. **Future Enhancements**
- Partner engagement metrics: "Most viewed solutions"
- User feedback integration: "Top-rated solutions in Healthcare"
- Custom metadata: Tags, certifications, case studies

---

## Recommended Hybrid Architecture

### Best of Both Worlds

```
                    User Query
                        ↓
            AI Agent (GPT-4o-mini)
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    MCP Server              Azure AI Search
    (Structured)            (Semantic)
        ↓                       ↓
    ISD API                 Vector Index
        ↓                       ↓
    ┌───┴───────────────────────┘
    ↓
Combined Results
    ↓
User Interface
```

### Routing Logic

**Use MCP Server for:**
- ✅ "List all Security solutions"
- ✅ "Get details for solution ID 12345"
- ✅ "Show me partners in Healthcare industry"
- ✅ "What technologies does Accenture offer?"

**Use Vector Search for:**
- ✅ "Find solutions similar to customer churn reduction"
- ✅ "What helps with predictive maintenance?"
- ✅ "Show me IoT solutions" (semantic understanding)
- ✅ "Solutions for digital transformation" (concept search)

**Use Both (combine results):**
- ✅ "Find AI solutions similar to fraud detection" (technology filter + semantic)
- ✅ "Show Healthcare solutions like patient engagement tools" (industry filter + semantic)

### Implementation Strategy

#### Phase 1: MCP Server Development (1-2 weeks)
1. Create MCP server wrapping ISD API
2. Define tools: `list_by_industry`, `list_by_technology`, `get_details`, `search`
3. Add error handling and rate limiting
4. Deploy to Azure Container App

#### Phase 2: Backend Integration (1 week)
1. Add MCP client to chat backend
2. Update system prompt with tool descriptions
3. Implement smart routing logic
4. Test tool calling with GPT-4o-mini

#### Phase 3: Monitoring & Optimization (2 weeks)
1. Track which queries use MCP vs vector search
2. Monitor ISD API latency and errors
3. Optimize caching strategy
4. Tune routing logic based on usage

#### Phase 4: Vector Search Optimization (1 week)
1. Keep vector search for semantic queries only
2. Reduce index size (remove structured fields)
3. Cost optimization: Smaller tier or serverless option
4. Incremental updates via MCP webhooks (if ISD provides)

---

## Cost-Benefit Analysis

### Current Monthly Costs
- Azure AI Search (Basic): ~$75/month
- Azure AI Search (Standard S1): ~$250/month (current)
- Blob Storage: ~$10/month
- Indexer compute: Included
- **Total**: ~$260/month

### MCP-Only Approach
- Azure Container App: ~$50/month (always-on)
- Cosmos DB: ~$25/month (existing)
- **Total**: ~$75/month
- **Savings**: ~$185/month (~71% reduction)

### Hybrid Approach
- Azure AI Search (Basic): ~$75/month (reduced tier)
- MCP Container App: ~$50/month
- Cosmos DB: ~$25/month (existing)
- **Total**: ~$150/month
- **Savings**: ~$110/month (~42% reduction)

### ROI Calculation
- Development time: ~40 hours @ $200/hour = $8,000
- Payback period (MCP-only): 43 months
- Payback period (Hybrid): 73 months

**Note**: Primary value is data freshness and architectural simplification, not cost savings.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ISD API downtime | High - app unusable | Hybrid approach with fallback to cached index |
| Rate limiting | Medium - degraded performance | Collaborate with ISD team for quota increase |
| API breaking changes | High - integration failure | Version pinning, monitoring, change alerts |
| Slower performance | Medium - user experience | Smart caching, async queries, result streaming |
| Loss of semantic search | High - reduced capabilities | Keep vector search in hybrid model |
| Development complexity | Low - scope creep | Phased rollout, MVP first |

---

## Discussion Questions for PSA Team

1. **Business Value**: Is real-time data worth the architectural change, or is periodic indexing sufficient?

2. **User Expectations**: Do users expect to see brand-new solutions immediately, or is daily/weekly refresh acceptable?

3. **ISD Collaboration**: Should we engage ISD team proactively, or build independently and iterate?

4. **Semantic vs Structured**: What percentage of queries are keyword-based vs semantic? (Monitor current usage)

5. **Cost Priority**: Is $185/month savings meaningful enough to justify migration effort?

6. **Risk Tolerance**: Are we comfortable depending on ISD API uptime, or do we need offline resilience?

7. **Future Vision**: Does this align with Microsoft's broader MCP/tool-calling strategy?

8. **Performance SLA**: What response time do we guarantee? Can we meet it with API dependency?

9. **Development Capacity**: Do we have 4-6 weeks for development and testing?

10. **Rollback Plan**: If MCP approach fails, how quickly can we revert to current architecture?

---

## Next Steps

### Immediate Actions (This Week)
1. **Monitor current usage**: Log which queries are keyword vs semantic
2. **Test ISD API performance**: Measure latency, rate limits, uptime
3. **PSA team discussion**: Get feedback on this proposal
4. **Stakeholder alignment**: Present to leadership

### If Approved (Week 2-3)
1. **MVP MCP server**: Wrap 3-5 core ISD endpoints
2. **Local testing**: Validate tool calling with GPT-4o-mini
3. **ISD team outreach**: Schedule meeting to discuss collaboration
4. **Performance baseline**: Measure current system metrics for comparison

### Pilot Phase (Week 4-6)
1. **Deploy hybrid system**: MCP + vector search in parallel
2. **A/B testing**: Route 10% of traffic to MCP path
3. **Monitor metrics**: Latency, accuracy, cost, user satisfaction
4. **Iterate**: Refine routing logic based on data

### Decision Point (Week 7)
- **Full migration** to hybrid if metrics positive
- **Scale back** to vector-only if MCP underperforms
- **Optimize** architecture based on learnings

---

## Appendix: Technical References

### MCP Resources
- **MCP Specification**: https://modelcontextprotocol.io/
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk

### Current System Components
- **ISD API Endpoint**: mssoldir-app-prd.azurewebsites.net/api/Industry
- **Azure AI Search Index**: partner-solutions-integrated (637 documents)
- **Embedding Model**: text-embedding-3-large
- **Chat Model**: gpt-4o-mini (supports tool calling)

### Related Documentation
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Current system architecture
- [MCS_INTEGRATION.md](./MCS_INTEGRATION.md) - Multi-Cloud Search patterns
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Infrastructure setup

---

## Conclusion

The MCP server approach offers compelling benefits in data freshness, cost efficiency, and architectural simplicity. However, the loss of semantic search capabilities is a significant trade-off.

**Recommended Path Forward**: Implement hybrid architecture to preserve semantic search while gaining real-time structured querying. This approach:
- ✅ Maintains all current capabilities
- ✅ Adds real-time data access
- ✅ Reduces costs by 42%
- ✅ Positions us for future MCP ecosystem growth
- ✅ Provides graceful fallback if ISD API unavailable

**Critical Success Factor**: Collaboration with ISD team for production-grade reliability, optimized endpoints, and change notifications.

---

**Document Owner**: Arturo Quiroga (arturoquiroga@microsoft.com)  
**Last Updated**: December 12, 2025  
**Version**: 1.0  
**Review Date**: January 2026 (after PSA team discussion)
