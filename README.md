# Industry Solutions Directory - AI Chat Assistant

A pro-code solution to add intelligent chat capabilities to the Microsoft Industry Solutions Directory website using Azure AI services and the RAG (Retrieval-Augmented Generation) pattern.

## Overview

This solution enables natural language search and partner recommendations through a conversational AI interface integrated into the existing Industry Solutions Directory website at `https://solutions.microsoftindustryinsights.com/dashboard`.

### Key Features

- **Natural Language Search**: Users can ask questions in plain English about partner solutions
- **Contextual Recommendations**: AI-powered matching of user needs with relevant solutions
- **Multi-Industry Support**: Filter by industry categories (Healthcare, Financial Services, Retail, etc.)
- **Technology Filtering**: Search by technology stack (AI, Cloud, Security, etc.)
- **Conversation Memory**: Maintains context across multiple turns
- **Source Citations**: Provides links to actual partner solutions

## Architecture

The solution uses a modern RAG architecture with the following components:

### Backend (Python FastAPI)
- REST API for chat interactions
- Integration with Azure OpenAI for LLM capabilities
- Azure AI Search for hybrid vector + keyword search
- Azure Cosmos DB for conversation persistence

### Frontend (JavaScript Widget)
- Lightweight embeddable chat widget
- Can be integrated via simple `<script>` tag
- Responsive design for desktop and mobile

### Data Pipeline
- Web scraping and indexing scripts
- Automated chunking and vectorization
- Scheduled updates for fresh content

## Project Structure

```
Industry-Solutions-Directory-PRO-Code/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── services/          # Azure service integrations
│   │   │   ├── search_service.py     # Azure AI Search
│   │   │   ├── openai_service.py     # Azure OpenAI
│   │   │   └── cosmos_service.py     # Azure Cosmos DB
│   │   ├── models/            # Data models
│   │   ├── config.py          # Configuration
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
├── frontend/                  # Chat widget (JavaScript/React)
│   ├── src/
│   ├── package.json
│   └── README.md
├── data-ingestion/           # Data scraping and indexing
│   ├── ingest_data.py        # Main ingestion script
│   └── requirements.txt
├── infra/                    # Infrastructure as Code (Bicep)
│   ├── main.bicep           # Main infrastructure template
│   ├── parameters/          # Environment-specific parameters
│   └── modules/             # Bicep modules
├── .github/workflows/        # CI/CD pipelines
│   └── deploy.yml
├── docs/                     # Additional documentation
├── discovery-meeting/        # Project discovery notes
├── ARCHITECTURE.md           # Detailed architecture documentation
└── README.md                # This file
```

## Prerequisites

- **Azure Subscription** with the following services:
  - Azure OpenAI Service
  - Azure AI Search (Standard tier or higher)
  - Azure Cosmos DB for NoSQL
  - Azure App Service or Container Apps
  - Azure Key Vault (recommended)

- **Development Tools**:
  - Python 3.11+
  - Node.js 18+ (for frontend widget)
  - Azure CLI
  - Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Industry-Solutions-Directory-PRO-Code.git
cd Industry-Solutions-Directory-PRO-Code
```

### 2. Set Up Azure Resources

#### Option A: Using Bicep (Recommended)

```bash
cd infra
az login
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters parameters/dev.parameters.json
```

#### Option B: Manual Setup

Create the following Azure resources manually through the Azure Portal:
1. Azure OpenAI Service with deployments:
   - `gpt-4.1-mini` (or `gpt-4o`)
   - `text-embedding-3-large`
2. Azure AI Search (Standard tier)
3. Azure Cosmos DB for NoSQL (Serverless)
4. Azure App Service (B1 or higher)

### 3. Configure Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your Azure service endpoints and keys:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4-1-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-key-here
AZURE_SEARCH_INDEX_NAME=partner-solutions-index

# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_COSMOS_KEY=your-key-here
AZURE_COSMOS_DATABASE_NAME=industry-solutions-db
AZURE_COSMOS_CONTAINER_NAME=chat-sessions
```

### 4. Run Data Ingestion

Index partner solution data into Azure AI Search:

```bash
cd data-ingestion
pip install -r requirements.txt
python ingest_data.py
```

> **Note**: The current implementation includes sample data. You'll need to implement the actual web scraping logic based on the website's structure.

### 5. Run the Backend API Locally

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 6. Test the API

```bash
# Health check
curl http://localhost:8000/api/health

# Chat request
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What healthcare AI solutions are available?",
    "filters": {
      "industries": ["Healthcare & Life Sciences"]
    }
  }'
```

### 7. Build and Deploy Frontend Widget

```bash
cd frontend
npm install
npm run build
```

Deploy the built widget to Azure CDN or Static Web Apps.

### 8. Integrate into Existing Website

Add the following code to the Industry Solutions Directory website:

```html
<!-- Add before closing </body> tag -->
<script src="https://your-cdn.azureedge.net/chat-widget.js"></script>
<script>
  window.IndustrySolutionsChat.init({
    apiEndpoint: 'https://your-api.azurewebsites.net',
    theme: 'auto',
    primaryColor: '#0078d4',
    position: 'bottom-right'
  });
</script>
```

## API Endpoints

### `POST /api/chat`
Main chat endpoint for user queries.

**Request:**
```json
{
  "message": "What partners offer financial services solutions?",
  "session_id": "optional-session-id",
  "filters": {
    "industries": ["Financial Services"],
    "technologies": ["AI"]
  }
}
```

**Response:**
```json
{
  "response": "Based on your query, I found several financial services solutions...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "citations": [
    {
      "solution_name": "Financial Risk Management Suite",
      "partner_name": "FinTech Solutions Corp",
      "description": "Advanced risk management...",
      "url": "https://solutions.example.com/...",
      "relevance_score": 0.95
    }
  ],
  "message_id": "msg-12345"
}
```

### `GET /api/chat/history/{session_id}`
Retrieve chat history for a session.

### `POST /api/feedback`
Submit user feedback on responses.

### `GET /api/health`
Health check endpoint for monitoring.

## Configuration

All configuration is managed through environment variables. See `backend/app/config.py` for available settings.

### Key Settings

- `MAX_HISTORY_MESSAGES`: Number of conversation turns to keep in context (default: 10)
- `MAX_CONTEXT_TOKENS`: Maximum tokens for RAG context (default: 4000)
- `TEMPERATURE`: LLM temperature for response generation (default: 0.7)
- `SEARCH_TOP_K`: Number of search results to retrieve (default: 5)

## Deployment

### Deploy to Azure App Service

```bash
cd backend

# Create a web app
az webapp up \
  --name industry-solutions-chat-api \
  --resource-group your-rg \
  --runtime "PYTHON:3.11" \
  --sku B1

# Configure app settings
az webapp config appsettings set \
  --name industry-solutions-chat-api \
  --resource-group your-rg \
  --settings @appsettings.json
```

### Deploy with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) for automated deployment.

1. Add Azure credentials as GitHub secrets
2. Push to `main` branch to trigger deployment

## Monitoring & Observability

The solution includes:

- **Application Insights** integration for telemetry
- **Structured logging** with correlation IDs
- **Health check endpoints** for service monitoring
- **Error tracking** and alerting

View logs and metrics in Azure Portal > Application Insights.

## Cost Estimation

### Monthly Costs (Low to Medium Traffic)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| Azure OpenAI | GPT-4.1-mini (~500K tokens/day) | $150-300 |
| Azure OpenAI | Embeddings (~100K tokens/day) | $10-20 |
| Azure AI Search | Standard S1 | $250 |
| Azure Cosmos DB | Serverless (10GB, 1M RUs) | $25-50 |
| Azure App Service | B1 Basic | $13 |
| Application Insights | Basic | $5-20 |
| **Total** | | **$453-653/month** |

### Cost Optimization Tips

1. Use `gpt-4.1-nano` for simpler queries (80% cheaper)
2. Implement response caching for common questions
3. Use Cosmos DB serverless for variable traffic
4. Start with AI Search Basic tier for < 1000 queries/day

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint
pylint app/
```

## Troubleshooting

### Common Issues

**Issue**: Search returns no results
- **Solution**: Verify the index exists and contains data. Run data ingestion script.

**Issue**: OpenAI API rate limit errors
- **Solution**: Implement retry logic with exponential backoff (included in code)

**Issue**: CORS errors from frontend
- **Solution**: Add your website domain to `cors_origins` in `config.py`

### Debug Mode

Enable debug logging:

```bash
export DEBUG=True
python -m app.main
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Team & Contact

- **Technical Lead**: Arturo Quiroga
- **Product Owner**: Will Casavan
- **Development Team**: Jason, Thomas, Arturo

For questions or support, contact the team via Microsoft Teams.

## License

This project is proprietary and confidential.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Azure AI Services](https://azure.microsoft.com/services/ai-services/)
- Based on Microsoft RAG best practices

## Next Steps

After initial deployment:

1. **Gather User Feedback**: Collect usage data and user satisfaction metrics
2. **Optimize Prompts**: Refine system prompts based on real queries
3. **Add Features**: Implement voice interface, multi-language support
4. **Scale Infrastructure**: Adjust based on traffic patterns
5. **Enhance Search**: Implement agentic retrieval for complex queries

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed architecture documentation
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [RAG Pattern Overview](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)
