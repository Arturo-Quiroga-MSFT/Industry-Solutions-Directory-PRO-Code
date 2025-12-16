# Quick Start: Connect ISD MCP Server to Azure AI Foundry

**MCP Server URL**: `https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io`

---

## 🚀 Steps to Connect

### 1. Open Azure AI Foundry
Go to: **https://ai.azure.com**

### 2. Add MCP Tool

**Navigation**: Build → Tools → + Add tool → Custom → Model Context Protocol

**Configuration**:
```
Name: ISD Solutions Directory
Remote MCP Server endpoint: https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/mcp
Server Label: isd-server
Authentication: None
```

Click **Connect**

### 3. Create Agent

**Navigation**: Build → Agents → Create agent

**Agent Configuration**:
```
Name: ISD Solutions Assistant
Model: gpt-4 or gpt-4-turbo

Instructions:
You are an expert assistant for the Microsoft Industry Solutions Directory.

Use the ISD MCP tools to help users discover Microsoft partner solutions:
- Use list_industries to show available industry categories (35 total)
- Use list_technologies to show technology areas (AI, Cloud, Security)
- Use get_solutions_by_industry when users ask about specific industries
- Use search_solutions to find solutions by keywords

Always provide:
- Solution name
- Partner company name  
- Brief description
- URL link to the solution

Be helpful and concise.

Tools: ✅ ISD Solutions Directory
```

Click **Create**

---

## 💬 Sample Queries to Test

### Query 1: List Industries
```
What industries are available in the directory?
```
**Expected**: Agent calls `list_industries` and returns 35 industry categories

### Query 2: Get Solutions by Industry  
```
Show me solutions for Managing Risk and Compliance
```
**Expected**: Agent calls `get_solutions_by_industry("Managing Risk and Compliance")` and returns ~85 solutions

### Query 3: Technology Focus
```
What AI Business Solutions are available?
```
**Expected**: Agent calls `get_solutions_by_technology("AI Business Solutions")`

### Query 4: Specific Use Case
```
Find solutions for Student Success in education
```
**Expected**: Agent calls `get_solutions_by_industry("Student Success")` and returns 2 solutions

### Query 5: Search
```
Show me all solutions related to healthcare
```
**Expected**: Agent calls `search_solutions(query="healthcare")`

---

## 🔧 Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| **list_industries** | Get all 35 industry categories | None |
| **list_technologies** | Get all 3 technology areas | None |
| **get_solutions_by_industry** | Get solutions for specific industry | `industry` (string) |
| **get_solutions_by_technology** | Get solutions for specific technology | `technology` (string) |
| **search_solutions** | Search with keywords and filters | `query`, `industry`, `technology`, `limit` |

---

## 📊 What You Can Expect

- **35 Industry Categories** (e.g., Managing Risk and Compliance, Student Success, etc.)
- **3 Technology Areas** (AI Business Solutions, Cloud and AI Platforms, Security)
- **Real-time data** directly from ISD Production API
- **No indexing lag** - always current solutions
- **~200ms response time** for industry queries
- **Rich solution data**: name, partner, description, URL, logo

---

## 🎯 Use Cases

1. **Discovery**: "What types of solutions are available?"
2. **Industry-specific**: "Show me retail solutions"
3. **Technology-focused**: "What AI solutions exist?"
4. **Partner research**: "Solutions for financial services compliance"
5. **Quick lookup**: "Find solutions by Nerdio"

---

## 📝 Notes

- Server is public (no authentication required currently)
- Deployed on Azure Container Apps in Sweden Central
- Auto-scaling: 1-5 replicas
- Health monitoring: `/health` endpoint
- Full API docs: `https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/`

---

## 🆘 Troubleshooting

**Agent not finding tools?**
- Verify MCP endpoint URL ends with `/mcp`
- Check server health: `curl https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/health`

**Slow responses?**
- Technology queries scan all 35 industries (~20-30s)
- Industry queries are fast (~500ms)

**No results?**
- Check exact industry name spelling
- Use `list_industries` first to see available options

---

**Deployment Date**: December 15, 2025  
**Status**: ✅ Production Ready  
**Last Test**: All 8 tests passing
