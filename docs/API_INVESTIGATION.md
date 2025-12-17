# API Investigation - Industry Solutions Directory

## Investigation Date
November 5, 2025

## Website
https://solutions.microsoftindustryinsights.com

## Discovery Process

### 1. Initial Page Inspection
```bash
# Fetch the main page to see basic structure
curl -s "https://solutions.microsoftindustryinsights.com"
```

### 2. Finding JavaScript Bundles
```bash
# Search for script tags and API references in HTML
curl -s "https://solutions.microsoftindustryinsights.com" | grep -E "(script|api|data-|fetch|axios)" | head -30
```

**Result:** Found main JavaScript bundle: `main-QIRD4JU5.js`

### 3. Extracting API Endpoints from JavaScript
```bash
# Search for API endpoints in the main JavaScript bundle
curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | grep -oE '(https?://[^"'\'']+api[^"'\'']+|/api/[^"'\'']+)' | head -20
```

**Result:** Found primary API base URL: `https://mssoldir-app-prd.azurewebsites.net/api/Industry`

### 4. Testing Industry API Endpoint
```bash
# Test the Industry API and format JSON output
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry" | python3 -m json.tool | head -100
```

**Result:** Returns array of industries with sub-industries and themes

### 5. Searching for Solution/Partner Endpoints
```bash
# Look for solution or partner-related API paths
curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | grep -oE '(https?://[^"'\'']+|/api/[^"'\'']+)' | grep -i -E "(solution|partner)" | head -20
```

**Result:** Found dashboard URLs but no direct solution API endpoint yet

### 6. Testing Technology API
```bash
# Check if there's a Technology API similar to Industry API
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Technology"
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Technology" | head -50
```

**Result:** Endpoint exists but response needs further investigation

### 7. Listing All API Endpoints
```bash
# Extract all unique API endpoints from JavaScript
curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | grep -o 'mssoldir-app-prd.azurewebsites.net/api/[^"'\''[:space:]]*' | sort -u
```

**Result:** Only found `/api/Industry` endpoint so far

### 8. Analyzing Available Industries
```bash
# Get list of all industries
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry" | python3 -c "import sys, json; data=json.load(sys.stdin); print('Total industries:', len(data)); print('Industry names:'); [print(f\"  - {i['industryName']}\") for i in data[:10]]"
```

**Result:** 10 industries total:
- Defense Industrial Base
- Education
- Energy & Resources
- Financial Services
- Healthcare & Life Sciences
- Manufacturing & Mobility
- Media & Entertainment
- Retail & Consumer Goods
- State & Local Government
- Telecommunications

## Discovered API Endpoints

### Primary API Base
```
https://mssoldir-app-prd.azurewebsites.net/api/
```

### Known Endpoints

#### 1. Industry Endpoint
```
GET https://mssoldir-app-prd.azurewebsites.net/api/Industry
```

**Response Structure:**
```json
[
  {
    "industryId": "uuid",
    "industryName": "string",
    "industryDescription": "string",
    "status": "string",
    "subIndustries": [
      {
        "industryId": "uuid",
        "subIndustryId": "uuid",
        "industryThemeId": "uuid",
        "industryName": "string",
        "subIndustryName": "string",
        "theme": "string",
        "status": "string",
        "isPublished": "string",
        "industryThemeDesc": "html_content"
      }
    ]
  }
]
```

#### 2. Technology Endpoint
```
GET https://mssoldir-app-prd.azurewebsites.net/api/Technology
```
**Status:** Exists but needs further investigation

## SOLUTION FOUND! ✅

### Working Endpoints

#### 1. Menu/Navigation Structure
```bash
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu"
```
Returns complete industry hierarchy with slugs needed for fetching solutions.

#### 2. Theme Details with Partner Solutions
```bash
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug={industryThemeSlug}"
```

**Response Structure:**
```json
{
  "themeSolutionAreas": [
    {
      "solutionAreaName": "AI Business Solutions",
      "partnerSolutions": [
        {
          "partnerSolutionTitle": "Solution Name",
          "companyName": "Partner Company",
          "solutionDescription": "Description text...",
          "partnerSolutionUrl": "https://...",
          "logoUrl": "https://...",
          "partnerId": "uuid",
          "partnerSolutionId": "uuid"
        }
      ]
    }
  ],
  "spotLightPartnerSolutions": [...]
}
```

### Working Flow

1. **Get Menu** → Extract all `industryThemeSlug` values
2. **For each slug** → Call `GetThemeDetalsByViewId?slug={slug}`
3. **Parse** → Extract solutions from `themeSolutionAreas[].partnerSolutions[]`

### Test Results (November 5, 2025)
- ✅ Successfully scraped 12 solutions from 2 industries
- ✅ Generated 32 document chunks with embeddings
- ✅ Indexed into Azure AI Search
- ⚠️ Solution names showing as "Unknown Solution" - field name verification needed

---

## API Update - December 12, 2025

### Critical Finding: Corrected Field Names & Structure

After deep investigation for MCP server development, discovered the **actual field names** differ from initial investigation:

#### Correct Solution Field Names
```json
{
  "solutionName": "Solution Title",        // NOT partnerSolutionTitle
  "orgName": "Partner Company Name",       // NOT companyName
  "solutionDescription": "Description...",  // Correct
  "url": "https://...",                    // NOT partnerSolutionUrl
  "logoUrl": "https://...",                // Correct
  "id": "uuid"                             // NOT partnerSolutionId
}
```

#### Complete API Response Structure
```json
{
  "themeSolutionAreas": [
    {
      "solutionAreaId": "uuid",
      "solutionAreaName": "AI Business Solutions",
      "partnerSolutions": [
        {
          "id": "uuid",
          "solutionName": "Actual solution title",
          "orgName": "Partner company",
          "solutionDescription": "Full description text",
          "url": "https://partner-solution-url",
          "logoUrl": "https://logo-url",
          "industries": ["Industry1", "Industry2"],
          "technologies": ["Tech1", "Tech2"]
        }
      ]
    }
  ],
  "spotLightPartnerSolutions": [
    // Same structure as partnerSolutions
  ]
}
```

### Menu Structure Deep Dive

The menu API returns a nested hierarchy:

```json
[
  {
    "industryId": "uuid",
    "industryThemeId": "uuid or 00000000-0000-0000-0000-000000000000",
    "industryName": "Energy & Resources",
    "industrySlug": "energy--resources",
    "industryThemeSlug": "theme-slug-for-main-industry",
    "hasMultipleThme": true,
    "hasSubMenu": true,
    "subIndustries": [
      {
        "subIndustryId": "uuid",
        "subIndustryName": "Advance Your Net-Zero Journey",
        "subIndustrySlug": "advance-your-net-zero-journey",
        "industryThemeId": "uuid",
        "industryThemeSlug": "reach-net-zero-commitments-571",
        "solutionAreas": [
          {
            "industryThemeId": "uuid",
            "solutionAreaId": "uuid",
            "solutionAreaName": "AI Business Solutions",
            "industryThemeSlug": "reach-net-zero-commitments-571"
          }
        ]
      }
    ]
  }
]
```

### Key Insights

1. **Technologies are NOT a separate API dimension**
   - Technologies appear as `solutionAreas` within industry themes
   - Same solution can appear under multiple solution areas
   - Cannot query by technology alone - must query industry theme first

2. **Industry Hierarchy**
   - Top level: 10 main industries (Education, Financial Services, etc.)
   - Second level: ~36 sub-industries/use cases (Student Success, Net-Zero Journey, etc.)
   - Third level: 3 solution areas per theme (AI Business, Cloud & AI, Security)

3. **Query Parameters**
   - Endpoint uses `slug` parameter, **NOT** `viewId`
   - Must use `industryThemeSlug` from menu response
   - Format: `GetThemeDetalsByViewId?slug={industryThemeSlug}`

4. **Solution Distribution**
   - Solutions organized by solution area (technology)
   - Each solution includes both `industries[]` and `technologies[]` arrays
   - Same solution ID can appear under multiple themes (duplicates)

### Verified Working Flow (December 2025)

1. **Get menu structure**
   ```bash
   curl "https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu"
   ```

2. **Parse industries and use cases**
   - Extract all `subIndustries[].industryThemeSlug` values
   - Also extract `industryThemeSlug` from top-level industries (if not null GUID)

3. **Fetch solutions for each theme**
   ```bash
   curl "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug=improve-operational-efficiencies-for-modernized-school-experiences-850"
   ```

4. **Parse response**
   - Iterate `themeSolutionAreas[]`
   - For each area, extract `partnerSolutions[]`
   - Use correct field names: `solutionName`, `orgName`, `solutionDescription`

### Example: Fetching Education Solutions

```bash
# Get Education -> Institutional Innovation solutions
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug=improve-operational-efficiencies-for-modernized-school-experiences-850" | python3 -m json.tool
```

**Response includes:**
- `themeSolutionAreas[0].solutionAreaName`: "AI Business Solutions"
- `themeSolutionAreas[0].partnerSolutions[]`: Array of solutions with correct field names
- `themeSolutionAreas[1].solutionAreaName`: "Cloud and AI Platforms"
- `themeSolutionAreas[2].solutionAreaName`: "Security"

### Data Refresh Statistics (December 12, 2025)
- Total menu items: 10 main industries
- Parsed use cases: 36 sub-industries/themes
- Technology areas: 3 (AI Business Solutions, Cloud and AI Platforms, Security)
- Unique solutions indexed: 490 with content (from 539 unique after de-duplication)
- Total API entries: 700 (before de-duplication)

### MCP Server Implementation Notes

For the Model Context Protocol (MCP) server wrapping this API:

1. **Cache the menu** - Only fetch once per session
2. **Parse hierarchically** - Industries → Sub-Industries → Solution Areas
3. **Use slug for queries** - Always use `industryThemeSlug` parameter
4. **De-duplicate solutions** - Same solution ID appears under multiple themes
5. **Field name mapping**:
   - `solutionName` (NOT partnerSolutionTitle)
   - `orgName` (NOT companyName)
   - `url` (NOT partnerSolutionUrl)
   - `id` (NOT partnerSolutionId)

### Performance Considerations

- Menu API: Fast (~200ms)
- Theme details API: Moderate (~500-800ms per theme)
- Full scrape: ~36 API calls for all themes (assuming one call per sub-industry)
- Recommend: Cache aggressively, implement rate limiting for production use



---

## API Discovery Update - December 16, 2025

### Comprehensive Endpoint Discovery Results

**Discovery Method**: Systematic testing of potential API endpoints and parameters using automated script.

#### ✅ **Confirmed Working Endpoints**

1. **GET /api/Industry** - Returns root Industry data (200)
2. **GET /api/Industry/getMenu** - Complete navigation hierarchy (200)
3. **GET /api/Industry/GetThemeDetalsByViewId?slug={slug}** - Theme details (200 with valid slug)
4. **GET /api/Industry/GetPartnerSolutions** 🆕
   - Accepts: `partnerId` or `solutionId` parameters
   - Returns: Solution array (empty without valid ID)

#### ❌ **Not Available** (404)
- /api/Technology, /api/Partner, /api/Solution, /api/Search
- Industry methods: GetAll, GetById, Search, Filter, Query

### Discovery Script Created
- **Location**: `data-ingestion/api_endpoint_discovery.py`
- **Run**: `python3 api_endpoint_discovery.py`
- **Results**: `api_discovery_results.json`

### Questions for ISD Team (Meeting Follow-up)
1. Master data views from Santhanaraj?
2. GetPartnerSolutions valid ID formats?
3. Search/filter endpoints planned?
4. Complete API documentation/Swagger?
5. Internal data endpoints (consumption credit, incentive status)?

**Last Updated**: December 16, 2025

