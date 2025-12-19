#!/usr/bin/env python3
"""
FastAPI Backend for NL2SQL Chat Interface
Provides REST API endpoints for the React frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
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
    timestamp: str

class ConversationExportRequest(BaseModel):
    messages: List[Dict[str, Any]]

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
    return {
        "status": "healthy",
        "database": "connected",
        "pipeline": "ready",
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

@app.get("/api/examples", response_model=ExampleQuestionsResponse)
async def get_example_questions():
    """
    Get categorized example questions
    """
    examples = {
        "Financial Services": [
            "What financial services solutions help with risk management?",
            "Show me anti-money laundering solutions",
            "What solutions help with regulatory compliance?",
            "Banking solutions for customer engagement",
            "Fraud detection solutions",
            "Core banking modernization solutions"
        ],
        "Healthcare": [
            "Show me AI-powered healthcare solutions",
            "What solutions improve patient engagement?",
            "Electronic health record solutions",
            "Remote patient monitoring solutions",
            "Clinical workflow optimization",
            "Population health management solutions"
        ],
        "Manufacturing": [
            "What manufacturing solutions use IoT and AI?",
            "Show me predictive maintenance solutions",
            "Supply chain optimization for manufacturing",
            "Smart factory solutions",
            "Quality control and defect detection",
            "Asset performance management"
        ],
        "Education": [
            "What solutions help with student engagement?",
            "Campus management solutions",
            "Fundraising solutions for higher education",
            "Student lifecycle management",
            "Learning analytics platforms",
            "Alumni relationship management"
        ],
        "Retail & Consumer Goods": [
            "Customer experience solutions for retail",
            "Inventory management solutions",
            "Point of sale systems",
            "Personalized shopping experiences",
            "Omnichannel retail solutions",
            "Supply chain visibility for retail"
        ],
        "Energy & Resources": [
            "Sustainability solutions for energy companies",
            "Asset management for oil and gas",
            "Smart grid solutions",
            "Predictive maintenance for energy infrastructure",
            "Emissions management solutions",
            "Renewable energy optimization"
        ],
        "Government": [
            "Citizen engagement solutions",
            "Case management for government agencies",
            "Public safety solutions",
            "Smart city solutions",
            "Grant management systems"
        ],
        "Cross-Industry": [
            "Show me all cybersecurity solutions",
            "What AI and machine learning solutions are available?",
            "Cloud migration solutions",
            "Data analytics platforms",
            "Customer relationship management solutions",
            "Sustainability and ESG solutions"
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
