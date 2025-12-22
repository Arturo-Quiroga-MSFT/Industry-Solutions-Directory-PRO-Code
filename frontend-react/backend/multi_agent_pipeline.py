#!/usr/bin/env python3
"""
Multi-Agent Pipeline for ISD Query Processing
Four-agent architecture: Query Planner → SQL Executor → Insight Analyzer → Response Formatter
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
import sys

# Add path for nl2sql_pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data-ingestion/sql-direct'))
from nl2sql_pipeline import NL2SQLPipeline

load_dotenv()


class QueryPlanner:
    """Agent 1: Analyzes user intent and routes to appropriate processing path"""
    
    def __init__(self, llm_client: AzureOpenAI):
        self.llm_client = llm_client
        self.deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
    
    def analyze_intent(self, question: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze user intent and determine processing strategy.
        
        Returns:
            {
                "intent": "query" | "analyze" | "summarize" | "compare",
                "needs_new_query": True/False,
                "query_type": "specific" | "aggregate" | "exploratory",
                "reasoning": "explanation of intent"
            }
        """
        # Build context from conversation history
        history_context = ""
        if conversation_history:
            recent = conversation_history[-3:]  # Last 3 exchanges
            history_context = "Recent conversation:\n" + "\n".join([
                f"User: {msg['question']}\nAssistant: {msg.get('summary', 'Returned data')}"
                for msg in recent
            ])
        
        system_prompt = """You are a query intent analyzer for an Industry Solutions Directory chatbot.

**Task**: Determine if user wants NEW data or to analyze EXISTING results from conversation.

**Intent Classification:**

1. **query** - User requesting new/different data
   - Indicators: Asking about solutions, partners, industries, counts
   - Keywords: "show", "find", "what", "which", "how many"
   
2. **analyze** - User wants insights from current results  
   - Indicators: Asking about patterns, trends in shown data
   - Keywords: "analyze these", "what patterns", "summarize this"
   - Requires: Non-empty previous results

3. **summarize** - User wants summary of previous results
   - Indicators: Explicit summarization request
   - Keywords: "summary", "key takeaways", "overview"
   - Requires: Non-empty previous results

4. **compare** - User wants comparison
   - Indicators: Explicit comparison request
   - Keywords: "compare", "difference between", "versus"

**Decision Logic:**

- needs_new_query = true IF:
  - Intent is "query" OR
  - No conversation history OR
  - Previous results were empty (0 rows)

- needs_new_query = false IF:
  - Intent is "analyze" or "summarize" AND
  - Previous results exist AND have data

**Output Format:**
{{
    "intent": "query|analyze|summarize|compare",
    "needs_new_query": true/false,
    "query_type": "specific|aggregate|exploratory",
    "reasoning": "1-sentence explanation"
}}
"""
        
        user_prompt = f"""Question: "{question}"

{history_context}

Analyze the intent and routing strategy."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            # Fallback: default to query intent
            return {
                "intent": "query",
                "needs_new_query": True,
                "query_type": "specific",
                "reasoning": f"Error in intent analysis: {str(e)}"
            }


class InsightAnalyzer:
    """Agent 3: Analyzes query results to extract patterns, trends, and insights"""
    
    def __init__(self, llm_client: AzureOpenAI):
        self.llm_client = llm_client
        self.deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
    
    def _compute_statistics(self, rows: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """Pre-compute statistics from the dataset to provide richer context to LLM"""
        stats = {
            "total_solutions": len(rows)
        }
        
        def safe_get(row, key, default='Unknown'):
            """Safely get value from pyodbc.Row or dict"""
            try:
                # Try direct key access (for dict or pyodbc.Row)
                value = row[key]
                if value is None or value == "(Not Set)":
                    return default
                return str(value)
            except (KeyError, TypeError):
                # Try index-based access
                try:
                    idx = columns.index(key)
                    value = row[idx]
                    if value is None or value == "(Not Set)":
                        return default
                    return str(value)
                except (ValueError, IndexError, TypeError):
                    # Column doesn't exist or other error
                    return default
        
        # Count by partner (orgName)
        if 'orgName' in columns:
            partner_counts = {}
            for row in rows:
                partner = safe_get(row, 'orgName')
                if partner != 'Unknown':  # Only count actual partners
                    partner_counts[partner] = partner_counts.get(partner, 0) + 1
            
            if partner_counts:  # Only add if we have real data
                # Top 5 partners
                top_partners = dict(sorted(partner_counts.items(), key=lambda x: x[1], reverse=True)[:5])
                stats['top_partners'] = top_partners
                stats['unique_partners'] = len(partner_counts)
        
        # Count by solution area
        if 'solutionAreaName' in columns:
            area_counts = {}
            for row in rows:
                area = safe_get(row, 'solutionAreaName')
                if area != 'Unknown':
                    area_counts[area] = area_counts.get(area, 0) + 1
            
            if area_counts:
                stats['solution_areas'] = area_counts
        
        # Count by industry
        if 'industryName' in columns:
            industry_counts = {}
            for row in rows:
                industry = safe_get(row, 'industryName')
                if industry != 'Unknown':
                    industry_counts[industry] = industry_counts.get(industry, 0) + 1
            
            if industry_counts:
                stats['industries'] = dict(sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Count by sub-industry
        if 'subIndustryName' in columns:
            subind_counts = {}
            for row in rows:
                subind = safe_get(row, 'subIndustryName', None)
                if subind and subind != 'Unknown' and subind != '(Not Set)':
                    subind_counts[subind] = subind_counts.get(subind, 0) + 1
            
            if subind_counts:
                stats['top_sub_industries'] = dict(sorted(subind_counts.items(), key=lambda x: x[1], reverse=True)[:3])
        
        print(f"   Computed stats: {len(stats.get('top_partners', {}))} unique partners, {len(stats.get('solution_areas', {}))} solution areas")
        return stats

    def _row_to_dict(self, row: Any, columns: List[str]) -> Dict[str, Any]:
        """Convert pyodbc.Row or dict-like row into a standard dict using provided columns"""
        row_dict: Dict[str, Any] = {}

        if isinstance(row, dict):
            for col in columns:
                if col in row:
                    row_dict[col] = row[col]
            return row_dict

        for col in columns:
            try:
                row_dict[col] = row[col]
            except (KeyError, IndexError, TypeError):
                try:
                    row_dict[col] = getattr(row, col)
                except AttributeError:
                    continue

        return row_dict
    
    def analyze_results(self, question: str, results: Dict[str, Any], intent_info: Dict) -> Dict[str, Any]:
        """
        Analyze query results and extract insights.
        
        Returns:
            {
                "insights": {
                    "overview": "high-level summary",
                    "key_findings": ["finding 1", "finding 2", ...],
                    "patterns": ["pattern 1", "pattern 2", ...],
                    "statistics": {"stat_name": value, ...},
                    "recommendations": ["suggestion 1", ...]
                },
                "confidence": "high|medium|low"
            }
        """
        if results.get('error') or not results.get('rows'):
            return {
                "insights": {
                    "overview": "No results found or error occurred",
                    "key_findings": [],
                    "patterns": [],
                    "statistics": {},
                    "recommendations": ["Try refining your search criteria"]
                },
                "confidence": "low"
            }
        
        # Check APP_MODE to determine insight style
        app_mode = os.getenv('APP_MODE', 'seller').lower()
        is_customer_mode = app_mode == 'customer'
        
        print(f"🎯 Generating insights in {'CUSTOMER' if is_customer_mode else 'SELLER'} mode")
        
        # Prepare enhanced data summary for LLM with actual analysis
        row_count = len(results['rows'])
        columns = results['columns']
        all_rows = results['rows']  # Use all rows for statistical analysis
        
        # Pre-compute statistics to give LLM better context
        computed_stats = self._compute_statistics(all_rows, columns)
        
        # FOR CUSTOMER MODE: Remove partner-specific data from statistics
        if is_customer_mode:
            # Remove partner names and rankings
            computed_stats.pop('top_partners', None)
            computed_stats.pop('unique_partners', None)
            print("   🛡️ Filtered out partner rankings for customer mode")
            
            # Also remove orgName from sample rows
            filtered_columns = [col for col in columns if col != 'orgName']
        else:
            filtered_columns = columns
        
        # Sample rows for detailed analysis (include first, middle, last for variety)
        sample_size = min(15, row_count)
        if row_count <= 15:
            sample_rows = all_rows
        else:
            # Get diverse sample: first 5, middle 5, last 5
            sample_rows = (
                all_rows[:5] + 
                all_rows[row_count//2 - 2:row_count//2 + 3] + 
                all_rows[-5:]
            )
        
        # FOR CUSTOMER MODE: Filter orgName from sample rows
        if is_customer_mode:
            filtered_sample_rows = []
            for row in sample_rows:
                row_dict = self._row_to_dict(row, columns)
                if not row_dict:
                    continue
                filtered_row = {k: v for k, v in row_dict.items() if k != 'orgName'}
                filtered_sample_rows.append(filtered_row)
            sample_rows = filtered_sample_rows
            print(f"   🛡️ Removed orgName column from {len(sample_rows)} sample rows")
        
        # Different system prompts based on mode
        if is_customer_mode:
            # Customer Mode: Unbiased, no partner rankings or endorsements
            system_prompt = """You are an expert business analyst for the Industry Solutions Directory.

**CRITICAL - YOU ARE IN CUSTOMER MODE - EXTERNAL AUDIENCE**

This analysis is for EXTERNAL CUSTOMERS browsing for solutions. This is NOT for internal seller use.

**LEGAL COMPLIANCE REQUIREMENTS - ABSOLUTE RULES:**
❌ NEVER mention "for seller use" or "for internal use"
❌ NEVER rank partners by name or say "top partners" 
❌ NEVER use phrases like "Partner X leads with Y solutions"
❌ NEVER compare vendors directly (e.g., "Partner A vs Partner B")
❌ NEVER say phrases like "dominates", "stands out", "market leader"
❌ NEVER create partner leaderboards or rankings

✅ DO focus on solution CAPABILITIES and what they can do
✅ DO describe technology approaches available
✅ DO provide aggregate statistics (total counts, category distributions)
✅ DO remain completely neutral about all vendors

**Your Audience**: External customers evaluating solution options
**Your Goal**: Help them understand WHAT capabilities exist, not WHO provides them

**Analysis Framework:**

1. **Overview** (2-3 sentences)
   - Lead with solution capabilities and categories available
   - Establish market landscape without vendor bias
   - Focus on what solutions can do, not who provides them

2. **Key Findings** (4-6 capability-driven points)
   - Focus on WHAT capabilities exist (not WHO provides them)
   - Solution category distributions (e.g., "15 solutions in Cloud/AI, 8 in Security")
   - Industry coverage and applicability
   - Technology approaches available (AI, cloud, hybrid, etc.)
   - DO NOT mention specific partner names or counts

3. **Patterns** (3-4 observations)
   - Technology trends (AI adoption, cloud-native, etc.)
   - Solution clustering by capability
   - Integration approaches available
   - Deployment model variety

4. **Statistics** (aggregate metrics only)
   - Total solutions found
   - Solution area breakdown (categories with counts)
   - Industry distribution
   - Technology distribution (if applicable)
   - DO NOT include "top partners" or partner-specific stats

5. **Recommendations** (3-4 neutral next steps)
   - Explore specific solution categories or capabilities
   - Filter by industry or solution area
   - Investigate specific use cases or technologies
   - NO partner-specific recommendations

**Follow-Up Questions (CRITICAL):**
Generate 3-4 follow-up questions that are capability-focused:
- Based on solution areas found (e.g., "Compare Cloud and AI Platforms vs Security solutions")
- Based on industries or capabilities (e.g., "What solutions support [specific capability]?")
- Based on technology approaches (e.g., "Show me AI-powered solutions for [use case]")
- Based on sub-industries or themes (e.g., "What solutions focus on [theme] in [industry]?")

DO NOT generate questions that name specific partners or vendors.

**Response Format:**
Respond with a JSON object using this exact structure:
{{
    "insights": {{
        "overview": "neutral capability summary",
        "key_findings": ["capability-focused point", ...],
        "patterns": ["technology trend", ...],
        "statistics": {{"aggregate_metric": value, ...}},
        "recommendations": ["neutral exploration suggestion", ...],
        "follow_up_questions": ["capability-focused question", "category-based question", "industry-focused question"]
    }},
    "confidence": "high|medium|low"
}}
"""
        else:
            # Seller Mode: Internal use, can include partner insights and rankings
            system_prompt = """You are an expert business analyst for the Industry Solutions Directory.

**Objective**: Extract actionable insights from solution data to help Microsoft sellers identify the best partners and solutions for customers.

**Analysis Framework:**

1. **Overview** (2-3 sentences)
   - Lead with the most interesting/surprising finding
   - Establish context (market size, key players)
   - Highlight what makes this data set notable

2. **Key Findings** (4-6 data-driven points)
   - Focus on WHO (partners), WHAT (offerings), WHY (value)
   - Use specific numbers, percentages, distributions
   - Identify market leaders, gaps, concentrations
   - Note unexpected patterns or outliers
   - Name specific partners and their solution counts

3. **Patterns** (3-4 observations)
   - Technology trends and modern approaches
   - Solution clustering and categorization
   - Integration patterns and ecosystems
   - Deployment models and architectures

4. **Statistics** (quantitative metrics)
   - Partner distribution (top contributors with counts)
   - Solution area breakdown (categories with percentages)
   - Industry coverage and focus areas
   - Geographic or technology distributions

5. **Recommendations** (3-4 actionable next steps)
   - Specific partner portfolios to explore
   - Comparisons worth investigating
   - Notable individual solutions to review
   - Strategic insights for customer engagement

**Follow-Up Questions (CRITICAL):**
Generate 3-4 follow-up questions that are SPECIFIC to these findings:
- Based on top partners identified (e.g., "Show me all solutions from [PartnerName]")
- Based on solution areas or industries (e.g., "Compare [Area1] vs [Area2] solutions")
- Based on specific capabilities or themes (e.g., "What solutions focus on [capability]?")
- Based on geographic or sub-industry patterns (e.g., "Show me [SubIndustry] solutions in [Region]")

DO NOT include generic questions - ALL questions must be data-driven and specific to these results.

**Response Format:**
Respond with a JSON object using this exact structure:
{{
    "insights": {{
        "overview": "compelling summary with partner names",
        "key_findings": ["data-backed point with partner names", ...],
        "patterns": ["observed trend", ...],
        "statistics": {{"metric": value, "top_partners": ["Partner1 (count)", ...], ...}},
        "recommendations": ["partner-specific suggestion", ...],
        "follow_up_questions": ["specific partner-driven question", "relevant comparison", "contextual exploration"]
    }},
    "confidence": "high|medium|low"
}}
"""
        
        visible_columns = filtered_columns

        user_prompt = f"""Question: "{question}"

    Results Summary:
    - Total Results: {row_count}
    - Columns: {', '.join(visible_columns)}

    Sample Data (first 10 rows):
    {json.dumps(sample_rows[:10], indent=2, default=str)}

    Analyze these results and provide insights."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
                # Temperature removed - model doesn't support custom values
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate quality - reject generic responses
            if result.get('insights', {}).get('key_findings'):
                generic_phrases = ['query returned', 'matching solutions', 'results found']
                first_finding = result['insights']['key_findings'][0].lower() if result['insights']['key_findings'] else ''
                
                if any(phrase in first_finding for phrase in generic_phrases):
                    print(f"⚠️  Warning: Generic insight detected, using pre-computed stats as fallback")
                    # Force use of computed_stats
                    result['insights']['key_findings'] = [
                        f"Analysis of {row_count} solutions across {computed_stats.get('unique_partners', 'multiple')} partners",
                        f"Top providers: {', '.join(list(computed_stats.get('top_partners', {}).keys())[:3])}",
                        f"Primary solution areas: {', '.join(list(computed_stats.get('solution_areas', {}).keys())[:2])}"
                    ]
            
            # Ensure follow_up_questions exists and are data-driven
            if 'follow_up_questions' not in result.get('insights', {}):
                # Generate context-specific follow-ups based on actual data
                top_partners = list(computed_stats.get('top_partners', {}).keys())
                areas = list(computed_stats.get('solution_areas', {}).keys())
                industries = list(computed_stats.get('industries', {}).keys())
                
                result['insights']['follow_up_questions'] = []
                
                # Add partner-specific questions
                if len(top_partners) >= 2:
                    result['insights']['follow_up_questions'].append(f"Show me all solutions from {top_partners[0]}")
                    result['insights']['follow_up_questions'].append(f"Compare solutions from {top_partners[0]} and {top_partners[1]}")
                elif len(top_partners) == 1:
                    result['insights']['follow_up_questions'].append(f"Show me all solutions from {top_partners[0]}")
                    result['insights']['follow_up_questions'].append(f"What other partners offer similar solutions?")
                
                # Add solution area comparison if multiple areas exist
                if len(areas) >= 2:
                    result['insights']['follow_up_questions'].append(f"Compare {areas[0]} vs {areas[1]} solutions")
                
                # Add industry-specific question if industry data exists
                if len(industries) >= 1:
                    result['insights']['follow_up_questions'].append(f"What are the top solutions specifically for {industries[0]}?")
                
                # If we still have fewer than 3 questions, add more context-based ones
                if len(result['insights']['follow_up_questions']) < 3 and len(top_partners) >= 1 and len(areas) >= 1:
                    result['insights']['follow_up_questions'].append(f"Show me {areas[0]} solutions from {top_partners[0]}")
            
            return result
        
        except Exception as e:
            print(f"❌ Error in insight analysis: {str(e)}")
            # Use computed stats for fallback
            top_partners = list(computed_stats.get('top_partners', {}).keys())
            areas = list(computed_stats.get('solution_areas', {}).keys())
            industries = list(computed_stats.get('industries', {}).keys())
            
            # Generate context-specific follow-ups
            follow_ups = []
            if len(top_partners) >= 2:
                follow_ups.append(f"Show me all solutions from {top_partners[0]}")
                follow_ups.append(f"Compare solutions from {top_partners[0]} and {top_partners[1]}")
            elif len(top_partners) == 1:
                follow_ups.append(f"Show me all solutions from {top_partners[0]}")
            
            if len(areas) >= 2:
                follow_ups.append(f"Compare {areas[0]} vs {areas[1]} solutions")
            
            if len(industries) >= 1 and len(follow_ups) < 3:
                follow_ups.append(f"What are the top solutions for {industries[0]}?")
            
            # Add one more context-specific question if we have data
            if len(follow_ups) < 3 and len(top_partners) >= 1 and len(areas) >= 1:
                follow_ups.append(f"Show me {areas[0]} solutions from leading providers")
            
            return {
                "insights": {
                    "overview": f"Found {row_count} risk management solutions from {computed_stats.get('unique_partners', 'multiple')} partners",
                    "key_findings": [
                        f"Total solutions analyzed: {row_count}",
                        f"Top partners: {', '.join(top_partners[:3])}",
                        f"Solution areas: {', '.join(areas[:3])}"
                    ],
                    "patterns": ["Multiple solution approaches identified"],
                    "statistics": computed_stats,
                    "recommendations": ["Explore solutions by specific partner", "Filter by solution area"],
                    "follow_up_questions": follow_ups
                },
                "confidence": "medium",
                "error": str(e)
            }


class ResponseFormatter:
    """Agent 4: Formats insights and data into compelling user-facing response"""
    
    def __init__(self, llm_client: AzureOpenAI):
        self.llm_client = llm_client
        self.deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
    
    def format_response(self, question: str, insights: Dict, results: Dict, intent_info: Dict) -> str:
        """
        Create a compelling narrative response combining insights and data.
        
        Returns:
            Formatted markdown string with insights and data presentation
        """
        system_prompt = """You are a helpful assistant presenting Industry Solutions Directory insights.

Create a compelling, NARRATIVE response that tells a story with the data. Think like a business analyst presenting findings to executives.

CRITICAL REQUIREMENTS:
1. Write in flowing paragraphs, not bullet lists (except for specific findings)
2. Use a conversational, insightful tone
3. Highlight surprises, patterns, and strategic implications
4. Connect the dots between different findings
5. Use markdown effectively: **bold** for emphasis, ## for headers

STRUCTURE:
## Executive Summary
[2-3 sentences painting the big picture - what's the most important takeaway?]

## Market Landscape
[Narrative paragraph about the competitive landscape, who dominates, interesting patterns]

### Key Discoveries
[Use bullets ONLY here for specific findings - 3-5 data-backed points]

## Strategic Insights
[Narrative paragraph about what this means for decision-makers, technology trends, opportunities]

### Next Steps
[Short list of 2-3 specific actions they can take]

TONE EXAMPLES:
❌ BAD: "The query found 50 solutions. DXC has 18. Adobe has 12."
✅ GOOD: "The risk management landscape is dominated by two major players: **DXC Technology** commands 36% of the market with 18 solutions, while **Adobe** follows closely with 12 offerings focused primarily on behavioral analytics and customer journey intelligence."

Do NOT just list raw data - tell the story behind the numbers!
"""
        
        insights_content = insights.get('insights', {})
        overview = insights_content.get('overview', '')
        key_findings = insights_content.get('key_findings', [])
        patterns = insights_content.get('patterns', [])
        statistics = insights_content.get('statistics', {})
        recommendations = insights_content.get('recommendations', [])
        
        user_prompt = f"""Question: "{question}"

Intent: {intent_info.get('intent', 'query')}

Insights to present:
- Overview: {overview}
- Key Findings: {key_findings}
- Patterns: {patterns}
- Statistics: {statistics}
- Recommendations: {recommendations}

Create an engaging response. The detailed data table will be shown separately in another tab.
"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                # Temperature removed - model doesn't support custom values
            )
            
            content = response.choices[0].message.content
            
            # Track token usage
            tokens = None
            if hasattr(response, 'usage') and response.usage:
                tokens = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            
            return content, tokens
        
        except Exception as e:
            # Fallback formatting
            fallback = f"## Results for: {question}\n\n"
            fallback += f"{overview}\n\n"
            
            if key_findings:
                fallback += "### Key Findings\n"
                for finding in key_findings:
                    fallback += f"- {finding}\n"
                fallback += "\n"
            
            if statistics:
                fallback += "### Statistics\n"
                for key, value in statistics.items():
                    fallback += f"- **{key}**: {value}\n"
            
            return fallback, None


class MultiAgentPipeline:
    """
    Orchestrates the 4-agent workflow for intelligent query processing.
    
    Flow: Query Planner → SQL Executor → Insight Analyzer → Response Formatter
    """
    
    def __init__(self):
        """Initialize all agents and dependencies"""
        # Initialize Azure OpenAI client
        self.llm_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-08-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Initialize agents
        self.query_planner = QueryPlanner(self.llm_client)
        self.sql_executor = NL2SQLPipeline()  # Existing SQL agent
        self.insight_analyzer = InsightAnalyzer(self.llm_client)
        self.response_formatter = ResponseFormatter(self.llm_client)
        
        # Conversation state
        self.conversation_history = []
    
    def process_query(self, question: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main orchestration method - processes user query through all agents.
        
        Args:
            question: User's natural language question
            conversation_id: Optional conversation ID for context
        
        Returns:
            {
                "success": True/False,
                "question": original question,
                "intent": intent analysis results,
                "sql": generated SQL (if applicable),
                "explanation": SQL explanation,
                "insights": analyzed insights,
                "narrative": formatted response text,
                "data": {
                    "columns": [...],
                    "rows": [...]
                },
                "usage_stats": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int
                },
                "elapsed_time": float (seconds),
                "timestamp": ISO timestamp
            }
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # Initialize token tracking
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        
        try:
            # AGENT 1: Query Planner - Analyze intent
            print("🧠 Agent 1: Query Planner analyzing intent...")
            intent_info = self.query_planner.analyze_intent(question, self.conversation_history)
            
            # Track tokens from Agent 1
            if '_tokens' in intent_info:
                tokens = intent_info.pop('_tokens')
                total_prompt_tokens += tokens['prompt_tokens']
                total_completion_tokens += tokens['completion_tokens']
                total_tokens += tokens['total_tokens']
            print(f"   Intent: {intent_info['intent']}, New Query: {intent_info['needs_new_query']}")
            
            # AGENT 2: SQL Executor - Execute query if needed
            sql_result = None
            query_results = None
            
            if intent_info['needs_new_query']:
                print("🔍 Agent 2: SQL Executor generating query...")
                sql_result = self.sql_executor.generate_sql(question)
                
                # Check if query needs clarification
                if sql_result.get('needs_clarification'):
                    print(f"❓ Query needs clarification")
                    return {
                        "success": True,
                        "question": question,
                        "needs_clarification": True,
                        "clarification_question": sql_result.get('clarification_question'),
                        "suggested_refinements": sql_result.get('suggested_refinements', []),
                        "sql": sql_result.get('sql'),  # Still provide the broad query SQL
                        "explanation": sql_result.get('explanation'),
                        "confidence": sql_result.get('confidence', 'low'),
                        "row_count": 0,  # Add row_count for frontend compatibility
                        "columns": [],  # Add empty columns array
                        "rows": [],  # Add empty rows array
                        "timestamp": timestamp
                    }
                
                if sql_result.get('sql'):
                    # Validate that sql is a string, not a dict (compound queries not supported)
                    if isinstance(sql_result['sql'], dict):
                        # LLM tried to generate multiple queries - ask for clarification
                        return {
                            "success": True,
                            "question": question,
                            "needs_clarification": True,
                            "clarification_question": "Your question requires multiple separate queries. Could you please ask them one at a time?",
                            "suggested_refinements": [
                                "What agent-based solutions do we have?",
                                "How many solutions are focused on healthcare?"
                            ],
                            "row_count": 0,
                            "columns": [],
                            "rows": [],
                            "timestamp": timestamp
                        }
                    
                    print("⚙️  Agent 2: Executing SQL query...")
                    query_results = self.sql_executor.execute_sql(sql_result['sql'])
                else:
                    return {
                        "success": False,
                        "question": question,
                        "error": "Failed to generate SQL query",
                        "timestamp": timestamp
                    }
            else:
                # Use results from previous query in conversation
                if self.conversation_history:
                    last_exchange = self.conversation_history[-1]
                    query_results = last_exchange.get('raw_results', {})
                    
                    # Check if previous results actually have data
                    previous_row_count = query_results.get('row_count', 0)
                    if previous_row_count == 0:
                        print("⚠️  Previous query had 0 results - running new query instead")
                        # Force new query since there's nothing to analyze
                        sql_result = self.sql_executor.generate_sql(question)
                        
                        if sql_result.get('sql'):
                            print("⚙️  Agent 2: Executing SQL query...")
                            query_results = self.sql_executor.execute_sql(sql_result['sql'])
                        else:
                            return {
                                "success": False,
                                "question": question,
                                "error": "Failed to generate SQL query",
                                "timestamp": timestamp
                            }
                    else:
                        sql_result = {"sql": "-- Using cached results", "explanation": "Analyzing previous results"}
                else:
                    return {
                        "success": False,
                        "question": question,
                        "error": "No previous results to analyze",
                        "timestamp": timestamp
                    }
            
            # Check for SQL execution errors
            if query_results.get('error'):
                return {
                    "success": False,
                    "question": question,
                    "sql": sql_result.get('sql'),
                    "error": query_results['error'],
                    "timestamp": timestamp
                }
            
            # AGENT 3: Insight Analyzer - Extract insights
            print("📊 Agent 3: Insight Analyzer extracting insights...")
            insights = self.insight_analyzer.analyze_results(question, query_results, intent_info)
            print(f"   Confidence: {insights.get('confidence', 'unknown')}")
            
            # Track tokens from Agent 3
            if '_tokens' in insights:
                tokens = insights.pop('_tokens')
                total_prompt_tokens += tokens['prompt_tokens']
                total_completion_tokens += tokens['completion_tokens']
                total_tokens += tokens['total_tokens']
            
            # AGENT 4: Response Formatter - Create narrative
            print("✍️  Agent 4: Response Formatter creating narrative...")
            narrative, formatter_tokens = self.response_formatter.format_response(question, insights, query_results, intent_info)
            
            # Track tokens from Agent 4
            if formatter_tokens:
                total_prompt_tokens += formatter_tokens['prompt_tokens']
                total_completion_tokens += formatter_tokens['completion_tokens']
                total_tokens += formatter_tokens['total_tokens']
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Build response
            response = {
                "success": True,
                "question": question,
                "intent": intent_info,
                "sql": sql_result.get('sql'),
                "explanation": sql_result.get('explanation'),
                "confidence": sql_result.get('confidence'),
                "insights": insights.get('insights', {}),
                "narrative": narrative,
                "data": {
                    "columns": query_results.get('columns', []),
                    "rows": query_results.get('rows', [])
                },
                "usage_stats": {
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_tokens
                },
                "elapsed_time": round(elapsed_time, 2),
                "timestamp": timestamp
            }
            
            # Print usage summary
            print(f"📊 Token Usage: {total_tokens} total ({total_prompt_tokens} input, {total_completion_tokens} output)")
            print(f"⏱️  Elapsed Time: {elapsed_time:.2f}s")
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "intent": intent_info['intent'],
                "summary": insights.get('insights', {}).get('overview', ''),
                "raw_results": query_results
            })
            
            # Keep only last 10 exchanges
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            print("✅ Multi-agent processing complete!\n")
            return response
        
        except Exception as e:
            print(f"❌ Error in multi-agent pipeline: {str(e)}")
            return {
                "success": False,
                "question": question,
                "error": f"Pipeline error: {str(e)}",
                "timestamp": timestamp
            }
