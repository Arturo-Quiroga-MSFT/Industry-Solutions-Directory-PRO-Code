# NL2SQL Pipeline - Natural Language to SQL

**Purpose**: Query the ISD SQL database using natural language questions, powered by Azure OpenAI.

**Status**: 🧪 Testing/Prototype

---

## Overview

This pipeline allows you to query the ISD database using natural language instead of writing SQL. It uses Azure OpenAI GPT-4 to:
1. Convert natural language questions to SQL
2. Validate the generated SQL for safety
3. Execute against the database
4. Format and display results

---

## Architecture

```
Natural Language Question
         ↓
[Azure OpenAI GPT-4]
    (with schema context)
         ↓
Generated SQL Query
         ↓
[SQL Validation]
    (safety checks)
         ↓
[Database Execution]
    (read-only SELECT)
         ↓
Formatted Results
```

---

## Files

- **`nl2sql_pipeline.py`** - Main pipeline (interactive mode)
- **`nl2sql_batch_test.py`** - Batch testing with predefined queries
- **`nl2sql_history.json`** - Query history (auto-generated)

---

## Quick Start

### Interactive Mode

```bash
cd data-ingestion/sql-direct
python nl2sql_pipeline.py
```

Then ask questions in natural language:
```
Enter your question: Show me the top 5 healthcare AI solutions
Enter your question: Which partners have solutions in multiple industries?
Enter your question: What are the latest manufacturing solutions?
```

### Batch Test Mode

```bash
python nl2sql_batch_test.py
```

Runs 20+ predefined test queries to validate the pipeline.

---

## Example Queries

### Basic Discovery
- "Show me the top 10 partners by number of solutions"
- "How many solutions are in each industry?"
- "What are the technology areas available?"

### Industry-Specific
- "Find all healthcare AI solutions"
- "What partners offer financial services security solutions?"
- "Show manufacturing cloud solutions"

### Technology-Focused
- "Which solutions have AI capabilities?"
- "List solutions with security features"
- "What are the cloud platform solutions for retail?"

### Partner Analysis
- "Which partners serve multiple industries?"
- "Show me RSM's solutions"
- "What solutions does Elastic offer?"

### Analytics
- "What's the distribution of solutions by technology area?"
- "Which sub-industries have the most solutions?"
- "Show recent solution updates in the last 30 days"

### Complex Queries
- "Find cross-industry partners with more than 5 solutions"
- "What percentage of solutions have marketplace links?"
- "Show education sector solutions grouped by technology"

### Use Case Driven
- "I need a compliance solution for financial services"
- "What AI solutions help with patient experience in healthcare?"
- "Show me smart factory solutions for manufacturing"

---

## How It Works

### 1. Schema Context

The pipeline provides GPT-4 with comprehensive schema information:
- Table structures (partnerSolution, organization, Industry, etc.)
- Column names and types
- Relationships (foreign keys, junction tables)
- Common query patterns
- Example industry/technology names

### 2. SQL Generation

GPT-4 generates T-SQL queries following best practices:
- Uses appropriate JOINs based on relationships
- Filters by `IsPublished = 1` for active solutions
- Includes TOP clause for large result sets
- Handles NULL values properly
- Uses clear aliases (ps, o, i, sa, etc.)

### 3. Safety Validation

Before execution, queries are validated:
- ✅ Must be SELECT statements only
- ❌ Blocks DROP, DELETE, INSERT, UPDATE, etc.
- ✅ Read-only access enforced

### 4. Execution & Display

- Executes against ISD production database
- Formats results in readable tables
- Shows row counts and query metadata
- Saves query history for analysis

---

## Configuration

### Environment Variables Required

```bash
# SQL Server (from .env)
SQL_SERVER=mssoldir-prd-sql.database.windows.net
SQL_DATABASE=mssoldir-prd
SQL_USERNAME=isdapi
SQL_PASSWORD=***

# Azure OpenAI (from .env)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=***
```

Make sure your `.env` file has both SQL and OpenAI credentials.

---

## Output Format

### Query Execution Flow

```
================================================================================
Question: Show me the top 5 healthcare AI solutions
================================================================================

🤖 Generating SQL from natural language...

✓ SQL generated successfully
Confidence: high

Generated SQL:
SELECT TOP 5
    ps.solutionName,
    o.orgName AS PartnerName,
    si.subIndustryName
FROM dbo.partnerSolution ps
INNER JOIN dbo.organization o ON ps.OrganizationId = o.orgId
INNER JOIN dbo.Industry i ON ps.IndustryId = i.industryId
LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
WHERE i.industryName = 'Healthcare & Life Sciences'
AND sa.solutionAreaName = 'AI Business Solutions'
AND ps.IsPublished = 1
ORDER BY ps.rowChangedDate DESC

Explanation:
This query retrieves the top 5 most recently updated healthcare AI solutions...

✓ SQL validated (read-only SELECT query)

📊 Executing SQL query...

✓ Query executed successfully (5 rows)

Results:

solutionName          | PartnerName           | subIndustryName       
----------------------------------------------------------------------
Clinical Document ... | WinWire               | Empower Healthcare... 
Docusign Intelligent  | Docusign              | Empower Healthcare... 
Life Science Essen... | RSM US LLP            | Enhance Patient...    

Total: 5 rows
```

---

## Query History

All queries are saved to `nl2sql_history.json`:

```json
[
  {
    "timestamp": "2025-12-17T10:30:45",
    "natural_query": "Show me healthcare AI solutions",
    "sql": "SELECT TOP 5...",
    "row_count": 5,
    "success": true
  }
]
```

This helps track:
- What questions users ask
- SQL query patterns
- Success/failure rates
- Performance metrics

---

## Limitations

### Current Limitations

1. **Schema Knowledge**
   - Limited to tables we've documented
   - Doesn't know about undocumented columns
   - May need schema updates as database evolves

2. **Query Complexity**
   - Works best for straightforward analytical queries
   - Complex multi-step queries may need refinement
   - Aggregations across M:N relationships can be tricky

3. **LLM Variability**
   - GPT-4 may generate slightly different SQL each time
   - Confidence scores are estimates
   - May hallucinate column names if context is unclear

4. **Performance**
   - Each query requires OpenAI API call (~1-3 seconds)
   - Large result sets may be slow
   - No query caching yet

### Safety Features

✅ **Enforced:**
- Read-only SELECT queries only
- No data modification allowed
- SQL injection prevention via parameterization
- Query validation before execution

---

## Adaptation for View-Based Approach

Once the ISD team creates the database view, we'll update the pipeline:

### Changes Needed

1. **Update Schema Context**
   ```python
   schema_context = """
   # ISD Database View Schema
   
   ## vw_PartnerSolutionsForAI (view)
   Consolidated view with all data for AI search.
   Columns:
   - (based on actual view definition)
   """
   ```

2. **Simplify Queries**
   - No complex JOINs needed
   - Query single view instead of multiple tables
   - Faster execution (view is pre-joined)

3. **Example Transformation**
   
   **Before (multi-table):**
   ```sql
   SELECT ps.solutionName, o.orgName
   FROM dbo.partnerSolution ps
   INNER JOIN dbo.organization o ON ps.OrganizationId = o.orgId
   WHERE ps.IsPublished = 1
   ```
   
   **After (view-based):**
   ```sql
   SELECT solutionName, partnerName
   FROM dbo.vw_PartnerSolutionsForAI
   WHERE isPublished = 1
   ```

---

## Testing Strategy

### Phase 1: Current Testing (Multi-Table)
- ✅ Test with actual database schema
- ✅ Validate JOIN logic
- ✅ Identify common query patterns
- ✅ Measure success rates

### Phase 2: View-Based Testing (After View Created)
- Update schema context
- Re-run all test queries
- Compare performance (should be faster)
- Validate results match

### Phase 3: Production Integration
- Integrate with AI search backend
- Add caching layer
- Implement rate limiting
- Monitor query patterns

---

## Performance Tips

1. **Use TOP clause** for exploratory queries
2. **Be specific** in questions (include industry, technology, etc.)
3. **Avoid "all"** - use "top 10" or similar
4. **Leverage indexes** - queries on IndustryId, OrganizationId are fast

---

## Troubleshooting

### "Error generating SQL"
- Check Azure OpenAI credentials in `.env`
- Verify endpoint and API key are correct
- Ensure quota is available

### "Query contains dangerous keyword"
- Pipeline blocks write operations (safety feature)
- Use SELECT queries only

### "SQL execution error"
- Generated SQL may have syntax error
- Check if referenced columns exist
- Verify table/column names in schema context

### "No results found"
- Query logic may be too restrictive
- Try broader query
- Check if IsPublished filter is appropriate

---

## Next Steps

1. **Test extensively** with diverse questions
2. **Document common patterns** that work well
3. **Identify gaps** in schema knowledge
4. **Prepare for view migration** once available
5. **Integrate with AI search** backend

---

## Example Session

```bash
$ python nl2sql_pipeline.py

================================================================================
NL2SQL Pipeline - ISD Database
Natural Language to SQL Query System
================================================================================

Example questions you can ask:
  1. Show me the top 5 healthcare AI solutions
  2. Which partners have the most solutions in financial services?
  3. What are the latest solutions added in the last week?
  4. How many solutions are there for each technology area?
  5. Find solutions for manufacturing with security features

================================================================================
Enter your question (or 'quit' to exit): Which partners have solutions in 5+ industries?

[Pipeline generates SQL, validates, executes, displays results]

================================================================================
Enter your question (or 'quit' to exit): quit

✓ Query history saved to nl2sql_history.json

Thank you for using NL2SQL Pipeline!
```

---

## Future Enhancements

- [ ] Query result caching
- [ ] Query optimization suggestions
- [ ] Natural language result summaries
- [ ] Voice input support
- [ ] Query templates/shortcuts
- [ ] Performance analytics dashboard
- [ ] Multi-turn conversations (follow-up questions)
- [ ] Export results to CSV/JSON

---

**Ready to test!** Run `python nl2sql_pipeline.py` to start querying with natural language.
