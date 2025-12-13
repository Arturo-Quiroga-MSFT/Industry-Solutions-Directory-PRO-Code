# MCP ISD Server

Model Context Protocol (MCP) server for the Microsoft Industry Solutions Directory (ISD).

## Overview

This MCP server wraps the ISD API to provide structured tools for AI agents to discover and retrieve partner solutions. Instead of searching an index, AI models can directly call these tools to get **real-time data** from the ISD website.

**Author**: Arturo Quiroga, Principal Industry Solutions Architect  
**Date**: December 12, 2025  
**Status**: ✅ Tested & Working

## Available Tools

### 1. `list_industries`
Get all available industry categories from ISD.

**Returns**: List of industry names (Financial Services, Healthcare & Life Sciences, etc.)

### 2. `list_technologies`
Get all available technology categories from ISD.

**Returns**: List of technology names (AI Business Solutions, Cloud and AI Platforms, Security, etc.)

### 3. `get_solutions_by_industry`
Get all partner solutions for a specific industry use case.

**Parameters**:
- `industry` (required): Industry use case name (e.g., "Managing Risk and Compliance", "Student Success", "Institutional Innovation")

**Returns**: Array of solutions with name, partner, description, url, logo, industries, technologies

**Example**: Query for "Managing Risk and Compliance" returns 85 solutions

### 4. `get_solutions_by_technology`
Get all partner solutions for a specific technology category across all industries.

**Parameters**:
- `technology` (required): Technology name (e.g., "AI Business Solutions", "Cloud and AI Platforms", "Security")

**Returns**: De-duplicated array of solutions from all industries

**Note**: This queries multiple industries and de-duplicates by solution ID, so it may take longer (queries all 35 industry themes)

### 5. `search_solutions`
Search solutions by keyword with optional filters.

**Parameters**:
- `query` (optional): Keyword search
- `industry` (optional): Filter by industry
- `technology` (optional): Filter by technology
- `limit` (optional): Max results (default: 10)

**Returns**: Filtered array of matching solutions

## Installation

```bash
cd mcp-isd-server
pip install -r requirements.txt
```

## Testing

### Quick Test (Recommended)

```bash
cd mcp-isd-server
python test_client.py
# Choose option 1 for client function tests
```

**Test Results** (December 12, 2025):
- ✅ Lists 35 industry use cases (e.g., "Student Success", "Managing Risk and Compliance")
- ✅ Lists 3 technology areas (AI Business Solutions, Cloud and AI Platforms, Security)
- ✅ Retrieves 85 solutions for "Managing Risk and Compliance" industry
- ✅ Retrieves 2 solutions for "Student Success" industry
- ✅ De-duplicates solutions across multiple industries
- ✅ Keyword search with filters working

### Comprehensive Test

```bash
cd mcp-isd-server
python -c "
import asyncio
from server import ISDClient

async def test():
    client = ISDClient()
    
    # Get Financial Services solutions
    solutions = await client.get_solutions_by_industry('Managing Risk and Compliance')
    print(f'Found {len(solutions)} solutions')
    
    for sol in solutions[:3]:
        print(f'  - {sol[\"name\"]} by {sol[\"partner\"]}')
    
    await client.close()

asyncio.run(test())
"
```

### Run as MCP server (for integration with AI agents):

```bash
python server.py
```

The server runs over stdio and communicates via MCP protocol.

## Architecture

```
┌─────────────────┐
│   AI Agent      │
│  (GPT-4, etc)   │
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│  MCP ISD Server │
│   (server.py)   │
└────────┬────────┘
         │ HTTPS
┌────────▼────────────────────────────────┐
│  ISD API                                │
│  mssoldir-app-prd.azurewebsites.net     │
└─────────────────────────────────────────┘
```

## ISD API Endpoints Used

- `GET /api/Industry/getMenu` - Get all industries and use cases hierarchy (cached)
- `GET /api/Industry/GetThemeDetalsByViewId?slug={industryThemeSlug}` - Get solutions for a specific industry theme

### API Response Structure

Solutions are returned with the following fields:
```json
{
  "id": "uuid",
  "solutionName": "Solution Title",
  "orgName": "Partner Company Name",
  "solutionDescription": "HTML description",
  "url": "https://partner-solution-url",
  "logoUrl": "https://logo-url",
  "industries": ["Industry1", "Industry2"],
  "technologies": ["Tech1", "Tech2"]
}
```

**Note**: Field names differ from initial API investigation. See [API_INVESTIGATION.md](../data-ingestion/API_INVESTIGATION.md) for detailed findings.

## Performance Considerations

**Tested Performance** (December 12, 2025):
- **Menu API**: ~200ms (cached after first call)
- **Theme details API**: ~500-800ms per industry theme
- **Industry query**: Fast (single API call) - e.g., 85 solutions in ~600ms
- **Technology query**: Slower (queries all 35 themes, ~20-30 seconds for full scan)

**Caching Strategy**:
- Industries and technologies lists are cached in memory after first fetch
- Solutions are NOT cached (always real-time from API)
- No persistent cache - fresh data on every MCP server restart

**Recommendations**:
- Use specific industry queries when possible (faster than technology queries)
- Consider rate limiting for production use
- Technology queries scan all industries - may want to limit to specific industries for performance

## Example Usage in AI Conversation

**User**: "Show me solutions for Managing Risk and Compliance"

**AI Agent**:
1. Calls `get_solutions_by_industry(industry="Managing Risk and Compliance")`
2. Receives 85 real-time solutions from ISD API in ~600ms
3. Presents solutions to user with partner names, descriptions, URLs

**User**: "Find all AI Business Solutions"

**AI Agent**:
1. Calls `get_solutions_by_technology(technology="AI Business Solutions")`
2. Scans all 35 industry themes, de-duplicates solutions by ID
3. Returns comprehensive list of unique AI solutions across all industries

**User**: "What Security solutions are available for Student Success?"

**AI Agent**:
1. Calls `get_solutions_by_industry(industry="Student Success")`
2. Filters results by technology="Security" from the response
3. Returns targeted list of security solutions for education

## Next Steps

1. ✅ Create MCP server structure
2. ✅ Implement ISD API client with correct field names
3. ✅ Define MCP tools (list_industries, list_technologies, get_solutions_by_industry, etc.)
4. ✅ Create test client
5. ✅ Test all tools - verified working with real data
6. ✅ Document API structure and findings
7. ⏳ Add error handling and retries (basic error handling in place)
8. ⏳ Optimize caching strategy (consider persistent cache)
9. ⏳ Add rate limiting for production
10. ⏳ Integrate into main chat solution (see integration options below)
11. ⏳ Compare performance with vector search approach

## Integration Options

### Option 1: Hybrid Approach (Recommended)
- Keep existing vector search for semantic queries
- Add MCP server for structured/real-time queries
- AI agent chooses appropriate tool based on query type

### Option 2: MCP-Only
- Replace vector search entirely with MCP tools
- Simpler architecture, lower cost
- Lose semantic search capabilities

### Option 3: MCP + Webhook Updates
- Use MCP for queries
- Subscribe to ISD webhooks (if available) for real-time index updates
- Best of both worlds: semantic search + real-time data

See [MCP_SERVER_PROPOSAL.md](../docs/MCP_SERVER_PROPOSAL.md) for detailed analysis.

## Related Documentation

- [MCP Server Proposal](../docs/MCP_SERVER_PROPOSAL.md) - Architecture analysis
- [ISD API Investigation](../data-ingestion/API_INVESTIGATION.md) - API endpoint documentation
- [Architecture](../ARCHITECTURE.md) - Main solution architecture

## Limitations

- No semantic/vector search (keyword matching only in search_solutions)
- Dependent on ISD API uptime (no offline fallback)
- Technology queries are slow (~20-30s to scan all industries)
- HTML descriptions need cleanup for display (contains markup)
- No built-in persistent caching (fresh data on every restart)

## Advantages Over Vector Search

✅ **Real-time data** - Zero lag, always current (no indexing delay)  
✅ **Zero infrastructure cost** - No Azure AI Search service needed  
✅ **Simpler architecture** - No ETL pipeline, blob storage, or indexer  
✅ **Native tool calling** - GPT-4 optimized for structured function calls  
✅ **Canonical source** - Data directly from ISD API (no schema translation)  
✅ **Auto-updates** - New solutions appear immediately without re-indexing

## Trade-offs vs Vector Search

❌ **No semantic search** - Can't find "solutions like X" or conceptual queries  
❌ **Slower for broad queries** - Technology search queries all 35 themes  
❌ **API dependency** - Requires ISD API to be available  
❌ **No offline mode** - Can't serve requests if ISD API is down  
❌ **HTML in descriptions** - Requires cleanup for clean display

**Verdict**: Best used in hybrid approach - MCP for structured queries, vector search for semantic queries.

## Future Enhancements

- [ ] Add persistent caching (Redis) with TTL
- [ ] Implement exponential backoff for API retries
- [ ] Add HTML description cleanup/sanitization
- [ ] Support batch queries for better performance
- [ ] Add webhook support for real-time updates (if ISD provides)
- [ ] Optimize technology queries (parallel API calls)
- [ ] Add solution detail enrichment (additional metadata)
- [ ] Integrate with main chat backend
- [ ] Create hybrid routing logic (MCP + vector search)
- [ ] Add metrics/telemetry for monitoring
- [ ] Implement rate limiting middleware

## Test Coverage

**Verified Working** (December 12, 2025):
- ✅ Menu parsing (35 industries, 3 technologies)
- ✅ Industry-based solution retrieval (85 solutions for "Managing Risk and Compliance")
- ✅ Technology-based solution retrieval (de-duplication working)
- ✅ Correct field name mapping (solutionName, orgName, url, id)
- ✅ Spotlight solutions included
- ✅ Error handling for missing industries
- ✅ Caching for menu structure

**Known Issues**:
- ⚠️ HTML descriptions need sanitization for clean display
- ⚠️ Technology queries are slow (need optimization)
- ⚠️ No retry logic for transient API failures
