#!/usr/bin/env python3
"""
FastAPI Backend for NL2SQL Chat Interface
Provides REST API endpoints for the React frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
from datetime import datetime
import json
import re

# Add parent directory to path to import pipelines
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data-ingestion/sql-direct'))
from multi_agent_pipeline import MultiAgentPipeline

# Helper function to strip HTML tags
def strip_html(text):
    """Remove HTML tags from text"""
    if text is None or text == "(Not Set)":
        return text
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text_without_tags = re.sub(clean, '', str(text))
    # Replace multiple spaces/newlines with single space
    text_without_tags = re.sub(r'\s+', ' ', text_without_tags)
    return text_without_tags.strip()

# Initialize FastAPI app
app = FastAPI(
    title="ISD NL2SQL API",
    description="Natural Language to SQL API for Industry Solutions Directory",
    version="1.0.0"
)

# Configure CORS for React frontend
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Read from environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Multi-Agent pipeline
pipeline = MultiAgentPipeline()

# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    question: str
    intent: Optional[Dict[str, Any]] = None  # New: intent analysis
    narrative: Optional[str] = None  # New: formatted insights narrative
    insights: Optional[Dict[str, Any]] = None  # New: structured insights
    sql: Optional[str] = None
    explanation: Optional[str] = None
    confidence: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    error: Optional[str] = None
    usage_stats: Optional[Dict[str, int]] = None  # Token usage statistics
    elapsed_time: Optional[float] = None  # Time elapsed in seconds
    timestamp: str

class ConversationExportRequest(BaseModel):
    messages: List[Dict[str, Any]]
    mode: str = 'seller'

class ExampleQuestionsResponse(BaseModel):
    categories: Dict[str, List[str]]

# In-memory storage for conversation history (in production, use Redis or DB)
conversations: Dict[str, List[Dict[str, Any]]] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ISD NL2SQL API",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    app_mode = os.getenv('APP_MODE', 'seller').lower()
    return {
        "status": "healthy",
        "database": "connected",
        "pipeline": "ready",
        "mode": app_mode,  # customer or seller
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a natural language query using multi-agent pipeline
    Returns insights narrative + structured data
    """
    try:
        # Process query through multi-agent pipeline
        result = pipeline.process_query(request.question, request.conversation_id)
        
        if not result['success']:
            return QueryResponse(
                success=False,
                question=request.question,
                error=result.get('error', 'Unknown error'),
                timestamp=result['timestamp']
            )
        
        # Convert rows to clean data (HTML stripping)
        rows_data = []
        if result['data']['rows']:
            html_columns = [
                'solutionDescription', 'industryDescription', 'SubIndustryDescription',
                'solAreaDescription', 'orgDescription', 'areaSolutionDescription',
                'industryThemeDesc', 'solutionPlayDesc', 'resourceLinkDescription',
                'THEME', 'DESCRIPTION', 'DESC', 'SOLUTION_DESCRIPTION'
            ]
            
            for row in result['data']['rows']:
                row_dict = {}
                for col in result['data']['columns']:
                    try:
                        value = row[col]
                    except (KeyError, TypeError):
                        idx = result['data']['columns'].index(col)
                        value = row[idx]
                    
                    if value is None:
                        row_dict[col] = "(Not Set)"
                    elif hasattr(value, 'isoformat'):
                        row_dict[col] = value.isoformat()
                    else:
                        str_value = str(value) if value != "NULL" else "(Not Set)"
                        col_lower = col.lower()
                        if (col in html_columns or 
                            any(keyword in col_lower for keyword in ['desc', 'description', 'theme'])):
                            str_value = strip_html(str_value)
                        row_dict[col] = str_value
                rows_data.append(row_dict)
        
        # Store in conversation history
        if request.conversation_id:
            if request.conversation_id not in conversations:
                conversations[request.conversation_id] = []
            conversations[request.conversation_id].append({
                "question": request.question,
                "narrative": result.get('narrative'),
                "timestamp": result['timestamp']
            })
        
        # Return comprehensive response with insights
        return QueryResponse(
            success=True,
            question=request.question,
            intent=result.get('intent'),
            narrative=result.get('narrative'),
            insights=result.get('insights'),
            sql=result.get('sql'),
            explanation=result.get('explanation'),
            confidence=result.get('confidence'),
            columns=result['data']['columns'],
            rows=rows_data,
            row_count=len(rows_data),
            usage_stats=result.get('usage_stats'),
            elapsed_time=result.get('elapsed_time'),
            timestamp=result['timestamp']
        )
        
        # Store in conversation history
        if request.conversation_id:
            if request.conversation_id not in conversations:
                conversations[request.conversation_id] = []
            conversations[request.conversation_id].append({
                'timestamp': datetime.now().isoformat(),
                'question': request.question,
                'sql': sql_result['sql'],
                'row_count': result['row_count']
            })
        
        return QueryResponse(
            success=True,
            question=request.question,
            sql=sql_result['sql'],
            explanation=sql_result['explanation'],
            confidence=sql_result['confidence'],
            columns=result['columns'],
            rows=rows_data,
            row_count=result['row_count'],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            question=request.question,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/api/query/stream")
async def stream_query(request: QueryRequest):
    """
    Execute a natural language query with streaming response.
    Returns SSE events: metadata (agents 1-3), deltas (agent 4 tokens), done (final stats).
    """
    # HTML-column list for stripping tags from SSE metadata rows
    html_columns = [
        'solutionDescription', 'industryDescription', 'SubIndustryDescription',
        'solAreaDescription', 'orgDescription', 'areaSolutionDescription',
        'industryThemeDesc', 'solutionPlayDesc', 'resourceLinkDescription',
        'THEME', 'DESCRIPTION', 'DESC', 'SOLUTION_DESCRIPTION'
    ]

    def _clean_rows(columns, rows):
        """Convert pyodbc rows to JSON-safe dicts with HTML stripping."""
        cleaned = []
        for row in rows:
            row_dict = {}
            for col in columns:
                try:
                    value = row[col]
                except (KeyError, TypeError):
                    idx = columns.index(col)
                    value = row[idx]
                if value is None:
                    row_dict[col] = "(Not Set)"
                elif hasattr(value, 'isoformat'):
                    row_dict[col] = value.isoformat()
                else:
                    str_value = str(value) if value != "NULL" else "(Not Set)"
                    col_lower = col.lower()
                    if (col in html_columns or
                        any(kw in col_lower for kw in ['desc', 'description', 'theme'])):
                        str_value = strip_html(str_value)
                    row_dict[col] = str_value
            cleaned.append(row_dict)
        return cleaned

    def event_generator():
        for event in pipeline.process_query_stream(request.question, request.conversation_id):
            if event["type"] == "metadata" and "data" in event:
                # Clean rows for JSON serialization before sending
                data = event.get("data", {})
                if data.get("rows"):
                    event["data"]["rows"] = _clean_rows(data["columns"], data["rows"])
                    event["row_count"] = len(event["data"]["rows"])
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/examples", response_model=ExampleQuestionsResponse)
async def get_example_questions():
    """
    Get categorized example questions
    """
    examples = {
        "Defense Industrial Base": [
            "What solutions support defense modernization and military readiness?",
            "Show me cybersecurity solutions for defense contractors and the defense industrial base",
            "What solutions help with secure supply chain management for defense organizations?",
            "Show me solutions for defense logistics and mission-critical operations",
            "What AI-powered solutions exist for defense intelligence and threat analysis?",
            "Show me solutions for secure communications and classified data management"
        ],
        "Education": [
            "What solutions help improve student engagement and learning outcomes?",
            "Show me campus management and administrative solutions for education",
            "What fundraising and donor management solutions are available for higher education?",
            "Show me student lifecycle management platforms",
            "What learning analytics and educational data platforms are available?",
            "Show me alumni relationship management and engagement solutions"
        ],
        "Energy & Resources": [
            "What sustainability and carbon management solutions are available for energy companies?",
            "Show me asset management solutions for oil and gas operations",
            "What smart grid and energy distribution solutions are available?",
            "Show me predictive maintenance solutions for energy infrastructure",
            "What emissions tracking and management solutions help with environmental compliance?",
            "Show me renewable energy optimization and management solutions"
        ],
        "Financial Services": [
            "What financial services solutions help with risk management?",
            "Show me solutions for anti-money laundering and financial crime prevention",
            "What solutions help with regulatory compliance in financial services?",
            "What are the best banking solutions for improving customer engagement and retention?",
            "Show me fraud detection and prevention solutions for financial institutions",
            "What solutions support core banking modernization and digital transformation?"
        ],
        "Government": [
            "What solutions improve citizen engagement and digital government services?",
            "Show me case management solutions for government agencies",
            "What public safety and emergency response solutions are available?",
            "Show me smart city and urban management solutions",
            "What grant management and funding distribution systems are available?",
            "Show me solutions for government transparency and open data initiatives"
        ],
        "Healthcare & Life Sciences": [
            "Show me AI-powered solutions for healthcare and life sciences",
            "What solutions help improve patient engagement and care coordination?",
            "Show me electronic health record and clinical data management solutions",
            "What solutions enable remote patient monitoring and telehealth?",
            "Show me solutions for clinical workflow optimization and automation",
            "What population health management and analytics solutions are available?"
        ],
        "Manufacturing & Mobility": [
            "What manufacturing solutions leverage IoT and AI for smart factories?",
            "Show me predictive maintenance solutions for manufacturing equipment",
            "What solutions optimize supply chain management for manufacturers?",
            "Show me smart factory and Industry 4.0 solutions",
            "What solutions help with quality control and automated defect detection?",
            "Show me asset performance management and mobility solutions"
        ],
        "Media & Entertainment": [
            "What solutions support content creation and digital media management?",
            "Show me streaming and media delivery platform solutions",
            "What solutions help with audience analytics and engagement for media companies?",
            "Show me solutions for digital rights management and content monetization",
            "What AI-powered solutions exist for media personalization and recommendation?",
            "Show me solutions for live event management and broadcasting"
        ],
        "Retail & Consumer Goods": [
            "What solutions enhance customer experience in retail and consumer goods?",
            "Show me inventory management and stock optimization solutions for retail",
            "What modern point of sale and retail transaction solutions are available?",
            "Show me solutions for creating personalized shopping experiences",
            "What omnichannel retail and unified commerce solutions are available?",
            "Show me supply chain visibility and logistics solutions for retail"
        ],
        "Telecommunications": [
            "What solutions help telecom companies with network optimization and management?",
            "Show me customer experience and churn reduction solutions for telecom",
            "What 5G and next-generation network solutions are available?",
            "Show me solutions for telecom billing, revenue management, and monetization",
            "What AI-powered solutions exist for telecom network operations?",
            "Show me solutions for telecom fraud detection and prevention"
        ],
        "Cross-Industry": [
            "Show me comprehensive cybersecurity and threat protection solutions",
            "What AI and machine learning solutions are available across industries?",
            "Show me cloud migration and modernization solutions",
            "What data analytics and business intelligence platforms are available?",
            "Show me customer relationship management and CRM solutions",
            "What sustainability and ESG reporting solutions are available?"
        ]
    }
    
    return ExampleQuestionsResponse(categories=examples)

@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieve conversation history
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id],
        "message_count": len(conversations[conversation_id])
    }

@app.post("/api/conversation/export")
async def export_conversation(request: ConversationExportRequest):
    """
    Export conversation to JSON
    """
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "mode": request.mode,
        "total_queries": len([m for m in request.messages if m.get('role') == 'user']),
        "messages": request.messages
    }
    
    return export_data

@app.get("/api/stats")
async def get_statistics():
    """
    Get database and usage statistics
    """
    return {
        "database": {
            "view": "dbo.vw_ISDSolution_All",
            "total_rows": 5118,
            "total_columns": 33
        },
        "safety": {
            "mode": "READ-ONLY",
            "validation_layers": 4
        },
        "model": {
            "provider": "Azure OpenAI",
            "model": "GPT-4.1-mini"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
