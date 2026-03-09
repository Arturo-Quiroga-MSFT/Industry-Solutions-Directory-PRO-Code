# Data Ingestion - Industry Solutions Directory

**Solution Owner:** Arturo Quiroga  
**Role:** Principal Industry Solutions Architect, Microsoft  
**Purpose:** Data ingestion pipeline to index Microsoft partner solutions from the Industry Solutions Directory into Azure AI Search for AI-powered search

---

## Directory Structure

```
data-ingestion/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── verify_index.py                # Verify indexed data
├── partner_analysis.py            # Analyze partner statistics
├── API_INVESTIGATION.md           # API discovery documentation
├── RELEVANCE_SCORE.md             # Search relevance documentation
│
├── integrated-vectorization/      # ⭐ CURRENT PRODUCTION APPROACH
│   ├── README.md
│   ├── 01_create_vectorizer.py
│   ├── 02_create_index.py
│   ├── 03_ingest_data.py
│   └── 04_test_search.py
│
├── update-monitor/                # 🔍 ISD website update checker
│   ├── README.md
│   ├── check_for_updates.py       # Check for new/modified solutions
│   └── fetch_current_solutions.py # Fetch current ISD solutions
│
├── archive/                       # Historical/archived files
│   ├── README.md
│   ├── old-manual-ingestion/      # Old client-side vectorization approach
│   ├── mcs-compatibility/         # Old MCS compatibility attempts
│   └── logs-and-output/           # Historical logs
│
└── reports/                       # Current reports and analysis
    ├── README.md
    ├── current_index_verification.txt
    ├── full_ingestion_summary.md
    └── solutions-found.json
```

---

## 🎯 Quick Start (Current Approach)

The **production approach** uses Azure AI Search **integrated vectorization** (v2.8+):

```bash
cd integrated-vectorization

# 1. Create vectorizer (one-time)
python 01_create_vectorizer.py

# 2. Create index with integrated vectorization (one-time)
python 02_create_index.py

# 3. Ingest data
python 03_ingest_data.py

# 4. Test search
python 04_test_search.py
```

**Benefits of integrated-vectorization:**
- ✅ Automatic query vectorization (no client-side embedding needed)
- ✅ Direct REST API (no Python SDK dependency issues)
- ✅ Simpler code and maintenance
- ✅ Better performance

*(The integrated-vectorization pipeline has been removed — the SQL-direct pipeline in `sql-to-search/` is the current approach.)*

---

## Current Index Statistics

- **Index Name:** `partner-solutions-integrated`
- **Documents:** 535 documents
- **Unique Solutions:** 376 partner solutions
- **Industries:** 10+ major industries covered
- **Vectorization:** Azure OpenAI text-embedding-3-large (3072 dimensions)

Run `python verify_index.py` to see current statistics.

---

## 🔍 Monitoring for Updates

The `update-monitor/` directory contains scripts to check if the ISD website has new or updated partner solutions:

```bash
cd update-monitor

# Check for new or modified solutions
python check_for_updates.py

# Fetch current solutions from ISD
python fetch_current_solutions.py --output current_solutions.json
```

**Recommended schedule:** Weekly checks (e.g., every Monday morning)

*(The update-monitor scripts have been removed. SQL view row counts can be checked via `sql-direct/check_db_state.py`.)*

---

## Historical Context

### Old Manual Approach (Archived)

The original implementation (archived in `archive/old-manual-ingestion/`) used:
- Client-side embedding generation with Python SDK
- Manual chunking and vectorization
- azure-search-documents 11.6.0 (had compatibility issues)

**Why it was replaced:**
- Python SDK incompatibility with integrated vectorization
- More complex code requiring client-side embedding
- Maintenance burden for embedding generation

*(Archive folder has been removed.)*

---

## Web Scraping Implementation

The script uses a **multi-tiered approach** to retrieve solution data:

### 1. API-First Approach
Attempts to discover and use the website's backend API endpoints:
- `/api/solutions`
- `/api/v1/solutions`
- `/api/data/solutions`

This is the preferred method as it provides structured data directly from the source.

### 2. HTML Scraping Fallback
If API discovery fails, the script falls back to scraping the rendered HTML page:
- Parses solution cards from `/browse` page
- Extracts: solution names, descriptions, partner info, URLs
- Uses BeautifulSoup4 for HTML parsing

### 3. Sample Data Fallback
If both methods fail (e.g., during development/testing), the script uses 3 sample solutions to ensure the pipeline can be tested end-to-end.

## Data Structure

Each solution is structured as:
```python
{
    "solution_name": str,          # Name of the solution
    "partner_name": str,            # Microsoft partner name
    "description": str,             # Solution description
    "industries": List[str],        # Target industries
    "technologies": List[str],      # Technologies used
    "solution_url": str,            # Link to solution details
    "full_content": str             # Full solution content
}
```

## How It Works

1. **Scrape**: Retrieves solution data from the website
2. **Chunk**: Breaks long content into 1000-character chunks
3. **Embed**: Generates vector embeddings using `text-embedding-3-large`
4. **Index**: Uploads to Azure AI Search with:
   - Vector search (semantic similarity)
   - Keyword search (BM25)
   - Filters (industry, technology, partner)
   - Facets for filtering UI

## Usage

```bash
# Set environment variables
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/"
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-3-large"

# Run the script
python data-ingestion/ingest_data.py
```

## Dependencies

- `requests` - HTTP client for API calls
- `beautifulsoup4` - HTML parsing
- `azure-search-documents` - Azure AI Search SDK
- `azure-identity` - Azure authentication

Install all dependencies:
```bash
pip install -r backend/requirements.txt
```

## Authentication

The script uses **Azure CLI authentication** (DefaultAzureCredential):
- Ensure you're logged in: `az login`
- RBAC permissions required:
  - Search Index Data Contributor
  - Search Service Contributor
  - Cognitive Services OpenAI User

## Customization

To adapt the scraper for the specific website structure:

1. **Inspect the website**: Open browser DevTools → Network tab
2. **Find API calls**: Look for XHR/Fetch requests to `/api/*` endpoints
3. **Update `api_endpoints` list** in `scrape_solutions()` method
4. **Adjust HTML selectors** in `_scrape_html_page()` if needed

### Example: Custom API Parsing

```python
def _parse_api_solutions(self, data: List[Dict]) -> List[Dict[str, Any]]:
    solutions = []
    for item in data:
        solution = {
            "solution_name": item['name'],  # Adjust field names
            "partner_name": item['partner'],
            "industries": item['industries'].split(','),  # Handle format
            # ... customize as needed
        }
        solutions.append(solution)
    return solutions
```

## Troubleshooting

### No solutions found
- Check if website structure changed
- Verify API endpoints are correct
- Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`

### Authentication errors
- Run `az login` to authenticate
- Verify RBAC role assignments
- Check service principal permissions in production

### Embedding failures
- Verify OpenAI deployment name matches
- Check quota/rate limits on OpenAI service
- Ensure embedding model is `text-embedding-3-large`

## Next Steps

Once data is indexed, you can:
1. Test search queries via Azure portal
2. Start the FastAPI backend to use the chat API
3. Integrate the chat widget into the website
