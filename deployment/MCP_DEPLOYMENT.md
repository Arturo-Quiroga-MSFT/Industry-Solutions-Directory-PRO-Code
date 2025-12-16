# ISD MCP Server - Azure Container Apps Deployment

This guide covers deploying the Industry Solutions Directory (ISD) MCP Server to Azure Container Apps and connecting it to Azure AI Foundry Agent Service.

## 📋 Overview

The MCP server wraps the ISD API to provide structured tools for AI agents to discover and retrieve Microsoft partner solutions in real-time.

**Deployment Date**: December 15, 2025  
**Author**: Arturo Quiroga, Principal Industry Solutions Architect

## 🏗️ Architecture

```
┌─────────────────────────┐
│ Azure AI Foundry Agent  │
│   (GPT-4, etc.)        │
└───────────┬─────────────┘
            │ MCP Protocol (HTTP)
┌───────────▼──────────────┐
│  ISD MCP Server          │
│  (Azure Container Apps)  │
│  - FastAPI HTTP wrapper  │
│  - MCP protocol support  │
└───────────┬──────────────┘
            │ HTTPS
┌───────────▼──────────────┐
│  ISD Production API      │
│  mssoldir-app-prd        │
└──────────────────────────┘
```

## 🚀 Deployment Steps

### Prerequisites

1. **Azure CLI** installed and logged in
   ```bash
   az login
   ```

2. **Resource Group** exists (script will create if needed)
   - Default: `indsolse-dev-rg`
   - Location: `swedencentral`

3. **Azure Container Registry** exists
   - Default: `indsolsedevacr`

### Step 1: Deploy MCP Server

Run the deployment script:

```bash
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code
./deployment/deploy-mcp-server-aca.sh
```

This script will:
1. ✅ Build Docker image from `mcp-isd-server/`
2. ✅ Push to Azure Container Registry
3. ✅ Create new Container Apps environment (`indsolse-mcp-env`)
4. ✅ Deploy MCP server container app (`indsolse-mcp-server`)
5. ✅ Configure external ingress on port 8080
6. ✅ Output server URL and test commands

**Expected Output:**
```
🚀 MCP Server URL: https://indsolse-mcp-server.<random>.swedencentral.azurecontainerapps.io
```

### Step 2: Test Deployment

Run the test script:

```bash
./deployment/test-mcp-server.sh
```

This will test:
- ✅ Health endpoint
- ✅ Server info
- ✅ List tools
- ✅ List industries
- ✅ List technologies
- ✅ Get solutions by industry
- ✅ Search solutions
- ✅ MCP protocol endpoint

### Step 3: Update (Optional)

For quick updates during development:

```bash
./deployment/update-mcp-server.sh
```

This rebuilds the image and updates the container app without recreating the environment.

## 🔗 Connect to Azure AI Foundry

### Portal Configuration

1. Go to https://ai.azure.com
2. Navigate to your AI project
3. Go to **Build** → **Tools** → **Add Custom Tool**
4. Select **Model Context Protocol**
5. Configure:

   | Field | Value |
   |-------|-------|
   | **Name** | ISD Solutions Directory |
   | **Remote MCP Server endpoint** | `https://your-mcp-server.azurecontainerapps.io/mcp` |
   | **Server Label** | `isd-server` |
   | **Authentication** | None (or configure as needed) |

6. Click **Connect**

### Python SDK Configuration

```python
from openai import AsyncAzureOpenAI
from openai.agents import Agent, AgentRunner
from openai.agents.mcp import MCPServer

# Configure MCP server
mcp_server = MCPServer(
    server_url="https://your-mcp-server.azurecontainerapps.io/mcp",
    server_label="isd-server"
)

# Create agent with MCP tools
agent = Agent(
    name="ISD Solutions Assistant",
    instructions="""
    You are an expert at helping users find Microsoft partner solutions 
    from the Industry Solutions Directory. Use the ISD tools to:
    - List available industries and technologies
    - Find solutions by industry or technology
    - Search for specific solutions by keyword
    Always provide solution names, partner names, and URLs.
    """,
    model="gpt-4",
    mcp_servers=[mcp_server]
)

# Run queries
runner = AgentRunner(agent)
response = await runner.run("Show me AI solutions for healthcare")
print(response.content)
```

## 📊 Available MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `list_industries` | Get all industry categories | None |
| `list_technologies` | Get all technology categories | None |
| `get_solutions_by_industry` | Get solutions for a specific industry | `industry` (required) |
| `get_solutions_by_technology` | Get solutions for a specific technology | `technology` (required) |
| `search_solutions` | Search with keyword and filters | `query`, `industry`, `technology`, `limit` |

## 🧪 Example Queries

**List Industries:**
```bash
curl -X POST https://your-mcp-server.azurecontainerapps.io/tools/list_industries
```

**Get Solutions by Industry:**
```bash
curl -X POST https://your-mcp-server.azurecontainerapps.io/tools/get_solutions_by_industry \
  -H 'Content-Type: application/json' \
  -d '{"industry": "Managing Risk and Compliance"}'
```

**Search Solutions:**
```bash
curl -X POST https://your-mcp-server.azurecontainerapps.io/tools/search_solutions \
  -H 'Content-Type: application/json' \
  -d '{"query": "AI", "limit": 10}'
```

## 🔍 Monitoring

### View Logs

```bash
az containerapp logs show \
  --name indsolse-mcp-server \
  --resource-group indsolse-dev-rg \
  --follow
```

### View Metrics

```bash
az monitor metrics list \
  --resource "/subscriptions/<subscription-id>/resourceGroups/indsolse-dev-rg/providers/Microsoft.App/containerApps/indsolse-mcp-server"
```

### Check Health

```bash
curl https://your-mcp-server.azurecontainerapps.io/health
```

## 📁 Files Created

| File | Purpose |
|------|---------|
| `mcp-isd-server/Dockerfile` | Container image definition |
| `mcp-isd-server/http_server.py` | FastAPI HTTP wrapper for MCP server |
| `deployment/deploy-mcp-server-aca.sh` | Full deployment script |
| `deployment/update-mcp-server.sh` | Quick update script |
| `deployment/test-mcp-server.sh` | End-to-end testing script |
| `deployment/mcp-deployment-info.json` | Deployment metadata (created after deployment) |

## ⚙️ Configuration

### Resource Scaling

Default configuration:
- **Min replicas**: 1
- **Max replicas**: 5
- **CPU**: 0.5 cores
- **Memory**: 1 GB

To modify scaling:

```bash
az containerapp update \
  --name indsolse-mcp-server \
  --resource-group indsolse-dev-rg \
  --min-replicas 2 \
  --max-replicas 10
```

### Environment Variables

Current deployment uses no environment variables. All configuration is hardcoded to ISD production API.

To add environment variables:

```bash
az containerapp update \
  --name indsolse-mcp-server \
  --resource-group indsolse-dev-rg \
  --set-env-vars "KEY1=value1" "KEY2=value2"
```

## 🔐 Security Considerations

### Current State
- ✅ HTTPS enabled by default (Container Apps)
- ✅ System-assigned managed identity created
- ⚠️ No authentication required (public endpoint)

### Recommended Enhancements

1. **Add API Key Authentication:**
   ```python
   # In http_server.py
   from fastapi import Header, HTTPException
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("MCP_API_KEY"):
           raise HTTPException(status_code=401, detail="Invalid API key")
   ```

2. **Enable Microsoft Entra ID:**
   - Configure managed identity authentication
   - Use Azure AI Foundry project identity

3. **Add Rate Limiting:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

## 🐛 Troubleshooting

### Container App Won't Start

Check logs:
```bash
az containerapp logs show --name indsolse-mcp-server --resource-group indsolse-dev-rg --tail 100
```

Common issues:
- Port mismatch (ensure `--target-port 8080` matches `EXPOSE 8080` in Dockerfile)
- Missing dependencies in requirements.txt
- Health check failing

### MCP Tools Not Working

1. Test endpoints directly:
   ```bash
   curl https://your-mcp-server.azurecontainerapps.io/tools
   ```

2. Check if ISD API is accessible:
   ```bash
   curl https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu
   ```

3. Verify MCP protocol endpoint:
   ```bash
   curl -X POST https://your-mcp-server.azurecontainerapps.io/mcp \
     -H 'Content-Type: application/json' \
     -d '{"method": "tools/list", "params": {}}'
   ```

### Azure AI Foundry Connection Issues

- Ensure server URL ends with `/mcp` (not just the base URL)
- Check authentication settings match server configuration
- Verify network connectivity from Foundry to Container Apps
- Review Foundry agent logs for error messages

## 📈 Performance

**Expected Performance:**
- Health check: < 100ms
- List industries: ~200ms (cached)
- List technologies: ~200ms (cached)
- Get solutions by industry: ~600ms (1 API call)
- Get solutions by technology: ~20-30s (35 API calls)
- Search solutions: 200ms - 30s (depending on filters)

**Optimization Tips:**
- Results are cached in memory per container instance
- For production, consider Redis for distributed caching
- Technology queries can be optimized with parallel API calls

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy MCP Server

on:
  push:
    branches: [main]
    paths:
      - 'mcp-isd-server/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy MCP Server
        run: ./deployment/deploy-mcp-server-aca.sh
```

## 📚 Related Documentation

- [MCP Server README](../mcp-isd-server/README.md)
- [MCP Server Proposal](../docs/MCP_SERVER_PROPOSAL.md)
- [ISD API Investigation](../data-ingestion/API_INVESTIGATION.md)
- [Main Architecture](../ARCHITECTURE.md)

## 🎯 Next Steps

1. ✅ Deploy MCP server to Azure Container Apps
2. ✅ Test all endpoints
3. ⏳ Connect to Azure AI Foundry
4. ⏳ Test with AI agent queries
5. ⏳ Add authentication (API key or managed identity)
6. ⏳ Implement caching with Redis
7. ⏳ Add monitoring and alerting
8. ⏳ Set up CI/CD pipeline
9. ⏳ Performance optimization
10. ⏳ Production hardening

## 💡 Tips

- Use `update-mcp-server.sh` for quick iterations during development
- Always test with `test-mcp-server.sh` after deployment
- Monitor logs during first connection to Azure AI Foundry
- Keep deployment info file for reference (`mcp-deployment-info.json`)
- Technology queries are slow - prefer industry queries when possible

## 🆘 Support

For issues or questions:
1. Check logs: `az containerapp logs show`
2. Test endpoints directly with curl
3. Review this documentation
4. Check Azure AI Foundry agent logs
5. Verify ISD API is accessible

---

**Deployment Script**: `deployment/deploy-mcp-server-aca.sh`  
**Update Script**: `deployment/update-mcp-server.sh`  
**Test Script**: `deployment/test-mcp-server.sh`  
**Last Updated**: December 15, 2025
