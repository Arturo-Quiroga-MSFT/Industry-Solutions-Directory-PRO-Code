# VNet-Integrated Deployment with Private Endpoint

## ✅ PRODUCTION STATUS

**This is the CURRENT PRODUCTION DEPLOYMENT** of the Industry Solutions Directory chat application.

- **Architecture**: Traditional Azure Container Apps (Non-MCP)
- **Last Updated**: December 16, 2025
- **Frontend**: https://indsolse-dev-frontend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io
- **Backend**: https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io
- **Version**: v2.8 (REST API with integrated vectorization)

**Note**: This deployment does NOT use the MCP (Model Context Protocol) server. The MCP server (`mcp-isd-server/`) is a separate component for IDE/tool integration.

---

## Overview
This document describes the VNet-integrated deployment of the Industry Solutions Directory application with Azure Cosmos DB Private Endpoint connectivity. This eliminates the need for firewall IP management and provides secure, private connectivity.

## Original Deployment Date
November 7, 2025

## Architecture

### Network Configuration
- **VNet**: `indsolse-dev-vnet` (10.0.0.0/16)
- **Endpoints Subnet**: `endpoints-subnet` (10.0.1.0/24) - For private endpoints
- **Container Apps Subnet**: `aca-subnet` (10.0.2.0/23) - Delegated to Microsoft.App/environments
- **Private DNS Zone**: `privatelink.documents.azure.com`

### Container Apps Environment
- **Name**: `indsolse-dev-env-vnet`
- **Type**: VNet-integrated with infrastructure subnet
- **Location**: Sweden Central
- **Plan**: Consumption

### Private Endpoint
- **Name**: `cosmos-private-endpoint`
- **Service**: Azure Cosmos DB (indsolse-dev-db-okumlm)
- **Connection Type**: Sql (NoSQL API)
- **Status**: Cosmos DB public network access disabled

## Deployed Applications

### Backend (v2.2)
- **Name**: `indsolse-dev-backend-v2-vnet`
- **URL**: https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io
- **Image**: `indsolsedevacr.azurecr.io/industry-solutions-backend:v2.2`
- **Features**:
  - Follow-up questions generation (v2.2)
  - Conversation summary and export (v2)
  - Search URL fix (v2.1)
  - RAG pattern with Azure AI Search
  - Private Endpoint connectivity to Cosmos DB

**Environment Variables**:
```bash
AZURE_COSMOS_ENDPOINT="https://indsolse-dev-db-okumlm.documents.azure.com:443/"
AZURE_COSMOS_DB_NAME="industry-solutions"
AZURE_SEARCH_ENDPOINT="https://indsolse-dev-srch-okumlm.search.windows.net"
AZURE_SEARCH_INDEX="partner-solutions-index"
AZURE_OPENAI_ENDPOINT="https://indsolse-dev-ai-okumlm.openai.azure.com/"
AZURE_OPENAI_CHAT_MODEL="gpt-4.1-mini"
AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-3-large"
```

**Principal ID**: `d20e97c5-bbc4-48e2-a31b-10c5e7ed083b`

**RBAC Roles**:
- Cosmos DB Data Contributor
- Search Index Data Reader
- Cognitive Services OpenAI User
- AcrPull

### Frontend (v2.2)
- **Name**: `indsolse-dev-frontend-v2-vnet`
- **URL**: https://indsolse-dev-frontend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io
- **Image**: `indsolsedevacr.azurecr.io/industry-solutions-frontend:v2.2`
- **Features**:
  - Clickable follow-up question buttons (v2.2)
  - Summary generation UI (v2)
  - Conversation download (markdown/text) (v2)
  - Search URL citation links (v2.1)

**Environment Variables**:
```bash
BACKEND_URL="https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io"
```

**Principal ID**: `cbc196c0-9bdf-4831-8b6c-7a7e3e0c8681`

**RBAC Roles**:
- AcrPull

## Deployment Scripts

### 1. setup-private-endpoint.sh
Creates the Private Endpoint infrastructure:
- VNet with subnets
- Private Endpoint for Cosmos DB
- Private DNS Zone and DNS Zone Group
- Disables Cosmos DB public network access

**Usage**:
```bash
./deployment/setup-private-endpoint.sh
```

### 2. recreate-aca-with-vnet.sh
Creates VNet-integrated Container Apps environment and deploys applications:
- Creates new Container Apps environment with VNet integration
- Deploys backend and frontend apps
- Configures all RBAC permissions
- Preserves old environment for rollback

**Usage**:
```bash
./deployment/recreate-aca-with-vnet.sh
```

**Note**: Script requires manual fix for OpenAI resource name (`indsolse-dev-ai-okumlm` vs `indsolse-dev-aoai`)

## Health Check

Backend health endpoint confirms all services are operational:

```bash
curl https://indsolse-dev-backend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io/api/health
```

**Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "dependencies": {
        "azure_ai_search": "healthy",
        "azure_openai": "healthy",
        "azure_cosmos_db": "healthy"
    }
}
```

## Benefits

### Security
- ✅ Private connectivity to Cosmos DB
- ✅ No public database access
- ✅ VNet-isolated traffic
- ✅ Traffic never leaves Azure backbone

### Reliability
- ✅ No firewall IP management needed
- ✅ Works regardless of container restarts
- ✅ Azure Policy cannot break connectivity
- ✅ No more `fix-cosmos-network.sh` script needed

### Features
- ✅ AI-generated follow-up questions (v2.2)
- ✅ Clickable question buttons (v2.2)
- ✅ Conversation summary generation (v2)
- ✅ Markdown/text export (v2)
- ✅ Working search URLs for solutions (v2.1)

## Cost Impact

| Resource | Monthly Cost (Estimate) |
|----------|------------------------|
| VNet | Free |
| Private Endpoint | ~$7.30 |
| Container Apps Environment | Minimal increase (still Consumption plan) |
| **Total Additional** | **~$7-10/month** |

## Previous Deployment (Still Active)

The original non-VNet deployment is still running for rollback:

- **Environment**: `indsolse-dev-env`
- **Backend**: https://indsolse-dev-backend-v2.redplant-675b33da.swedencentral.azurecontainerapps.io
- **Frontend**: https://indsolse-dev-frontend-v2.redplant-675b33da.swedencentral.azurecontainerapps.io
- **Status**: Active with v2.1 (urlfix revision)
- **Issue**: Requires `fix-cosmos-network.sh` for firewall IP management

## Migration Notes

### DNS Resolution
Cosmos DB hostname resolves differently inside and outside the VNet:
- **Outside VNet**: Resolves to public IP (access denied)
- **Inside VNet**: Resolves to private IP (10.0.1.x) via Private DNS Zone
- **Result**: Apps in VNet connect privately; laptop still uses public access

### Cleanup Considerations
After confirming VNet deployment is stable:
1. Can delete old Container Apps environment: `indsolse-dev-env`
2. Can delete old Container Apps: `indsolse-dev-backend-v2`, `indsolse-dev-frontend-v2`
3. Should keep VNet deployment as primary

## Troubleshooting

### Backend Activation Failed
**Issue**: Missing environment variables

**Solution**: Run `az containerapp update` with all required env vars

### OpenAI Resource Not Found
**Issue**: Script uses incorrect resource name `indsolse-dev-aoai`

**Actual name**: `indsolse-dev-ai-okumlm`

**Solution**: Manually assign RBAC role:
```bash
az role assignment create \
  --assignee <PRINCIPAL_ID> \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/7a28b21e-0d3e-4435-a686-d92889d4ee96/resourceGroups/indsolse-dev-rg/providers/Microsoft.CognitiveServices/accounts/indsolse-dev-ai-okumlm"
```

### Subnet Delegation Error
**Issue**: Subnet not delegated to Microsoft.App/environments

**Solution**:
```bash
az network vnet subnet update \
  --resource-group indsolse-dev-rg \
  --vnet-name indsolse-dev-vnet \
  --name aca-subnet \
  --delegations Microsoft.App/environments
```

## Testing Follow-Up Questions Feature

1. Open frontend: https://indsolse-dev-frontend-v2-vnet.icyplant-dd879251.swedencentral.azurecontainerapps.io
2. Ask a question (e.g., "What AI solutions are available for healthcare?")
3. After response, observe 3-4 follow-up question buttons
4. Click any button - question is automatically sent as new message
5. Backend generates contextual questions based on:
   - User's original query
   - Assistant's response
   - Top solutions cited

## API Endpoints

### Backend Endpoints
- `GET /api/health` - Health check
- `POST /api/chat` - Send message (with follow-up questions in response)
- `GET /api/chat/history/{session_id}` - Get chat history
- `POST /api/chat/summary/{session_id}` - Generate conversation summary
- `GET /api/chat/export/{session_id}?format=markdown|text` - Export conversation

### Follow-Up Questions Response Format
```json
{
  "response": "Here are some AI solutions...",
  "session_id": "streamlit-abc123",
  "citations": [...],
  "message_id": "msg-xyz789",
  "follow_up_questions": [
    "Can you provide more details about the implementation process?",
    "What are the pricing models for these solutions?",
    "How do these solutions integrate with existing systems?"
  ]
}
```

## Data Models

### ChatResponse (API Response)
```python
class ChatResponse(BaseModel):
    response: str
    session_id: str
    citations: List[Citation]
    message_id: str
    follow_up_questions: Optional[List[str]] = None
```

### ChatMessage (Cosmos DB Storage)
```python
class ChatMessage(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    citations: Optional[List[Dict[str, Any]]] = None
    follow_up_questions: Optional[List[str]] = None
```

## Future Enhancements

1. **Custom Domain**: Configure custom domain for production URLs
2. **Monitoring**: Set up Azure Monitor alerts for health checks
3. **Scaling**: Configure autoscaling rules based on traffic
4. **CI/CD**: Automate deployment with GitHub Actions
5. **Testing**: Add integration tests for follow-up questions feature
6. **Analytics**: Track which follow-up questions users click most

## References

- [Azure Container Apps VNet Integration](https://learn.microsoft.com/azure/container-apps/vnet-custom)
- [Azure Private Endpoint](https://learn.microsoft.com/azure/private-link/private-endpoint-overview)
- [Azure Cosmos DB Private Link](https://learn.microsoft.com/azure/cosmos-db/how-to-configure-private-endpoints)
- [Container Apps Revisions](https://learn.microsoft.com/azure/container-apps/revisions)
