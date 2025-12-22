#!/usr/bin/env python3
"""
Multi-Agent Pipeline for ISD Query Processing
Four-agent architecture: Query Planner → SQL Executor → Insight Analyzer → Response Formatter
"""

import os
import json
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
        
        # Prepare enhanced data summary for LLM with actual analysis
        row_count = len(results['rows'])
        columns = results['columns']
        all_rows = results['rows']  # Use all rows for statistical analysis
        
        # Pre-compute statistics to give LLM better context
        computed_stats = self._compute_statistics(all_rows, columns)
        
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
        
        system_prompt = """You are an expert business analyst for the Industry Solutions Directory.

**Objective**: Extract actionable insights from solution data to help decision-makers.

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
   - Specific filters or refinements to explore
   - Comparisons worth investigating
   - Notable individual solutions to review
   - Strategic insights for decision-making

**Quality Standards:**
- Avoid generic statements like "query returned X results"
- Use specific data points and percentages
- Identify business value and strategic implications
- Connect findings to real-world use cases
- Suggest follow-up questions that add value

**Output Format:**
{{
    "insights": {{
        "overview": "compelling summary",
        "key_findings": ["data-backed point", ...],
        "patterns": ["observed trend", ...],
        "statistics": {{"metric": value, ...}},
        "recommendations": ["actionable suggestion", ...],
        "follow_up_questions": ["relevant next query", ...]
    }},
    "confidence": "high|medium|low"
}}
"""
        
        user_prompt = f"""Question: "{question}"

Results Summary:
- Total Results: {row_count}
- Columns: {', '.join(columns)}

Sample Data (first 10 rows):
{json.dumps(sample_rows, indent=2, default=str)}

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
            
            # Ensure follow_up_questions exists
            if 'follow_up_questions' not in result.get('insights', {}):
                # Generate default follow-ups based on data
                top_partners = list(computed_stats.get('top_partners', {}).keys())[:2]
                areas = list(computed_stats.get('solution_areas', {}).keys())[:2]
                
                result['insights']['follow_up_questions'] = []
                if top_partners:
                    result['insights']['follow_up_questions'].append(f"Show me all solutions from {top_partners[0]}")
                if len(areas) > 1:
                    result['insights']['follow_up_questions'].append(f"Compare {areas[0]} vs {areas[1]} solutions")
                result['insights']['follow_up_questions'].append("What are the latest solutions added?")
            
            return result
        
        except Exception as e:
            print(f"❌ Error in insight analysis: {str(e)}")
            # Use computed stats for fallback
            top_partners = list(computed_stats.get('top_partners', {}).keys())
            areas = list(computed_stats.get('solution_areas', {}).keys())
            
            follow_ups = []
            if len(top_partners) > 0:
                follow_ups.append(f"Show me all solutions from {top_partners[0]}")
            if len(areas) > 1:
                follow_ups.append(f"Compare {areas[0]} vs {areas[1]} solutions")
            follow_ups.append("What are the latest solutions available?")
            
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
            
            return response.choices[0].message.content
        
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
            
            return fallback


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
                "timestamp": ISO timestamp
            }
        """
        timestamp = datetime.now().isoformat()
        
        try:
            # AGENT 1: Query Planner - Analyze intent
            print("🧠 Agent 1: Query Planner analyzing intent...")
            intent_info = self.query_planner.analyze_intent(question, self.conversation_history)
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
            
            # AGENT 4: Response Formatter - Create narrative
            print("✍️  Agent 4: Response Formatter creating narrative...")
            narrative = self.response_formatter.format_response(question, insights, query_results, intent_info)
            
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
                "timestamp": timestamp
            }
            
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
