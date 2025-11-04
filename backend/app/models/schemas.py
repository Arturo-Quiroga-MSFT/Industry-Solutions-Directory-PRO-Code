"""
Data models for the Industry Solutions Chat API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role in a conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SearchFilter(BaseModel):
    """Filters for solution search"""
    industries: Optional[List[str]] = Field(None, description="Filter by industry categories")
    technologies: Optional[List[str]] = Field(None, description="Filter by technology categories")
    partner_name: Optional[str] = Field(None, description="Filter by partner name")


class ChatMessage(BaseModel):
    """A single message in a chat conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="Source citations for the response")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    filters: Optional[SearchFilter] = Field(None, description="Filters to apply to solution search")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What healthcare AI solutions are available?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "filters": {
                    "industries": ["Healthcare & Life Sciences"],
                    "technologies": ["AI"]
                }
            }
        }


class Citation(BaseModel):
    """Citation for a source document"""
    solution_name: str
    partner_name: str
    description: str
    url: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="AI-generated response")
    session_id: str = Field(..., description="Session ID for this conversation")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    message_id: str = Field(..., description="Unique identifier for this message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on your healthcare AI query, I found several relevant solutions...",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "citations": [
                    {
                        "solution_name": "Healthcare AI Platform",
                        "partner_name": "Partner Corp",
                        "description": "AI-powered healthcare analytics",
                        "url": "https://solutions.example.com/healthcare-ai",
                        "relevance_score": 0.95
                    }
                ],
                "message_id": "msg-12345"
            }
        }


class ChatHistoryResponse(BaseModel):
    """Response model for chat history endpoint"""
    session_id: str
    messages: List[ChatMessage]
    metadata: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint"""
    message_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Optional feedback comment")


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str
    version: str
    dependencies: Dict[str, str]


class PartnerSolution(BaseModel):
    """Model for a partner solution stored in search index"""
    id: str
    solution_name: str
    partner_name: str
    description: str
    industries: List[str]
    technologies: List[str]
    solution_url: str
    content_vector: Optional[List[float]] = None
    chunk_text: str
    metadata: Optional[Dict[str, Any]] = None
