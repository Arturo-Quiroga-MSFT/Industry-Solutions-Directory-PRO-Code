# ISD Website Structure and Data Extraction

**Owner:** Arturo Quiroga, Principal Industry Solutions Architect, Microsoft  
**Purpose:** Document the Microsoft Industry Solutions Directory website structure and data extraction methodology  
**Last Updated:** November 8, 2025

---

## Overview

The Microsoft Industry Solutions Directory (ISD) is a catalog of partner solutions organized by industry, theme, and solution area. This document explains the website's structure, API endpoints, and how we extract data for indexing.

**Website URL:** https://solutions.microsoftindustryinsights.com/  
**API Base URL:** https://mssoldir-app-prd.azurewebsites.net/api/Industry

---

## Website Architecture

### Hierarchical Structure

```
Industries (e.g., Education, Healthcare, Manufacturing)
├── Sub-Industries / Themes (e.g., "Institutional Innovation")
│   └── Solution Areas (e.g., "AI Business Solutions")
│       ├── Partner Solutions (regular solutions)
│       └── Spotlight Solutions (featured solutions)
```

### Data Organization

1. **Industry Level**
   - Top-level categorization (Defense, Education, Healthcare, etc.)
   - Each industry has multiple themes/sub-industries

2. **Theme/Sub-Industry Level**
   - Specific focus areas within an industry
   - Each theme has a unique slug for API access
   - Themes contain solution areas

3. **Solution Area Level**
   - Technology or business capability categories
   - Examples: "AI Business Solutions", "Cloud and AI Platforms", "Security"

4. **Solution Level**
   - Individual partner offerings
   - Contains detailed solution information
   - Each solution has a unique ID and slug

---

## API Endpoints

### 1. Get Industry Menu
**Endpoint:** `/api/Industry/getMenu`  
**Method:** GET  
**Purpose:** Retrieve the complete industry hierarchy with themes

**Response Structure:**
```json
[
  {
    "industryId": "uuid",
    "industryName": "Education",
    "industrySlug": "education",
    "hasMultipleTheme": true,
    "hasSubMenu": true,
    "subIndustries": [
      {
        "subIndustryId": "uuid",
        "subIndustryName": "Institutional Innovation",
        "subIndustrySlug": "institutional-innovation",
        "industryThemeId": "uuid",
        "industryThemeSlug": "improve-operational-efficiencies-...",
        "solutionAreas": [
          {
            "solutionAreaId": "uuid",
            "solutionAreaName": "AI Business Solutions",
            "industryThemeSlug": "improve-operational-efficiencies-..."
          }
        ]
      }
    ]
  }
]
```

**Key Fields:**
- `industryName`: Industry display name
- `subIndustries[]`: Array of themes within the industry
- `industryThemeSlug`: Unique identifier for theme API calls
- `solutionAreas[]`: Categories within each theme

---

### 2. Get Theme Details by View ID
**Endpoint:** `/api/Industry/GetThemeDetalsByViewId`  
**Method:** GET  
**Parameters:** `?slug={industryThemeSlug}`  
**Purpose:** Retrieve all solutions for a specific theme

**Response Structure:**
```json
{
  "industryThemeId": "uuid",
  "industryThemeTitle": "Theme Title",
  "themeSolutionAreas": [
    {
      "solutionAreaId": "uuid",
      "solutionAreaName": "AI Business Solutions",
      "partnerSolutions": [
        {
          "partnerSolutionId": "uuid",
          "solutionName": "Solution Name by Partner Name",
          "solutionDescription": "<p>HTML description...</p>",
          "partnerSolutionSlug": "solution-name-by-partner-name",
          "orgName": null,  // Often empty
          "publisherName": null,  // Often empty
          // Additional metadata fields
        }
      ]
    }
  ],
  "spotLightPartnerSolutions": [
    {
      "partnerSolutionId": "uuid",
      "solutionName": "Featured Solution by Partner",
      "solutionDescription": "<p>HTML description...</p>",
      "partnerSolutionSlug": "featured-solution-by-partner",
      // Additional metadata fields
    }
  ]
}
```

**Key Fields:**
- `themeSolutionAreas[]`: Array of solution areas
- `partnerSolutions[]`: Regular solutions within each area
- `spotLightPartnerSolutions[]`: Featured/highlighted solutions
- `solutionName`: Title (format: "Solution Name by Partner Name")
- `solutionDescription`: Full HTML description
- `partnerSolutionSlug`: URL-friendly identifier

---

## Data Extraction Methodology

### Two-Phase Approach

Our data extraction follows a two-phase process:

#### Phase 1: Fetch Industry Menu
```python
GET https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu
```

**Purpose:** Discover all available themes and their slugs

**What We Extract:**
- Industry names
- Sub-industry/theme names
- Theme slugs (needed for Phase 2)
- Solution area names

#### Phase 2: Fetch Theme Details
```python
GET https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug={theme_slug}
```

**Purpose:** Get actual solution data for each theme

**What We Extract:**
- Solution IDs (unique identifier)
- Solution names/titles
- Solution descriptions (HTML format)
- Partner names (extracted from title)
- Solution URLs (constructed from slug)
- Industry and theme associations

---

## Partner Name Extraction

### Challenge
The API response often has empty or null values for `orgName` and `publisherName` fields.

### Solution
Partner names are embedded in the solution title using the pattern:
```
"Solution Name by Partner Name"
```

**Extraction Logic:**
```python
title = solution.get("solutionName", "")
if " by " in title:
    partner = title.split(" by ")[-1]
else:
    partner = solution.get("orgName") or "Unknown"
```

**Examples:**
- Title: `"greymatter Student Lifecycle CRM by Frequency Foundry"`
- Extracted Partner: `"Frequency Foundry"`

- Title: `"Azure Migration Services by Accenture"`
- Extracted Partner: `"Accenture"`

---

## Solution URL Construction

Solution detail pages follow this pattern:
```
https://solutions.microsoftindustryinsights.com/solutiondetails/{partnerSolutionSlug}
```

**Example:**
- Slug: `greymatter-student-lifecycle-crm-by-frequency-foundry`
- URL: `https://solutions.microsoftindustryinsights.com/solutiondetails/greymatter-student-lifecycle-crm-by-frequency-foundry`

---

## Data Statistics (as of November 8, 2025)

### Current Counts
- **Total Solutions:** 695
- **Unique Partners:** 158
- **Industries:** 10+
- **Themes/Sub-Industries:** 50+
- **Solution Areas:** 5-6 per theme

### Top Partners by Solution Count
1. Striim: 31 solutions
2. RSM US LLP: 30 solutions
3. Baker Hughes: 24 solutions
4. EY: 22 solutions
5. Cognizant: 18+ solutions

### Data Quality
- **Solutions with Partner Names:** ~93% (646/695)
- **Solutions as "Unknown":** ~7% (49/695)
- **HTML Descriptions:** 100% (all solutions have descriptions)

---

## Content Characteristics

### Description Format
- **Type:** HTML markup
- **Length:** Varies from 500 to 5,000+ characters
- **Common Elements:**
  - `<p>` paragraphs
  - `<ul>` and `<li>` lists
  - `<strong>` emphasis
  - Feature lists and key capabilities
  - Benefits and use cases

### Solution Naming Convention
Most solutions follow the pattern:
```
[Product/Service Name] by [Partner Company]
```

Examples:
- "CDP Data Platform by Cloudera"
- "Enterprise Resource Planning by SAP"
- "Supply Chain Management by Blue Yonder"

---

## Data Extraction Process

### Complete Workflow

1. **Initialize API Connection**
   ```python
   base_url = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
   ```

2. **Fetch Industry Menu**
   ```python
   menu = requests.get(f"{base_url}/getMenu").json()
   ```

3. **Iterate Through Hierarchy**
   ```python
   for industry in menu:
       for theme in industry["subIndustries"]:
           theme_slug = theme["industryThemeSlug"]
           # Fetch theme details...
   ```

4. **Extract Solutions**
   ```python
   theme_data = requests.get(
       f"{base_url}/GetThemeDetalsByViewId",
       params={"slug": theme_slug}
   ).json()
   
   # Process regular solutions
   for area in theme_data["themeSolutionAreas"]:
       for solution in area["partnerSolutions"]:
           # Extract solution data...
   
   # Process spotlight solutions
   for solution in theme_data["spotLightPartnerSolutions"]:
       # Extract solution data...
   ```

5. **Parse and Structure Data**
   ```python
   solution_doc = {
       "id": solution["partnerSolutionId"],
       "title": solution["solutionName"],
       "description": solution["solutionDescription"],
       "partner": extract_partner(solution["solutionName"]),
       "industry": industry["industryName"],
       "theme": theme["subIndustryName"],
       "url": construct_url(solution["partnerSolutionSlug"])
   }
   ```

---

## Update Detection

### Change Detection Strategy

We use **MD5 content hashing** to detect changes:

```python
content = json.dumps(solution_data, sort_keys=True)
content_hash = hashlib.md5(content.encode()).hexdigest()
```

### Types of Changes Detected

1. **New Solutions:** Solution ID exists in ISD but not in our index
2. **Modified Solutions:** Solution ID exists in both, but content hash differs
3. **Removed Solutions:** Solution ID exists in our index but not in ISD

### Comparison Process

```python
# Fetch current ISD solutions (with hashes)
isd_solutions = fetch_from_isd_api()

# Fetch indexed solutions (with hashes)
indexed_solutions = fetch_from_search_index()

# Compare
new = isd_ids - indexed_ids
removed = indexed_ids - isd_ids
modified = [id for id in common_ids 
            if isd_hash[id] != indexed_hash[id]]
```

---

## Integration with Azure AI Search

### Data Transformation for Indexing

Original API data is transformed for optimal search:

**From API:**
```json
{
  "partnerSolutionId": "uuid",
  "solutionName": "Solution by Partner",
  "solutionDescription": "<p>HTML content...</p>"
}
```

**To Search Index:**
```json
{
  "id": "uuid",
  "title": "Solution by Partner",
  "content": "Solution by Partner\n\nPlain text content...",
  "partner": "Partner",
  "industry": "Education",
  "theme": "Institutional Innovation",
  "source_url": "https://solutions.microsoft.../solutiondetails/..."
}
```

### Chunking Strategy
- **Chunk Size:** 1000 characters
- **Overlap:** 200 characters
- **Purpose:** Optimize for semantic search and vector embeddings

---

## Error Handling

### API Request Failures
```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"⚠️  Error fetching theme {slug}: {e}")
    continue  # Skip this theme and continue with others
```

### Missing or Malformed Data
- **Missing Partner:** Extract from title or mark as "Unknown"
- **Empty Description:** Use title as content
- **Invalid Slug:** Skip solution and log warning
- **Null IDs:** Skip solution (cannot be indexed without ID)

---

## Scripts Using This Structure

### 1. Integrated Vectorization (`integrated-vectorization/`)
**File:** `01_export_to_blob.py`
- Fetches all solutions using the two-phase approach
- Exports to Azure Blob Storage as JSON
- Used for initial indexing and full re-indexing

### 2. Update Monitor (`update-monitor/`)
**File:** `fetch_current_solutions.py`
- Fetches current solutions for analysis
- Saves snapshot with metadata
- Used for manual inspection

**File:** `check_for_updates.py`
- Compares ISD vs. search index
- Detects new, modified, and removed solutions
- Recommends when to re-index

---

## API Rate Limiting

### Observations
- No explicit rate limits documented
- Typical response time: 200-500ms per request
- Total fetch time for all solutions: ~2-3 minutes
- Recommended: 1-second delay between theme requests (conservative)

### Best Practices
```python
import time

for theme in themes:
    fetch_theme_data(theme)
    time.sleep(1)  # Polite delay between requests
```

---

## Future Considerations

### Potential API Changes
- Monitor for new fields (partner info might be added)
- Watch for structure changes (new nesting levels)
- API versioning (may introduce `/v2/` endpoints)

### Enhancement Opportunities
- **Pagination:** API currently returns all data; may add pagination
- **Filtering:** Could add filters by industry, partner, or date
- **Webhooks:** ISD might add change notifications in the future
- **GraphQL:** Potential migration to GraphQL for flexible queries

---

## Related Documentation

- [Main Data Ingestion README](README.md) - Overview of ingestion pipeline
- [Integrated Vectorization README](integrated-vectorization/README.md) - Production indexing approach
- [Update Monitor README](update-monitor/README.md) - Update checking scripts
- [Partner Statistics](../docs/PARTNER_STATISTICS.md) - Current partner analysis

---

## Contact

For questions about the ISD website structure or data extraction:
- **Owner:** Arturo Quiroga
- **Role:** Principal Industry Solutions Architect, Microsoft
- **Repository:** [Industry-Solutions-Directory-PRO-Code](https://github.com/Arturo-Quiroga-MSFT/Industry-Solutions-Directory-PRO-Code)
