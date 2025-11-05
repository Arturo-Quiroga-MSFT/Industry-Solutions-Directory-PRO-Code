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
