# Data Ingestion Script

This script scrapes partner solutions from the Industry Solutions Directory website and indexes them in Azure AI Search with vector embeddings for semantic search.

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
