# Multi-Agent NL2SQL Chat System

## Overview

This is an intelligent, multi-agent query processing system for the Industry Solutions Directory that goes beyond simple SQL execution to provide **actionable insights** and **compelling narratives** alongside raw data.

## Architecture

### 4-Agent Pipeline

```
User Question → Query Planner → SQL Executor → Insight Analyzer → Response Formatter → User
```

#### Agent 1: Query Planner (Router)
**Purpose**: Analyzes user intent and determines processing strategy

**Capabilities**:
- Classifies intent: `query`, `analyze`, `summarize`, `compare`
- Determines if new SQL query is needed
- Routes to appropriate processing path
- Maintains conversation context for follow-up questions

**Example Intent Analysis**:
```json
{
  "intent": "query",
  "needs_new_query": true,
  "query_type": "specific",
  "reasoning": "User is asking for specific healthcare AI solutions"
}
```

#### Agent 2: SQL Executor
**Purpose**: Generates and executes T-SQL queries

**Capabilities**:
- Converts natural language to T-SQL
- Validates queries for safety (read-only)
- Executes against Azure SQL Database
- Returns structured results

**Enhanced Prompt Rules**:
- Always includes `solutionDescription` in results
- Places description column last for readability
- Handles aggregates vs. detailed queries
- Optimized for the denormalized view

#### Agent 3: Insight Analyzer
**Purpose**: Extracts patterns, trends, and actionable insights from data

**Capabilities**:
- Analyzes query results
- Identifies patterns and trends
- Calculates relevant statistics
- Provides recommendations

**Insight Structure**:
```json
{
  "overview": "Found 50 AI-powered healthcare solutions from 15 partners",
  "key_findings": [
    "40% focus on patient engagement",
    "30% on clinical decision support",
    "20% on medical imaging"
  ],
  "patterns": [
    "Most solutions integrate with existing EHR systems",
    "Strong emphasis on HIPAA compliance"
  ],
  "statistics": {
    "total_results": 50,
    "unique_partners": 15,
    "top_category": "Patient Engagement"
  },
  "recommendations": [
    "Filter by specific clinical specialty",
    "Compare solutions by partner"
  ]
}
```

#### Agent 4: Response Formatter
**Purpose**: Creates compelling, user-facing narratives

**Capabilities**:
- Formats insights in markdown
- Creates engaging narrative flow
- Highlights key takeaways
- Suggests follow-up actions

**Output**: Formatted markdown with headers, bullets, bold emphasis, and callouts

## Frontend Experience

### 4-Tab Interface

1. **Insights Tab** (Default) 📊
   - Compelling narrative with insights
   - Markdown-formatted for readability
   - Key findings highlighted
   - Recommendations for next steps

2. **Table Tab** 📋
   - Scrollable data table
   - HTML stripped from descriptions
   - Read more/Show less for long text
   - Responsive column widths

3. **Charts Tab** 📈
   - Auto-generated visualizations
   - Bar charts, pie charts
   - Smart chart type selection

4. **SQL Tab** 💻
   - Generated SQL query
   - For transparency and debugging

## Features

### Conversation Context
- Maintains last 10 exchanges
- Supports follow-up questions
- Analyzes previous results without re-querying
- "Summarize these" and "What are the trends?" work on cached data

### Smart Intent Detection
- **"Show me healthcare AI solutions"** → New SQL query
- **"What are the trends?"** → Analyze previous results
- **"Summarize these"** → Format existing data
- **"Compare these solutions"** → Extract comparison insights

### HTML Cleaning
- Strips HTML tags from description columns
- Pattern matching: any column with `desc`, `description`, or `theme`
- Preserves "(Not Set)" values
- Applied server-side for consistency

### Responsive Descriptions
- Truncated to 200 characters initially
- "Read more" button expands full text
- Individual expansion state per cell
- "Show less" collapses back

## API Response Format

```json
{
  "success": true,
  "question": "Show me healthcare AI solutions",
  "intent": {
    "intent": "query",
    "needs_new_query": true,
    "query_type": "specific"
  },
  "narrative": "## Healthcare AI Solutions\n\nFound 50 AI-powered healthcare solutions...",
  "insights": {
    "overview": "...",
    "key_findings": [...],
    "patterns": [...],
    "statistics": {...},
    "recommendations": [...]
  },
  "sql": "SELECT solutionName, orgName, industryName, solutionAreaName, solutionDescription FROM...",
  "explanation": "This query searches for...",
  "confidence": "high",
  "columns": ["solutionName", "orgName", "industryName", ...],
  "rows": [{...}, {...}],
  "row_count": 50,
  "timestamp": "2025-12-18T..."
}
```

## Example Queries

### Exploratory Query
**User**: "Show me AI healthcare solutions"

**Intent**: `query` (new SQL needed)

**Insights Generated**:
- Total solutions found
- Top partners
- Common focus areas
- Technology distribution
- Recommendations for filtering

### Analysis Query
**User**: "What are the common patterns in these solutions?"

**Intent**: `analyze` (use previous results)

**Insights Generated**:
- Technology patterns
- Partner trends
- Industry focus areas
- Deployment models

### Summary Query
**User**: "Give me key takeaways"

**Intent**: `summarize` (use previous results)

**Insights Generated**:
- Executive summary
- Top 3 findings
- Critical recommendations

## Running the System

### Backend (Multi-Agent Pipeline)
```bash
cd frontend-react/backend
python main.py
# Server runs on http://localhost:8000
```

### Frontend (React)
```bash
cd frontend-react
npm run dev
# App runs on http://localhost:5173
```

### Test a Query
1. Open http://localhost:5173
2. Click example: "Show me AI-powered healthcare solutions"
3. View **Insights** tab (default) for narrative
4. Switch to **Table** tab for data
5. Click **Read more** on descriptions
6. Ask follow-up: "What are the trends?" (uses cached data)

## Technologies

### Backend
- **FastAPI**: REST API framework
- **Azure OpenAI GPT-4**: Multi-agent LLM calls
- **pyodbc**: SQL Server connectivity
- **Pydantic**: Request/response validation

### Frontend
- **React 19**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **react-markdown**: Insights rendering
- **Tailwind CSS**: Styling
- **Recharts**: Visualizations

## Configuration

### Environment Variables (.env)
```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini

# SQL Server
SQL_SERVER=mssoldir-prd-sql.database.windows.net
SQL_DATABASE=ISD
SQL_USERNAME=isdapi
SQL_PASSWORD=...
```

## Benefits Over Previous System

| Feature | Old System | Multi-Agent System |
|---------|-----------|-------------------|
| **Output** | Raw SQL results | Insights + Data |
| **Presentation** | Table only | Narrative + 3 views |
| **Context** | None | Last 10 exchanges |
| **Follow-ups** | Re-query | Analyzes cached data |
| **Insights** | Manual interpretation | AI-generated |
| **Recommendations** | None | Suggested next steps |
| **User Experience** | Technical | Business-focused |

## Future Enhancements

1. **Comparison Agent**: Side-by-side solution comparison
2. **Trend Analysis**: Historical pattern detection
3. **Recommendation Engine**: Personalized solution suggestions
4. **Export Insights**: PDF/Word report generation
5. **User Preferences**: Remember analysis preferences
6. **Multi-turn Refinement**: Iterative query refinement
7. **Voice Input**: Natural language voice queries

## Debugging

### Backend Logs
The backend prints agent execution flow:
```
🧠 Agent 1: Query Planner analyzing intent...
   Intent: query, New Query: True
🔍 Agent 2: SQL Executor generating query...
⚙️  Agent 2: Executing SQL query...
📊 Agent 3: Insight Analyzer extracting insights...
   Confidence: high
✍️  Agent 4: Response Formatter creating narrative...
✅ Multi-agent processing complete!
```

### Frontend DevTools
Check Network tab for API response structure and insights payload.

## Performance

- **Query Planning**: ~200-500ms
- **SQL Generation**: ~1-2 seconds
- **SQL Execution**: ~100-500ms (depending on data size)
- **Insight Analysis**: ~1-3 seconds
- **Response Formatting**: ~1-2 seconds
- **Total**: ~3-7 seconds for complete multi-agent flow

## Conclusion

This multi-agent system transforms a technical NL2SQL tool into an **intelligent business assistant** that doesn't just return data—it provides **context, insights, and actionable recommendations** that drive decision-making.
