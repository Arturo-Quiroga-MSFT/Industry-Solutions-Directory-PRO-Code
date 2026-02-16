#!/usr/bin/env python3
"""
Natural Language to SQL Pipeline
Converts natural language queries to SQL and executes against ISD database.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import pyodbc
from openai import OpenAI

# Load environment variables
load_dotenv()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


class NL2SQLPipeline:
    """Natural Language to SQL conversion and execution pipeline."""
    
    def __init__(self):
        """Initialize the pipeline with database and LLM connections."""
        self.schema_context = self._load_schema_context()
        self.llm_client = self._init_llm_client()
        self.query_history = []
        self.app_mode = os.getenv('APP_MODE', 'seller').lower()  # 'seller' or 'customer'
    
    def _load_schema_context(self):
        """Load database schema context for the LLM."""
        return """
# ISD Database Schema Context

## Primary View: dbo.vw_ISDSolution_All (5,118 rows)

**IMPORTANT**: Use this VIEW for all queries. It contains denormalized, pre-joined data - NO JOINS NEEDED!

This view contains all solution data with related information already joined. Each row represents a solution with all its associated data.

### Key Columns:

**Solution Information:**
- SolutionType (varchar) - Type of solution (e.g., "Industry")
- solutionName (varchar) - Name of the solution
- solutionDescription (varchar) - HTML-formatted description
- solutionOrgWebsite (nvarchar) - Partner's website URL
- marketPlaceLink (varchar) - Azure Marketplace link
- specialOfferLink (varchar) - Special offer URL (if available)
- logoFileLink (varchar) - Solution logo URL

**Industry Classification:**
- industryName (varchar) - Industry category (e.g., "Healthcare & Life Sciences", "Financial Services", "State & Local Government")
- industryDescription (varchar) - HTML-formatted industry description
- subIndustryName (varchar) - Sub-industry category
- SubIndustryDescription (varchar) - Sub-industry description
- theme (varchar) - Industry theme/focus area
- industryThemeDesc (varchar) - Theme description

**Technology/Solution Area:**
- solutionAreaName (varchar) - Technology area: "AI Business Solutions", "Cloud and AI Platforms", or "Security"
- solAreaDescription (varchar) - Solution area description
- areaSolutionDescription (varchar) - Additional area description

**Solution Plays (Microsoft terminology):**
- solutionPlayName (varchar) - Solution play name (may be NULL)
- solutionPlayDesc (varchar) - Solution play description
- solutionPlayLabel (varchar) - Solution play label

**Partner Information:**
- orgName (varchar) - Partner/organization name
- orgDescription (varchar) - Partner description
- userType (varchar) - Usually "Partner"

**Status & Publishing:**
- solutionStatus (nvarchar) - Status (e.g., "Approved")
- displayLabel (nvarchar) - Display label for status

**Geographic Information:**
- geoName (varchar) - Geographic region (e.g., "United States", "Canada")

**Resources & Links:**
- resourceLinkTitle (varchar) - Resource link title
- resourceLinkUrl (varchar) - Resource URL
- resourceLinkName (varchar) - Resource name/type (e.g., "Blog")
- resourceLinkDescription (varchar) - Resource description

**Images:**
- image_thumb (varchar) - Thumbnail image URL
- image_main (varchar) - Main image URL
- image_mobile (varchar) - Mobile-optimized image URL

### Important Notes:

1. **No JOINs Required**: This view already contains all related data
2. **Denormalized & Duplicates**: Each solution may appear multiple times (10-20+ rows) if it has:
   - Multiple solution areas
   - Multiple resources
   - Multiple geographic regions
   - Multiple solution plays
   - **CRITICAL**: ALWAYS use SELECT DISTINCT when listing solutions to avoid showing duplicates
3. **NULL Values**: Some fields like solutionPlayName, industryName may be NULL (displays as "(Not Set)" in UI)
4. **Filtering**: Most queries will want to filter on:
   - solutionStatus = 'Approved' (published solutions only)
   - industryName (to focus on specific industries)
   - solutionAreaName (to focus on AI, Cloud, or Security)
   - orgName (for partner-specific queries)

## Sample Query Patterns:

### Count solutions by industry:
SELECT industryName, COUNT(DISTINCT solutionName) as solution_count
FROM dbo.vw_ISDSolution_All
WHERE solutionStatus = 'Approved'
GROUP BY industryName

### Find healthcare AI solutions (DISTINCT required to avoid duplicates):
SELECT DISTINCT TOP 50 solutionName, orgName, industryName, solutionAreaName, solutionDescription
FROM dbo.vw_ISDSolution_All
WHERE industryName = 'Healthcare & Life Sciences'
  AND solutionAreaName = 'AI Business Solutions'
  AND solutionStatus = 'Approved'

### Top partners by solution count:
SELECT orgName, COUNT(DISTINCT solutionName) as solution_count
FROM dbo.vw_ISDSolution_All
WHERE solutionStatus = 'Approved'
GROUP BY orgName
ORDER BY solution_count DESC

### Solutions with marketplace links (DISTINCT to avoid duplicates):
SELECT DISTINCT TOP 50 solutionName, orgName, marketPlaceLink, geoName
FROM dbo.vw_ISDSolution_All
WHERE marketPlaceLink IS NOT NULL
  AND solutionStatus = 'Approved'
   JOIN partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
   JOIN solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId

4. Published solutions only:
   WHERE ps.IsPublished = 1

## Important Notes
- Always use table aliases (ps, o, i, si, sa, psba)
- Filter by IsPublished = 1 for active solutions
- Use LEFT JOIN for optional relationships
- Industry names: "Financial Services", "Healthcare & Life Sciences", "Retail & Consumer Goods", 
  "Manufacturing & Mobility", "Education", "Energy & Resources", "State & Local Government"
"""
    
    def _init_llm_client(self):
        """Initialize OpenAI client per official Azure Responses API docs."""
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        return OpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=f"{azure_endpoint}/openai/v1/"
        )
    
    def _get_db_connection(self):
        """Get database connection."""
        server = os.getenv('SQL_SERVER')
        database = os.getenv('SQL_DATABASE')
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        
        conn_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={server};"
            f"Database={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"ApplicationIntent=ReadOnly;"  # PRODUCTION SAFETY: Read-only mode
        )
        
        return pyodbc.connect(conn_str)
    
    def generate_sql(self, natural_query: str) -> dict:
        """
        Convert natural language query to SQL.
        
        Args:
            natural_query: Natural language question
        
        Returns:
            dict with 'sql', 'explanation', and 'confidence'
        """
        print(f"{BLUE}🤖 Generating SQL from natural language...{RESET}\n")
        
        # Determine mode-specific requirements
        is_seller_mode = self.app_mode == 'seller'
        mode_label = "SELLER" if is_seller_mode else "CUSTOMER"
        print(f"{CYAN}📋 Mode: {mode_label}{RESET}")
        
        # Mode-specific column requirements
        if is_seller_mode:
            column_requirements = """
**SELLER MODE - REQUIRED COLUMNS:**
Microsoft sellers need comprehensive solution information. For ALL queries (including those asking for "breakdowns" or "which industries"):

**CRITICAL: For "Breakdown" or "Which Industries/Partners" Queries:**
When a user asks "which industries have X" or "breakdown by Y" or "detailed breakdown", they want to SEE the solutions, not just count them.

**WRONG APPROACH (DO NOT DO THIS):**
```sql
-- ❌ BAD: User asked for "detailed breakdown of which industries have Adastra's agentic AI offerings"
-- This returns counts only - seller can't see WHAT the solutions are!
SELECT industryName, COUNT(DISTINCT solutionName) as solution_count
FROM dbo.vw_ISDSolution_All
WHERE orgName LIKE '%Adastra%' AND ...
GROUP BY industryName
```

**RIGHT APPROACH (DO THIS INSTEAD):**
```sql
-- ✅ GOOD: Returns individual solutions so seller can see names, descriptions, and industry grouping
-- ⚠️ CRITICAL: MUST start with SELECT DISTINCT - even when breakdown column is first!
SELECT DISTINCT TOP 50
    industryName,           -- Shows which industry (for breakdown)
    solutionName,           -- REQUIRED: What is the solution?
    orgName,                -- REQUIRED: Who provides it?
    solutionAreaName,       -- REQUIRED: Solution category
    geoName,                -- Geographic availability
    marketPlaceLink,        -- Where to find it
    solutionOrgWebsite,     -- Partner website
    solutionPlayName,       -- Solution play
    solutionDescription     -- REQUIRED LAST: What does it do?
FROM dbo.vw_ISDSolution_All
WHERE orgName LIKE '%Adastra%' AND ...
ORDER BY industryName, solutionName

-- ⚠️ ABSOLUTE RULE: Whether you start with industryName, solutionName, or any column
-- YOU MUST ALWAYS USE "SELECT DISTINCT TOP 50" - NO EXCEPTIONS!
```

**For Aggregate Queries (ONLY if explicitly requested):**
Only use GROUP BY/COUNT if user specifically asks "how many total", "just give me counts", "summary statistics only":
- What specific solutions exist in each group/category
- The solution descriptions so sellers can evaluate them

**Approach for Breakdown Queries:**
If the user asks "which industries have X" or "breakdown by Y", structure your query to show BOTH:
1. The aggregate counts/groups
2. Example solutions or a supplementary list

Example pattern for "which industries have X solutions":
```sql
SELECT 
    industryName, 
    geoName, 
    COUNT(DISTINCT solutionName) as solution_count,
    -- Include actual solution names (comma-separated or as array aggregate if supported)
    STRING_AGG(DISTINCT solutionName, '; ') WITHIN GROUP (ORDER BY solutionName) as example_solutions
FROM dbo.vw_ISDSolution_All
WHERE ...
GROUP BY industryName, geoName
ORDER BY solution_count DESC
```

OR return individual rows with all details (preferred for detailed analysis):
```sql
SELECT DISTINCT TOP 50  -- DISTINCT is REQUIRED to avoid duplicate solutions
    solutionName,           -- REQUIRED: What is the solution?
    orgName,                -- REQUIRED: Who provides it?
    industryName,           -- REQUIRED: Which industry?
    solutionAreaName,       -- REQUIRED: Solution category
    marketPlaceLink,        -- RECOMMENDED: Where to find it
    solutionOrgWebsite,     -- RECOMMENDED: Partner website
    geoName,                -- RECOMMENDED: Geographic availability
    solutionPlayName,       -- RECOMMENDED: Solution play
    solutionDescription     -- REQUIRED: MUST BE LAST COLUMN - What does it do?
FROM dbo.vw_ISDSolution_All
WHERE ...
ORDER BY industryName, orgName
```

**CRITICAL - DEDUPLICATION:**
- The view is denormalized - same solution appears 10-20+ times for different resources, plays, etc.
- **ALWAYS include DISTINCT** when listing individual solutions (not for GROUP BY aggregates)
- Without DISTINCT, you'll get 328 results where 300+ are duplicates of the same 20 solutions
- This confuses users and makes tables unusable

**Column Priority for Seller Mode:**
- solutionName (REQUIRED - first)
- orgName (REQUIRED - the partner)
- industryName (REQUIRED - target market)
- solutionAreaName (REQUIRED - AI/Cloud/Security)
- solutionDescription (REQUIRED - LAST column - detailed description)
- marketPlaceLink (RECOMMENDED - Azure Marketplace link)
- solutionOrgWebsite (RECOMMENDED - partner website)
- geoName (RECOMMENDED - regional availability)
- solutionPlayName (RECOMMENDED - solution play alignment)

**CRITICAL FOR SELLERS:**
- ❌ NEVER return aggregate-only results without solution names/descriptions
- ✅ ALWAYS include solutionDescription column (as last column for readability)
- ✅ If grouping data, use STRING_AGG or return individual rows
- ✅ Sellers need to SEE the actual solutions, not just counts"""
        else:
            column_requirements = """
**CUSTOMER MODE - MINIMAL COLUMNS:**
External customers need focused, unbiased information:
- solutionName
- industryName
- solutionAreaName
- solutionDescription (brief)
- geoName
DO NOT include orgName (partner names) for customer mode."""
        
        system_prompt = f"""You are an expert SQL query generator for the ISD (Industry Solutions Directory) database.

{self.schema_context}

{column_requirements}

Generate a SQL query to answer the user's question. Follow these rules:

**SEARCH PRECISION RULES:**

1. **Core Terms** - Always search for fundamental business concepts/technologies:
   - Pattern: Extract core 1-2 word concepts (e.g., "supply chain" from "supply chain visibility")
   - Implementation: Use LIKE '%core term%' for broader matching
   - Example: "point of sale systems" → search "%point of sale%"
   - Example: "supply chain visibility" → search "%supply chain%"
   - Rationale: Descriptive modifiers often don't match database terminology exactly

2. **Exact Phrases** - Use only when specific multi-word terms are well-defined:
   - Use for: Established phrases ("smart city", "fraud detection", "risk management")
   - Implementation: LIKE '%complete phrase%' 
   - Test: Would removing one word completely change the meaning?

3. **Industry/Technology Filters** - Add explicit filters when mentioned:
   - Pattern: "X for Y" or "Y solutions"
   - Implementation: AND industryName = 'Y' or filter by solutionAreaName
   - Example: "retail solutions" → AND industryName = 'Retail & Consumer Goods'

4. **Ambiguity Detection** - Trigger clarification when:
   - Query is 1-2 generic words (e.g., "AI", "smart", "cloud") without context
   - Term has multiple distinct solution categories
   - When ambiguous: suggest 3-4 specific refinements with real-world use cases

**SQL GENERATION RULES - READ CAREFULLY:**

5. Return ONLY valid T-SQL for SQL Server
6. Use the vw_ISDSolution_All view - NO JOINS needed (data is pre-joined)
7. Always filter by solutionStatus = 'Approved' unless specifically asked for all
8. Use clear aliases and column names

9. **🚨 CRITICAL RULE #1 - ALWAYS USE DISTINCT FOR SOLUTION LISTINGS 🚨**
   - The view is denormalized - EVERY solution appears 10-20+ times for different resources, plays, regions
   - **MANDATORY: Start ALL solution listing queries with SELECT DISTINCT TOP 50**
   - Syntax: `SELECT DISTINCT TOP 50 solutionName, orgName, industryName...`
   - ❌ WRONG: `SELECT industryName, solutionName...` → Returns 80-328 duplicate rows
   - ✅ RIGHT: `SELECT DISTINCT TOP 50 industryName, solutionName...` → Returns ~10-20 unique solutions
   - **EXCEPTION**: Only skip DISTINCT when using GROUP BY with aggregates (COUNT, SUM, etc.)

10. For limiting results, use TOP 50 as default (AFTER DISTINCT if listing solutions)
11. Handle NULL values appropriately (they display as "(Not Set)" in UI - this is expected)
12. When counting solutions with GROUP BY, use COUNT(DISTINCT solutionName) to avoid counting duplicates
13. **COMPOUND QUESTIONS**: If the question asks multiple things ("what X and how many Y"), 
    - Generate ONE primary query that best answers the main question
    - Explain in the explanation field what the query shows
    - DO NOT return multiple queries or a dictionary of queries
    - The "sql" field must ALWAYS be a single SQL string, never a dict or array

**CRITICAL SELLER MODE REMINDER:**
- If in seller mode and query asks for breakdowns/groupings (e.g., "which industries", "breakdown by", "detailed breakdown"), 
  **ALWAYS return individual solution rows with full details** - NEVER use GROUP BY with just counts
- Sellers need to see WHAT the solutions are (names + descriptions), not just HOW MANY there are
- "Breakdown by industry" = show individual solutions with their industry column, NOT aggregate counts
- "Which industries have X" = show individual solutions from those industries with industry column visible
- Only use pure aggregates (COUNT without details) if the user **explicitly** asks for "just counts", "summary only", or "how many total"
- When in doubt: **individual rows with DISTINCT > aggregates**

**ABSOLUTE RULE FOR ALL SELLER QUERIES LISTING SOLUTIONS:**
- EVERY query that lists individual solutions MUST start with: SELECT DISTINCT TOP 50
- Even if putting industryName or orgName first for grouping: SELECT DISTINCT TOP 50 industryName, solutionName, ...
- NO EXCEPTIONS - the view is denormalized and will return 10-80 duplicates without DISTINCT
- If you write SELECT industryName, ... without DISTINCT, you WILL return duplicate solutions and fail the requirement

**BEFORE GENERATING SQL - CHECKLIST:**
✓ Am I listing individual solutions? → START WITH `SELECT DISTINCT TOP 50`
✓ Does my query show solution names, descriptions, partners? → MUST USE DISTINCT
✓ Am I using GROUP BY? → Then skip DISTINCT, but use COUNT(DISTINCT solutionName)
✓ Is this a breakdown/which industries question? → DISTINCT + individual rows, NOT GROUP BY

Return your response in JSON format:
{{
    "sql": "SELECT DISTINCT TOP 50 ... (⚠️ MUST include DISTINCT for all solution listings)",
    "explanation": "This query does X...",
    "confidence": "high|medium|low",
    "needs_clarification": false,
    "clarification_question": "Optional: Only if ambiguous",
    "suggested_refinements": ["Optional: Only if ambiguous"]
}}

CRITICAL REMINDER BEFORE YOU GENERATE:
- If your SQL lists solutions (not just counts), CHECK IT STARTS WITH: SELECT DISTINCT TOP 50
- If you wrote: SELECT industryName, solutionName... → WRONG! Must be: SELECT DISTINCT TOP 50 industryName, solutionName...
- The view is denormalized - without DISTINCT you'll return 80 duplicate rows instead of 10 unique solutions

**Response Confidence Levels:**
- high: Clear intent, specific domain terms, unambiguous
- medium: Broad but actionable, may return many results
- low: Very vague or likely to return no results
"""
        
        try:
            # Use the deployment name from environment or default
            deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
            
            response = self.llm_client.responses.create(
                model=deployment_name,
                instructions=system_prompt,
                input=natural_query,
                text={"format": {
                    "type": "json_schema",
                    "name": "sql_generation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "anyOf": [{"type": "string"}, {"type": "null"}]
                            },
                            "explanation": {"type": "string"},
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low", "none"]
                            },
                            "needs_clarification": {"type": "boolean"},
                            "clarification_question": {
                                "anyOf": [{"type": "string"}, {"type": "null"}]
                            },
                            "suggested_refinements": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["sql", "explanation", "confidence", "needs_clarification", "clarification_question", "suggested_refinements"],
                        "additionalProperties": False
                    }
                }}
            )
            
            result = json.loads(response.output_text)
            
            print(f"{GREEN}✓ SQL generated successfully{RESET}")
            print(f"{CYAN}Confidence: {result.get('confidence', 'unknown')}{RESET}\n")
            
            return result
            
        except Exception as e:
            print(f"{RED}✗ Error generating SQL: {str(e)}{RESET}\n")
            return {
                "sql": None,
                "explanation": f"Error: {str(e)}",
                "confidence": "none"
            }
    
    def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL query for safety - PRODUCTION DATABASE PROTECTION.
        
        Multiple validation layers:
        1. Block all write operations (INSERT, UPDATE, DELETE, etc.)
        2. Block DDL operations (CREATE, DROP, ALTER, etc.)
        3. Block stored procedures and functions (EXEC, EXECUTE)
        4. Block transactions (BEGIN, COMMIT)
        5. Only allow SELECT queries
        
        Args:
            sql: SQL query to validate
        
        Returns:
            True if safe, False otherwise
        """
        import re
        
        sql_upper = sql.upper()
        
        # LAYER 1: Block write operations
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'MERGE']
        for keyword in write_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                print(f"{RED}✗ BLOCKED: Query contains WRITE operation: {keyword}{RESET}")
                print(f"{RED}✗ This is a PRODUCTION database - READ-ONLY access only!{RESET}\n")
                return False
        
        # LAYER 2: Block DDL operations
        ddl_keywords = ['DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'RENAME']
        for keyword in ddl_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                print(f"{RED}✗ BLOCKED: Query contains DDL operation: {keyword}{RESET}")
                print(f"{RED}✗ This is a PRODUCTION database - READ-ONLY access only!{RESET}\n")
                return False
        
        # LAYER 3: Block stored procedures and functions
        exec_keywords = ['EXEC', 'EXECUTE', 'SP_', 'XP_']
        for keyword in exec_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                print(f"{RED}✗ BLOCKED: Query attempts to execute code: {keyword}{RESET}")
                print(f"{RED}✗ This is a PRODUCTION database - READ-ONLY access only!{RESET}\n")
                return False
        
        # LAYER 4: Block transaction control
        transaction_keywords = ['BEGIN TRAN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT']
        for keyword in transaction_keywords:
            if keyword in sql_upper:
                print(f"{RED}✗ BLOCKED: Query contains transaction control: {keyword}{RESET}")
                print(f"{RED}✗ This is a PRODUCTION database - READ-ONLY access only!{RESET}\n")
                return False
        
        # LAYER 5: Ensure it's a SELECT query
        if not sql_upper.strip().startswith('SELECT') and not sql_upper.strip().startswith('WITH'):
            print(f"{RED}✗ BLOCKED: Only SELECT queries are allowed{RESET}")
            print(f"{RED}✗ This is a PRODUCTION database - READ-ONLY access only!{RESET}\n")
            return False
        
        print(f"{GREEN}✓ SQL validated - Safe READ-ONLY query{RESET}\n")
        return True
    
    def execute_sql(self, sql: str) -> dict:
        """
        Execute SQL query against the database (READ-ONLY).
        
        SAFETY MEASURES:
        - Connection in READ-ONLY mode (ApplicationIntent=ReadOnly)
        - Explicit ROLLBACK after each query
        - No transactions committed
        
        Args:
            sql: SQL query to execute
        
        Returns:
            dict with 'columns', 'rows', 'row_count', 'error'
        """
        print(f"{BLUE}📊 Executing SQL query (READ-ONLY mode)...{RESET}\n")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Execute query
            cursor.execute(sql)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            # SAFETY: Explicitly rollback any transaction (even though we only SELECT)
            conn.rollback()
            
            cursor.close()
            conn.close()
            
            print(f"{GREEN}✓ Query executed successfully ({len(rows)} rows) [READ-ONLY]{RESET}\n")
            
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "error": None
            }
            
        except Exception as e:
            # SAFETY: Rollback on error
            try:
                conn.rollback()
            except:
                pass
            
            cursor.close()
            conn.close()
            
            print(f"{RED}✗ Query execution error: {str(e)}{RESET}\n")
            
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "error": str(e)
            }
    
    def format_results(self, result: dict, max_width: int = 30):
        """
        Format and display query results.
        
        Args:
            result: Query result dictionary
            max_width: Maximum column width
        """
        if result['error']:
            print(f"{RED}Error: {result['error']}{RESET}\n")
            return
        
        if result['row_count'] == 0:
            print(f"{YELLOW}No results found.{RESET}\n")
            return
        
        # Print header
        header = " | ".join(f"{col[:max_width]:<{max_width}}" for col in result['columns'])
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in result['rows']:
            row_str = " | ".join(f"{str(val)[:max_width]:<{max_width}}" for val in row)
            print(row_str)
        
        print(f"\n{GREEN}Total: {result['row_count']} rows{RESET}\n")
    
    def run_query(self, natural_query: str, auto_execute: bool = True):
        """
        Complete pipeline: NL -> SQL -> Execute -> Display.
        
        Args:
            natural_query: Natural language question
            auto_execute: Whether to automatically execute the query
        """
        print(f"\n{BLUE}{'='*80}{RESET}")
        print(f"{CYAN}Question: {natural_query}{RESET}")
        print(f"{BLUE}{'='*80}{RESET}\n")
        
        # Step 1: Generate SQL
        sql_result = self.generate_sql(natural_query)
        
        if not sql_result['sql']:
            return
        
        # Display generated SQL
        print(f"{BLUE}Generated SQL:{RESET}")
        print(f"{CYAN}{sql_result['sql']}{RESET}\n")
        
        print(f"{BLUE}Explanation:{RESET}")
        print(f"{sql_result['explanation']}\n")
        
        # Step 2: Validate SQL
        if not self.validate_sql(sql_result['sql']):
            return
        
        print(f"{GREEN}✓ SQL validated (read-only SELECT query){RESET}\n")
        
        # Step 3: Execute (if auto or confirmed)
        if not auto_execute:
            response = input(f"{YELLOW}Execute this query? (y/n): {RESET}")
            if response.lower() != 'y':
                print(f"{YELLOW}Query cancelled.{RESET}\n")
                return
        
        result = self.execute_sql(sql_result['sql'])
        
        # Step 4: Format and display results
        print(f"{BLUE}Results:{RESET}\n")
        self.format_results(result)
        
        # Save to history
        self.query_history.append({
            "timestamp": datetime.now().isoformat(),
            "natural_query": natural_query,
            "sql": sql_result['sql'],
            "row_count": result['row_count'],
            "success": result['error'] is None
        })
    
    def save_history(self, filename: str = "nl2sql_history.json"):
        """Save query history to file."""
        with open(filename, 'w') as f:
            json.dump(self.query_history, f, indent=2)
        print(f"{GREEN}✓ Query history saved to {filename}{RESET}\n")


def main():
    """Main execution - interactive mode."""
    print(f"\n{RED}{'='*80}{RESET}")
    print(f"{RED}⚠️  PRODUCTION DATABASE - READ-ONLY MODE ⚠️{RESET}")
    print(f"{RED}{'='*80}{RESET}\n")
    print(f"{YELLOW}Safety measures enabled:{RESET}")
    print(f"{YELLOW}  ✓ Connection in READ-ONLY mode{RESET}")
    print(f"{YELLOW}  ✓ Explicit ROLLBACK after each query{RESET}")
    print(f"{YELLOW}  ✓ Multi-layer SQL validation (blocks all writes){RESET}")
    print(f"{YELLOW}  ✓ Only SELECT queries allowed{RESET}\n")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}NL2SQL Pipeline - ISD Database{RESET}")
    print(f"{BLUE}Natural Language to SQL Query System{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    pipeline = NL2SQLPipeline()
    
    # Example queries
    example_queries = [
        "Show me the top 5 healthcare AI solutions",
        "Which partners have the most solutions in financial services?",
        "What are the latest solutions added in the last week?",
        "How many solutions are there for each technology area?",
        "Find solutions for manufacturing with security features"
    ]
    
    print(f"{CYAN}Example questions you can ask:{RESET}")
    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")
    print()
    
    # Interactive loop
    while True:
        print(f"{YELLOW}{'='*80}{RESET}")
        user_query = input(f"{CYAN}Enter your question (or 'quit' to exit): {RESET}")
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_query.strip():
            continue
        
        pipeline.run_query(user_query, auto_execute=True)
    
    # Save history
    if pipeline.query_history:
        pipeline.save_history()
    
    print(f"\n{GREEN}Thank you for using NL2SQL Pipeline!{RESET}\n")


if __name__ == "__main__":
    main()
