# Dual Browsing Support: Industry & Technology

**Document Owner:** Arturo Quiroga, Principal Industry Solutions Architect, Microsoft  
**Last Updated:** December 12, 2025  
**Purpose:** Comprehensive guide on how the AI Chat Assistant supports both industry-based and technology-based browsing patterns

---

## Executive Summary

Following feedback from the ISD team meeting, the AI Chat Assistant has been enhanced to fully support **both browsing patterns** that users see on the Microsoft Industry Solutions Directory portal:

1. **Browse by Industry** (e.g., Healthcare, Education, Financial Services, Manufacturing)
2. **Browse by Technology** (e.g., AI Business Solutions, Cloud and AI Platforms, Security)

The system now seamlessly handles queries from both perspectives, allowing users to discover partner solutions whether they're thinking about their industry needs or specific technology capabilities.

---

## User Browsing Patterns

### Pattern 1: Industry-Based Browsing

**What Users See:**
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

**Example User Queries:**
- "What solutions are available for healthcare organizations?"
- "Show me education solutions"
- "I need manufacturing solutions"
- "What partners work in financial services?"

**How the System Responds:**
The AI assistant searches the `industries` field and returns solutions specifically tagged for that industry, ensuring results are relevant to the user's sector.

---

### Pattern 2: Technology-Based Browsing

**What Users See:**
- AI Business Solutions
- Cloud and AI Platforms
- Security

**Example User Queries:**
- "What AI Business Solutions are available?"
- "Show me Cloud and AI Platforms"
- "I'm looking for Security solutions"
- "What AI capabilities do you have?"

**How the System Responds:**
The AI assistant searches the `technologies` field and returns solutions categorized under those technology areas, regardless of industry.

---

### Pattern 3: Combined Browsing (Most Powerful)

Users often want to combine both dimensions:

**Example Combined Queries:**
- "What AI solutions are available for healthcare?"
- "Show me Security solutions for financial services"
- "I need Cloud and AI Platforms for education"
- "What AI Business Solutions work in manufacturing?"

**How the System Responds:**
The AI assistant applies filters on BOTH dimensions simultaneously, returning highly targeted results that match both the industry AND technology criteria.

---

## Technical Implementation

### Data Model

Each solution in the Azure AI Search index contains:

```json
{
  "id": "solution-uuid",
  "solution_name": "Solution Name by Partner",
  "partner_name": "Partner Company",
  "description": "Detailed solution description...",
  "industries": "Healthcare, Patient Care",  // Industry categorization
  "technologies": "AI Business Solutions",    // Technology categorization
  "solution_url": "https://solutions.microsoftindustryinsights.com/...",
  "content_vector": [...]  // Vector embedding for semantic search
}
```

**Key Fields:**
- **`industries`**: Captures industry verticals and sub-categories (e.g., "Healthcare", "Patient Care", "Education", "Student Success")
- **`technologies`**: Captures solution areas and technology categories (e.g., "AI Business Solutions", "Cloud and AI Platforms", "Security")

Both fields are:
- **Searchable**: Allow semantic and keyword search
- **Filterable**: Enable precise filtering by category

---

### Search Service Implementation

The `SearchService` class in [backend/app/services/search_service.py](../backend/app/services/search_service.py) implements dual dimension filtering:

```python
def _build_filter_expression(self, filters: Optional[SearchFilter]) -> Optional[str]:
    """
    Build OData filter expression from search filters
    Supports both industry-based and technology-based filtering
    """
    filter_parts = []
    
    # Industry-based filtering
    if filters.industries:
        industry_filters = " or ".join([
            f"search.ismatch('{industry}', 'industries')"
            for industry in filters.industries
        ])
        filter_parts.append(f"({industry_filters})")
    
    # Technology-based filtering
    if filters.technologies:
        tech_filters = " or ".join([
            f"search.ismatch('{tech}', 'technologies')"
            for tech in filters.technologies
        ])
        filter_parts.append(f"({tech_filters})")
    
    # Combine with AND for intersectional queries
    return " and ".join(filter_parts) if filter_parts else None
```

---

### AI Assistant Intelligence

The OpenAI service system prompt ([backend/app/services/openai_service.py](../backend/app/services/openai_service.py)) has been enhanced to understand both browsing patterns:

**Key Capabilities:**
1. **Pattern Recognition**: Automatically detects whether user is browsing by industry, technology, or both
2. **Contextual Responses**: Mentions both industry focus AND technology capabilities when relevant
3. **Smart Filtering**: Applies appropriate filters based on user intent
4. **Clear Communication**: Explicitly states whether solutions are industry-specific or technology-specific

**Example System Prompt Excerpt:**
```
UNDERSTANDING USER BROWSING PATTERNS:
Users can browse the directory in TWO ways:
1. **By Industry** (e.g., Healthcare, Education, Financial Services)
2. **By Technology** (e.g., AI Business Solutions, Cloud and AI Platforms)

You MUST be able to handle both types of queries:
- Industry-focused: "What solutions are available for healthcare?"
- Technology-focused: "Show me AI Business Solutions"
- Combined: "What AI solutions are available for financial services?"
```

---

## Example Interactions

### Example 1: Industry-Based Query

**User:** "What solutions are available for healthcare organizations?"

**System Process:**
1. Detects industry-based query ("healthcare")
2. Searches with filter: `search.ismatch('Healthcare', 'industries')`
3. Returns solutions tagged with Healthcare industry

**AI Response:**
```
I found several partner solutions for healthcare organizations:

1. **Patient Care Platform by Acme Health** 
   - Comprehensive patient management system
   - Industries: Healthcare, Patient Care
   - Technologies: Cloud and AI Platforms

2. **Clinical AI Assistant by MedTech Solutions**
   - AI-powered clinical decision support
   - Industries: Healthcare, Life Sciences
   - Technologies: AI Business Solutions

3. **Healthcare Security Suite by SecureHealth**
   - HIPAA-compliant security platform
   - Industries: Healthcare
   - Technologies: Security

Would you like to explore any specific technology area within healthcare?
```

---

### Example 2: Technology-Based Query

**User:** "Show me AI Business Solutions"

**System Process:**
1. Detects technology-based query ("AI Business Solutions")
2. Searches with filter: `search.ismatch('AI Business Solutions', 'technologies')`
3. Returns solutions tagged with AI Business Solutions technology

**AI Response:**
```
Here are the AI Business Solutions in our directory:

1. **Intelligent Process Automation by AutomateAI**
   - Industries: Manufacturing, Financial Services
   - AI-powered workflow automation and optimization

2. **Customer Insights Platform by DataDriven**
   - Industries: Retail, Healthcare
   - AI-based customer behavior analytics

3. **Predictive Maintenance Suite by IndustryAI**
   - Industries: Manufacturing, Energy & Resources
   - Machine learning for equipment monitoring

These solutions span multiple industries. Would you like to narrow down by a specific industry?
```

---

### Example 3: Combined Query

**User:** "What AI solutions are available for financial services?"

**System Process:**
1. Detects combined query (technology: "AI", industry: "financial services")
2. Searches with dual filters:
   - `search.ismatch('AI Business Solutions', 'technologies')`
   - `search.ismatch('Financial Services', 'industries')`
3. Returns highly targeted results

**AI Response:**
```
I found AI Business Solutions specifically for financial services:

1. **Fraud Detection AI by FinSecure**
   - Real-time transaction monitoring using machine learning
   - Industries: Financial Services, Banking
   - Technologies: AI Business Solutions

2. **Credit Risk Analytics by RiskAI**
   - AI-powered credit scoring and risk assessment
   - Industries: Financial Services
   - Technologies: AI Business Solutions

3. **Personalized Banking Assistant by CustomerFirst AI**
   - Conversational AI for customer service
   - Industries: Financial Services, Retail Banking
   - Technologies: AI Business Solutions, Cloud and AI Platforms

All of these solutions are specifically designed for financial services organizations.
```

---

## Benefits of Dual Browsing Support

### For Users
✅ **Flexibility**: Search the way that makes sense for their needs  
✅ **Comprehensive Coverage**: Won't miss relevant solutions by only browsing one dimension  
✅ **Faster Discovery**: Quickly narrow down to highly relevant solutions  
✅ **Better Understanding**: See how solutions map across both industries and technologies

### For Partners
✅ **Better Visibility**: Solutions appear in multiple browsing contexts  
✅ **Targeted Exposure**: Reach users through both industry and technology searches  
✅ **Clear Positioning**: Industry focus AND technology capabilities are highlighted

### For Microsoft
✅ **Enhanced User Experience**: Aligns with the portal's dual navigation structure  
✅ **Higher Engagement**: Users can explore from multiple perspectives  
✅ **Complete Solution**: Addresses both "what industry" and "what technology" questions  
✅ **Competitive Advantage**: More sophisticated than single-dimension search

---

## Query Examples by Pattern

### Industry-Based Queries
- "What solutions are available for healthcare?"
- "Show me education technology"
- "I need manufacturing solutions"
- "What partners work in retail?"
- "Solutions for financial services"
- "Defense industry solutions"
- "Energy sector partners"

### Technology-Based Queries
- "What AI Business Solutions do you have?"
- "Show me Cloud and AI Platforms"
- "I'm looking for Security solutions"
- "What AI capabilities are available?"
- "Cloud infrastructure solutions"
- "Cybersecurity offerings"

### Combined Queries
- "AI for healthcare"
- "Security solutions for financial services"
- "Cloud platforms for education"
- "AI Business Solutions in manufacturing"
- "Healthcare security solutions"
- "Retail AI capabilities"
- "Energy sector cloud solutions"

---

## Data Ingestion Process

### How Technology Categories Are Captured

The data ingestion pipeline ([data-ingestion/integrated-vectorization/01_export_to_blob.py](../data-ingestion/integrated-vectorization/01_export_to_blob.py)) extracts technology categories from the ISD API:

```python
for area in theme_solution_areas:
    area_name = area.get('solutionAreaName', 'Unknown Area')  # This is the technology category
    partner_solutions = area.get('partnerSolutions', [])
    
    for ps in partner_solutions:
        doc = {
            "id": ps.get("partnerSolutionId"),
            "solution_name": ps.get("solutionName"),
            "industries": [industry_name, theme_title],      # Industry categorization
            "technologies": [area_name] if area_name else [], # Technology categorization
            # ... other fields
        }
```

**Technology Categories Come From:**
- **Solution Areas** in the ISD API (e.g., "AI Business Solutions", "Cloud and AI Platforms", "Security")
- These are the same categories users see when browsing by technology

---

## Testing the Dual Browsing Support

### Manual Testing Scenarios

**Test 1: Industry Query**
```
Query: "What solutions are available for healthcare?"
Expected: Solutions tagged with "Healthcare" industry
Verify: Results include healthcare-specific solutions
```

**Test 2: Technology Query**
```
Query: "Show me AI Business Solutions"
Expected: Solutions tagged with "AI Business Solutions" technology
Verify: Results include AI-focused solutions across industries
```

**Test 3: Combined Query**
```
Query: "What AI solutions are available for financial services?"
Expected: Solutions with BOTH "Financial Services" AND "AI Business Solutions"
Verify: Results are narrowed to intersection of both categories
```

**Test 4: Clarification Handling**
```
Query: "What solutions do you have?"
Expected: AI asks for clarification (industry or technology focus)
Verify: AI prompts user to specify browsing preference
```

---

## Architecture Updates

The following files have been updated to support dual browsing:

### 1. Architecture Documentation
**File:** [ARCHITECTURE.md](../ARCHITECTURE.md)
- Updated business requirements section
- Documented dual dimension filtering strategy
- Added technology-based browsing support details

### 2. Search Service
**File:** [backend/app/services/search_service.py](../backend/app/services/search_service.py)
- Enhanced `_build_filter_expression()` with comments explaining dual support
- Both industry and technology filters properly implemented

### 3. OpenAI Service
**File:** [backend/app/services/openai_service.py](../backend/app/services/openai_service.py)
- Enhanced system prompt to recognize both browsing patterns
- Added instructions for handling industry-based, technology-based, and combined queries
- Improved response format to mention both dimensions when relevant

### 4. Data Ingestion
**File:** [data-ingestion/integrated-vectorization/01_export_to_blob.py](../data-ingestion/integrated-vectorization/01_export_to_blob.py)
- Already captures technology categories via `solutionAreaName`
- Maps to `technologies` field in search index
- No changes needed (already working correctly)

---

## Future Enhancements

### 1. Enhanced Faceted Search
Add UI elements to allow users to filter by:
- Multiple industries simultaneously
- Multiple technology categories
- Partner size/type
- Geographic region

### 2. Intelligent Query Routing
Use GPT to automatically detect and suggest:
- "I see you're asking about healthcare. Would you like to see all solutions or focus on a specific technology area?"
- "You mentioned AI. Which industry are you most interested in?"

### 3. Cross-Dimensional Recommendations
- "Users who looked at AI solutions for healthcare also viewed..."
- "Similar solutions in other industries..."
- "Alternative technology approaches for this industry..."

### 4. Analytics Dashboard
Track user behavior patterns:
- What % of queries are industry-based vs. technology-based
- Most common combined queries
- Conversion rates by browsing pattern

---

## API Examples

### Example 1: Search by Industry

**Request:**
```bash
POST /api/chat/stream
Content-Type: application/json

{
  "message": "What solutions are available for healthcare?",
  "filters": {
    "industries": ["Healthcare"]
  },
  "session_id": "user-session-123"
}
```

**Response:** (streaming)
```
data: {"type": "session", "session_id": "user-session-123"}
data: {"type": "citations", "citations": [...]}
data: {"type": "content", "content": "I found several..."}
data: {"type": "follow_up", "questions": ["What specific healthcare area?", ...]}
data: {"type": "done"}
```

---

### Example 2: Search by Technology

**Request:**
```bash
POST /api/chat/stream
Content-Type: application/json

{
  "message": "Show me AI Business Solutions",
  "filters": {
    "technologies": ["AI Business Solutions"]
  },
  "session_id": "user-session-123"
}
```

---

### Example 3: Combined Search

**Request:**
```bash
POST /api/chat/stream
Content-Type: application/json

{
  "message": "What AI solutions are available for financial services?",
  "filters": {
    "industries": ["Financial Services"],
    "technologies": ["AI Business Solutions"]
  },
  "session_id": "user-session-123"
}
```

---

## Key Takeaways

### ✅ What's Supported
- Industry-based queries (e.g., "healthcare solutions")
- Technology-based queries (e.g., "AI Business Solutions")
- Combined queries (e.g., "AI for healthcare")
- Automatic pattern detection by the AI
- Smart filtering on both dimensions
- Clear communication of both aspects in responses

### ⚠️ Important Notes
- The AI assistant automatically detects user intent (industry vs. technology)
- Filters can be applied explicitly via API or inferred from natural language
- System is designed to work seamlessly with the portal's dual navigation structure
- No changes needed to existing data ingestion (already captures both dimensions)

### 🎯 Success Metrics
- Users can discover solutions regardless of browsing approach
- Results are relevant to BOTH stated dimensions when combined
- AI responses clearly indicate industry focus AND technology capabilities
- Follow-up questions guide users to explore the other dimension

---

## Support & Questions

For questions about dual browsing support implementation:
- **Technical Owner:** Arturo Quiroga
- **Role:** Principal Industry Solutions Architect, Microsoft
- **Related Documentation:**
  - [ARCHITECTURE.md](../ARCHITECTURE.md) - Overall system architecture
  - [ISD_WEBSITE_STRUCTURE.md](../data-ingestion/ISD_WEBSITE_STRUCTURE.md) - Data structure details
  - [Backend API Documentation](../backend/README.md) - API reference

---

**Document Version:** 1.0  
**Status:** Complete ✅  
**Reviewed By:** ISD Team Meeting, December 2025
