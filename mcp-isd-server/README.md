# MCP ISD Server

Model Context Protocol (MCP) server for the Microsoft Industry Solutions Directory (ISD).

## Overview

This MCP server wraps the ISD API to provide structured tools for AI agents to discover and retrieve partner solutions. Instead of searching an index, AI models can directly call these tools to get real-time data from the ISD website.

**Author**: Arturo Quiroga, Principal Industry Solutions Architect  
**Date**: December 12, 2025  
**Status**: Testing/Development

## Available Tools

### 1. `list_industries`
Get all available industry categories from ISD.

**Returns**: List of industry names (Financial Services, Healthcare & Life Sciences, etc.)

### 2. `list_technologies`
Get all available technology categories from ISD.

**Returns**: List of technology names (AI Business Solutions, Cloud and AI Platforms, Security, etc.)

### 3. `get_solutions_by_industry`
Get all partner solutions for a specific industry.

**Parameters**:
- `industry` (required): Industry name (e.g., "Financial Services")

**Returns**: Array of solutions with name, partner, description, industries, technologies, URL

### 4. `get_solutions_by_technology`
Get all partner solutions for a specific technology category.

**Parameters**:
- `technology` (required): Technology name (e.g., "AI Business Solutions")

**Returns**: Array of solutions with full details

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

### Test the client functions (recommended for development):

```bash
python test_client.py
```

This will run 6 tests:
1. List all industries
2. List all technologies
3. Get Financial Services solutions
4. Get AI Business Solutions
5. Search for "copilot" solutions
6. Search Healthcare for "patient" solutions

### Run as MCP server:

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
│  mssoldir-app-prd.azurewebsites.net    │
└─────────────────────────────────────────┘
```

## ISD API Endpoints Used

- `GET /api/Industry/getMenu` - Get all industries and technologies
- `GET /api/Industry/GetThemeDetalsByViewId?viewId={id}` - Get solutions for a category

## Performance Considerations

- **Caching**: Industries and technologies lists are cached after first fetch
- **Rate limiting**: No authentication required, but consider adding delays for production
- **Search performance**: `search_solutions` may fetch multiple categories (can be slow)
- **Recommended**: Use specific industry/technology filters when possible

## Example Usage in AI Conversation

**User**: "Show me AI Business Solutions"

**AI Agent**:
1. Calls `get_solutions_by_technology(technology="AI Business Solutions")`
2. Receives real-time list from ISD API
3. Presents solutions to user

**User**: "Find Healthcare solutions for patient engagement"

**AI Agent**:
1. Calls `search_solutions(query="patient engagement", industry="Healthcare & Life Sciences")`
2. Filters solutions in real-time
3. Returns relevant matches

## Next Steps

1. ✅ Create MCP server structure
2. ✅ Implement ISD API client
3. ✅ Define MCP tools
4. ✅ Create test client
5. ⏳ Test all tools work correctly
6. ⏳ Add error handling and retries
7. ⏳ Optimize caching strategy
8. ⏳ Add rate limiting
9. ⏳ Integrate into main solution
10. ⏳ Compare with vector search approach

## Related Documentation

- [MCP Server Proposal](../docs/MCP_SERVER_PROPOSAL.md) - Architecture analysis
- [ISD API Investigation](../data-ingestion/API_INVESTIGATION.md) - API endpoint documentation
- [Architecture](../ARCHITECTURE.md) - Main solution architecture

## Limitations

- No semantic/vector search (keyword matching only)
- Dependent on ISD API uptime
- Search across all categories can be slow (fetches multiple API calls)
- No built-in caching beyond in-memory during runtime

## Future Enhancements

- Add persistent caching (Redis)
- Implement exponential backoff for retries
- Add solution detail enrichment
- Support batch queries
- Add webhook support for real-time updates
- Integrate with main chat backend
