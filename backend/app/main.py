"""
Main FastAPI application for Industry Solutions Chat API
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from app.config import settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    FeedbackRequest,
    HealthResponse,
    MessageRole,
    Citation
)
from app.services.search_service import SearchService
from app.services.openai_service import OpenAIService
from app.services.cosmos_service import CosmosDBService

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
search_service: SearchService = None
openai_service: OpenAIService = None
cosmos_service: CosmosDBService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global search_service, openai_service, cosmos_service
    
    # Startup
    logger.info("Starting Industry Solutions Chat API...")
    try:
        search_service = SearchService()
        openai_service = OpenAIService()
        # cosmos_service = CosmosDBService()  # Temporarily disabled while Cosmos DB updates
        logger.info("Search and OpenAI services initialized successfully (Cosmos DB disabled)")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Industry Solutions Chat API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description="AI-powered chat assistant for Microsoft Industry Solutions Directory"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check all services
        search_healthy = await search_service.health_check()
        openai_healthy = await openai_service.health_check()
        # cosmos_healthy = await cosmos_service.health_check()  # Temporarily disabled
        
        dependencies = {
            "azure_ai_search": "healthy" if search_healthy else "unhealthy",
            "azure_openai": "healthy" if openai_healthy else "unhealthy",
            "azure_cosmos_db": "disabled"  # Temporarily disabled while updating
        }
        
        overall_healthy = all([search_healthy, openai_healthy])  # Don't require Cosmos for now
        
        return HealthResponse(
            status="healthy" if overall_healthy else "degraded",
            version=settings.app_version,
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    Implements RAG pattern: Search -> Retrieve -> Generate
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Ensure session exists (disabled while Cosmos DB updates)
        # await cosmos_service.create_session(session_id)
        
        # Step 1: Search for relevant solutions
        logger.info(f"Searching for: {request.message[:50]}...")
        citations = await search_service.semantic_hybrid_search(
            query=request.message,
            filters=request.filters
        )
        
        # Step 2: Retrieve chat history for context (disabled - no history without Cosmos)
        # chat_history = await cosmos_service.get_session_history(session_id)
        chat_history = []  # Empty history while Cosmos DB disabled
        
        # Step 3: Generate response using RAG
        logger.info(f"Generating response with {len(citations)} citations...")
        response_text = await openai_service.generate_response(
            user_message=request.message,
            context=citations,
            chat_history=chat_history
        )
        
        # Step 4: Store messages in Cosmos DB (disabled)
        # await cosmos_service.add_message(session_id=session_id, role=MessageRole.USER, content=request.message)
        # message_id = await cosmos_service.add_message(session_id=session_id, role=MessageRole.ASSISTANT, content=response_text, citations=[citation.model_dump() for citation in citations])
        message_id = f"msg-{uuid.uuid4()}"  # Generate temporary message ID
        
        logger.warning("Cosmos DB disabled - session history not persisted")
        
        # Return response
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            citations=citations,
            message_id=message_id
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/api/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    # Cosmos DB disabled - return unavailable
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Chat history temporarily unavailable (Cosmos DB disabled)"
    )


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a message"""
    try:
        # Here you would typically store feedback in a database
        # For now, just log it
        logger.info(f"Feedback received - Message: {request.message_id}, Rating: {request.rating}")
        
        if request.comment:
            logger.info(f"Comment: {request.comment}")
        
        return {"status": "success", "message": "Feedback received"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting feedback"
        )


@app.get("/api/facets")
async def get_facets():
    """Get available facets for filters"""
    try:
        facets = await search_service.get_facets()
        return facets
    except Exception as e:
        logger.error(f"Error retrieving facets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving facets"
        )


@app.delete("/api/chat/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        success = await cosmos_service.delete_session(session_id)
        if success:
            return {"status": "success", "message": f"Session {session_id} deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting session"
        )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
