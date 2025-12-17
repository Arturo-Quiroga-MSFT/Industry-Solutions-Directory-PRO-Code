
Based on the investigation, here are the **ISD API endpoints** discovered:

## 📡 Industry Solutions Directory API Endpoints

### **Base URL:**
```
https://mssoldir-app-prd.azurewebsites.net/api/
```

### **Main Endpoints:**

#### 1. **Get Menu/Navigation Structure**
```bash
GET https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu
```
- Returns complete industry hierarchy with slugs
- **Response**: Industry → Sub-Industries → Solution Areas
- **Key field**: `industryThemeSlug` (used for fetching solutions)

#### 2. **Get Theme Details with Partner Solutions**
```bash
GET https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug={industryThemeSlug}
```
- Returns all partner solutions for a specific theme/use case
- **Parameter**: `slug` (the `industryThemeSlug` from menu)
- **Response**: Solutions organized by solution areas (AI Business, Cloud & AI, Security)

### **Correct Field Names (Important!):**

The actual API uses different field names than initially thought:

```json
{
  "solutionName": "Solution Title",           // NOT partnerSolutionTitle
  "orgName": "Partner Company Name",          // NOT companyName
  "solutionDescription": "Description...",
  "url": "https://...",                      // NOT partnerSolutionUrl
  "logoUrl": "https://...",
  "id": "uuid",                              // NOT partnerSolutionId
  "industries": ["Industry1", "Industry2"],
  "technologies": ["Tech1", "Tech2"]
}
```

### **Data Structure:**

- **10 main industries** (Healthcare, Education, Financial Services, etc.)
- **~36 sub-industries/use cases** (themes)
- **3 solution areas** per theme:
  - AI Business Solutions
  - Cloud and AI Platforms
  - Security

### **Current Stats (December 12, 2025):**
- 490 unique solutions with content
- 700 total API entries (with duplicates)
- Same solution can appear under multiple themes

In the meeting notes, **Santhanaraj** mentioned creating **master views** for technology and industry - these would likely aggregate this API data into easier-to-query views! 📊
