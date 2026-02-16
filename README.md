# Industry Solutions Directory - AI Chat Assistants

**Solution Owner:** Arturo Quiroga  
**Role:** Principal Industry Solutions Architect, Microsoft  
**Purpose:** Pro-code AI chat solution enabling natural language queries against the Microsoft Industry Solutions Directory using a multi-agent NL2SQL pipeline

## Overview

Two AI-powered chat assistants — **Seller** (internal) and **Customer** (external) — that let users ask natural language questions about Microsoft partner solutions. The backend translates questions directly into SQL queries against the ISD production database, returning structured results with AI-generated insights.

**Live Apps** (Azure Container Apps, Sweden Central):

| App | Frontend | Backend |
|-----|----------|---------|
| **Seller** | [isd-chat-seller-frontend](https://isd-chat-seller-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io) | [isd-chat-seller-backend](https://isd-chat-seller-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io) |
| **Customer** | [isd-chat-customer-frontend](https://isd-chat-customer-frontend.kindfield-353d98ed.swedencentral.azurecontainerapps.io) | [isd-chat-customer-backend](https://isd-chat-customer-backend.kindfield-353d98ed.swedencentral.azurecontainerapps.io) |

### Seller vs Customer Mode

- **Seller mode** — For internal Microsoft sellers. Shows partner names, rankings, solution counts by vendor, and competitive insights.
- **Customer mode** — For external customers. Neutral, capability-focused responses. No partner rankings or vendor endorsements (legal compliance).

The mode is controlled by the `APP_MODE` environment variable (`seller` or `customer`).

### Key Features

- **Natural Language to SQL**: Ask questions in plain English; the multi-agent pipeline generates and executes SQL automatically
- **Four-Agent Architecture**: Query Planner → SQL Executor → Insight Analyzer → Response Formatter
- **448 Solutions**: Across 174 partners, 50+ industries, 3 solution areas (AI Business Solutions, Cloud and AI Platforms, Security)
- **Conversation Memory**: Maintains context across turns with intent routing
- **Data Tables + Insights**: Returns both structured tabular data and AI-generated narrative analysis
- **Follow-up Questions**: Context-specific suggested questions based on query results
- **Export**: Conversations exportable as JSON or Markdown

## Architecture

```
User → React Frontend → FastAPI Backend → Multi-Agent Pipeline → SQL Database
                                              │
                                              ├─ Agent 1: Query Planner (intent analysis)
                                              ├─ Agent 2: NL2SQL + SQL Executor (pyodbc → SQL Server)
                                              ├─ Agent 3: Insight Analyzer (patterns, stats)
                                              └─ Agent 4: Response Formatter (narrative + citations)
                                              │
                                              └─ Azure OpenAI (gpt-4.1 for all agents)
```

### Key Components

- **Backend**: Python FastAPI with multi-agent NL2SQL pipeline
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS
- **Database**: SQL Server (`mssoldir-prd-sql.database.windows.net`) — read-only queries against `dbo.vw_ISDSolution_All` view (4,934 rows, 33 columns)
- **LLM**: Azure OpenAI (`r2d2-foundry-001.openai.azure.com`) — `gpt-4.1` deployment
- **Deployment**: Azure Container Apps (4 apps in `indsolse-dev-rg`, ACR: `indsolsedevacr`)

### Standalone Resources

These are available but **not used** by the chat apps:
- **Azure AI Search index** (`isd-solutions-v1` on `aq-mysearch001.search.windows.net`) — 449 documents with vector embeddings, available for Copilot Studio, MCP, or future integrations
- **MCP Server** (`mcp-isd-server/`) — Model Context Protocol server for IDE/tool integration

## Project Structure

```
Industry-Solutions-Directory-PRO-Code/
├── frontend-react/              # React 19 + TypeScript frontend (shared by both apps)
│   ├── src/                     # React components, API client, types
│   ├── backend/                 # FastAPI backend + multi-agent pipeline
│   │   ├── main.py              # FastAPI app with /api/query, /api/health, etc.
│   │   ├── multi_agent_pipeline.py  # 4-agent orchestrator
│   │   └── nl2sql_pipeline.py   # NL-to-SQL conversion + execution
│   ├── .env.seller              # Seller app env config
│   ├── .env.customer            # Customer app env config
│   └── Dockerfile               # Multi-stage build (Node build → nginx serve)
├── data-ingestion/
│   ├── sql-direct/              # NL2SQL pipeline (used by backend)
│   └── sql-to-search/           # SQL → Azure AI Search ingestion pipeline
│       ├── 01_create_index.py   # Create search index with vector config
│       ├── 02_ingest_from_sql.py # Read SQL → embeddings → upload
│       ├── 03_verify_index.py   # Verify index contents
│       └── README.md            # Pipeline docs, DB schema, run history
├── teams-apps/                  # Microsoft Teams Tab App packages
│   ├── seller/                  # Seller manifest + icons
│   ├── customer/                # Customer manifest + icons
│   ├── package.sh               # Build .zip packages for sideloading
│   └── README.md                # Teams deployment guide
├── deployment/                  # ACA deployment scripts
├── mcp-isd-server/              # MCP server (standalone)
├── infra/                       # Infrastructure as Code (Bicep)
├── docs/                        # Additional documentation
├── ARCHITECTURE.md              # Detailed architecture docs
└── README.md                    # This file
```

## Prerequisites

- **Azure Services**:
  - Azure OpenAI Service (with `gpt-4.1` deployment)
  - SQL Server with ISD database (read-only access)
  - Azure Container Apps environment
  - Azure Container Registry

- **Local Development**:
  - Python 3.11+
  - Node.js 18+
  - ODBC Driver 18 for SQL Server
  - Azure CLI (`az login`)

## Quick Start

### 1. Clone & Set Up

```bash
git clone https://github.com/Arturo-Quiroga-MSFT/Industry-Solutions-Directory-PRO-Code.git
cd Industry-Solutions-Directory-PRO-Code
python -m venv .venv && source .venv/bin/activate
```

### 2. Configure Environment

```bash
cd frontend-react/backend
cp .env.example .env   # or create from template below
```

Required `.env` variables:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4.1

# SQL Database (read-only)
SQL_SERVER=mssoldir-prd-sql.database.windows.net
SQL_DATABASE=mssoldir-prd
SQL_USERNAME=isdapi
SQL_PASSWORD=your-password

# App Mode
APP_MODE=seller   # or "customer"
```

### 3. Run Backend

```bash
cd frontend-react/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000` — docs at `http://localhost:8000/docs`

### 4. Run Frontend

```bash
cd frontend-react
npm install
npm run dev
```

Frontend available at `http://localhost:5173`

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/api/health

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What healthcare AI solutions are available?"}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (includes app mode) |
| `POST` | `/api/query` | Execute natural language query |
| `GET` | `/api/examples` | Get example questions by category |
| `GET` | `/api/stats` | Database statistics |
| `POST` | `/api/conversation/export` | Export conversation |

### `POST /api/query`

**Request:**
```json
{
  "question": "What partners offer financial services AI solutions?",
  "conversation_id": "optional-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "question": "...",
  "intent": { "intent": "query", "needs_new_query": true, "query_type": "specific" },
  "narrative": "AI-generated insights narrative...",
  "insights": { "overview": "...", "key_findings": [...], "follow_up_questions": [...] },
  "sql": "SELECT DISTINCT TOP 50 ...",
  "explanation": "This query finds...",
  "confidence": "high",
  "columns": ["solutionName", "orgName", ...],
  "rows": [{ "solutionName": "...", "orgName": "..." }],
  "row_count": 25,
  "usage_stats": { "total_tokens": 1500 },
  "elapsed_time": 3.2,
  "timestamp": "2026-02-16T..."
}
```

## Deployment

All four apps run on Azure Container Apps. Deployment scripts are in `deployment/`:

```bash
# Build and deploy seller backend
az acr build --registry indsolsedevacr --image isd-backend-seller:latest --file Dockerfile .
az containerapp update --name isd-chat-seller-backend --resource-group indsolse-dev-rg \
  --image indsolsedevacr.azurecr.io/isd-backend-seller:latest

# See deployment/ for full scripts
```

### Teams Integration

Teams Tab App packages are available in `teams-apps/`:

```bash
cd teams-apps && bash package.sh
# Upload isd-seller-teams-app.zip or isd-customer-teams-app.zip to Teams
```

See [teams-apps/README.md](teams-apps/README.md) for sideloading and admin center instructions.

## Data Pipeline

### SQL-to-Search Index (standalone)

A separate pipeline in `data-ingestion/sql-to-search/` reads the SQL database and populates an Azure AI Search index with vector embeddings. This index is a standalone resource, not used by the chat apps.

```bash
cd data-ingestion/sql-to-search
python 01_create_index.py    # Create index schema
python 02_ingest_from_sql.py # Ingest + embed 448 solutions
python 03_verify_index.py    # Verify search works
```

See [data-ingestion/sql-to-search/README.md](data-ingestion/sql-to-search/README.md) for full documentation.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ODBC driver not found | Install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server) |
| SQL connection timeout | Check SQL Server firewall rules allow your IP |
| Azure OpenAI 429 errors | Built-in retry logic handles rate limits; increase deployment quota if persistent |
| CORS errors from frontend | Set `ALLOWED_ORIGINS` env var to include your frontend URL |
| Blank Teams tab | Add `X-Frame-Options` header to ACA frontend (see teams-apps/README.md) |

## Team & Contact

- **Solution Owner & Technical Lead**: Arturo Quiroga, Principal Industry Solutions Architect
- **Product Owner**: Will Casavan

For questions or support, contact the team via Microsoft Teams.

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) — Detailed architecture documentation
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Complete documentation index
- [data-ingestion/sql-to-search/README.md](data-ingestion/sql-to-search/README.md) — Search index pipeline docs
- [teams-apps/README.md](teams-apps/README.md) — Teams deployment guide
- [SAMPLE_QUESTIONS.md](SAMPLE_QUESTIONS.md) — Example queries to try
