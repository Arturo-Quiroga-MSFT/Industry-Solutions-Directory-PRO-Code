
## Demo Flow Order

### 1. **Start with Overview** (2-3 minutes)
- **README.md** - Project introduction and quick start
- **PROJECT_SUMMARY.md** or **AQ_SUMMARY.md** - High-level business context
- **Key points to mention:**
  - This is an AI-powered search solution for Microsoft's Industry Solutions Directory
  - Combines Azure AI Search with Azure OpenAI for intelligent Q&A
  - Production-ready with enterprise features (auth, monitoring, updates)

### 2. **Architecture Deep Dive** (5 minutes)
- **ARCHITECTURE.md** - Show the system design
- **CURRENT_ARCHITECTURE.md** or **ARCHITECTURE_DIAGRAMS.md** - Visual representations
- **Key points to mention:**
  - Backend API (FastAPI) with streaming responses
  - Frontend (Streamlit) for user interface
  - Azure AI Search with integrated vectorization
  - Azure OpenAI for embeddings and chat completions
  - Cosmos DB for conversation history
  - Container Apps for hosting

### 3. **Data Ingestion Pipeline** (3-4 minutes)
- **README.md** - Overview of the ingestion process
- **integrated-vectorization** folder - Show the pipeline scripts:
  - `01_export_to_blob.py` - Data extraction
  - `02_create_index.py` - Index setup
  - `03_create_skillset.py` - AI enrichment
  - `04_create_indexer.py` - Automated updates
- **Key points to mention:**
  - Automated data pipeline from ISD website
  - Integrated vectorization using Azure AI Search skillsets
  - No manual embedding generation needed
  - Partner and solution metadata enrichment

### 4. **Backend API** (4-5 minutes)
- **main.py** - Core API endpoints
- **services** - Show key services (search, chat)
- **api** - API routes
- **Key points to mention:**
  - RESTful API with streaming support
  - Azure OpenAI integration for chat
  - Hybrid search (vector + keyword)
  - Conversation history management
  - Authentication with Azure AD

### 5. **Frontend Interface** (2-3 minutes)
- **streamlit_app.py** - User interface
- **Key points to mention:**
  - Clean, intuitive Streamlit interface
  - Real-time streaming responses
  - Conversation history with Cosmos DB
  - Source citations and partner information

### 6. **Monitoring & Updates** (3 minutes)
- **update-monitor** - Automated monitoring
- **function_app.py** - Show the logic
- **Key points to mention:**
  - Scheduled function checks for website updates
  - Triggers re-indexing automatically
  - Keeps search index fresh with latest data
  - Email notifications for updates

### 7. **Deployment** (3-4 minutes)
- **deploy-v2.9-full.sh** or **deploy-aca-v2.sh** - Full deployment script
- **main.bicep** - Infrastructure as Code
- **DEPLOYMENT_GUIDE.md** - Deployment documentation
- **Key points to mention:**
  - Containerized deployment to Azure Container Apps
  - Infrastructure as Code with Bicep
  - One-command deployment script
  - Private networking with VNet integration

### 8. **Sample Queries & Results** (2 minutes)
- **SAMPLE_QUESTIONS.md** - Example queries the system handles
- Run a live demo if possible
- **Key points to mention:**
  - Natural language queries
  - Industry-specific searches
  - Partner capability matching
  - Conversational follow-ups

## Quick 10-Minute Version
1. README.md (30 sec)
2. ARCHITECTURE.md (2 min)
3. data-ingestion/integrated-vectorization/ (2 min)
4. main.py (2 min)
5. streamlit_app.py (1 min)
6. azure-functions/update-monitor/ (1 min)
7. deployment/ scripts (1 min)
8. Live demo or SAMPLE_QUESTIONS.md (30 sec)

## Key Talking Points Throughout
- **Enterprise-ready**: Authentication, monitoring, automated updates
- **Azure-native**: Leverages Azure AI Search, OpenAI, Cosmos DB, Container Apps
- **Production patterns**: IaC, containerization, CI/CD ready
- **Cost-effective**: Serverless functions, container apps with autoscaling
- **Maintainable**: Automated data refresh, clear documentation