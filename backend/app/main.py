"""
Main FastAPI application for Industry Solutions Chat API
"""
import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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
        cosmos_service = CosmosDBService()
        logger.info("All services initialized successfully")
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
        cosmos_healthy = await cosmos_service.health_check()
        
        dependencies = {
            "azure_ai_search": "healthy" if search_healthy else "unhealthy",
            "azure_openai": "healthy" if openai_healthy else "unhealthy",
            "azure_cosmos_db": "healthy" if cosmos_healthy else "unhealthy"
        }
        
        overall_healthy = all([search_healthy, openai_healthy, cosmos_healthy])
        
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
        
        # Ensure session exists
        await cosmos_service.create_session(session_id)
        
        # Step 1: Search for relevant solutions
        logger.info(f"Searching for: {request.message[:50]}...")
        citations = await search_service.semantic_hybrid_search(
            query=request.message,
            filters=request.filters
        )
        
        # Step 2: Retrieve chat history for context
        chat_history = await cosmos_service.get_session_history(session_id)
        
        # Step 3: Generate response using RAG
        logger.info(f"Generating response with {len(citations)} citations...")
        response_text = await openai_service.generate_response(
            user_message=request.message,
            context=citations,
            chat_history=chat_history
        )
        
        # Step 4: Generate follow-up questions
        logger.info("Generating follow-up questions...")
        follow_up_questions = await openai_service.generate_follow_up_questions(
            user_query=request.message,
            assistant_response=response_text,
            citations=citations
        )
        
        # Step 5: Store messages in Cosmos DB
        # Store user message
        await cosmos_service.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=request.message
        )
        
        # Store assistant message with citations and follow-up questions
        message_id = await cosmos_service.add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            citations=[citation.model_dump() for citation in citations],
            follow_up_questions=follow_up_questions
        )
        
        # Return response
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            citations=citations,
            message_id=message_id,
            follow_up_questions=follow_up_questions
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint
    Implements RAG pattern with Server-Sent Events (SSE) streaming
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Ensure session exists
        await cosmos_service.create_session(session_id)
        
        # Search for relevant solutions
        logger.info(f"Searching for: {request.message[:50]}...")
        citations = await search_service.semantic_hybrid_search(
            query=request.message,
            filters=request.filters
        )
        
        # Retrieve chat history for context
        chat_history = await cosmos_service.get_session_history(session_id)
        
        # Store user message
        await cosmos_service.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=request.message
        )
        
        async def generate_stream():
            """Generator function for SSE streaming"""
            try:
                # Send session info and citations first
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\\n\\n"
                yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]})}\\n\\n"
                
                # Stream the response
                full_response = ""
                async for chunk in openai_service.generate_response_stream(
                    user_message=request.message,
                    context=citations,
                    chat_history=chat_history
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Generate follow-up questions
                logger.info("Generating follow-up questions...")
                follow_up_questions = await openai_service.generate_follow_up_questions(
                    user_query=request.message,
                    assistant_response=full_response,
                    citations=citations
                )
                
                # Store assistant message with citations and follow-up questions
                message_id = await cosmos_service.add_message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    citations=[citation.model_dump() for citation in citations],
                    follow_up_questions=follow_up_questions
                )
                
                # Send follow-up questions
                yield f"data: {json.dumps({'type': 'follow_up', 'questions': follow_up_questions})}\n\n"
                
                # Send message ID
                yield f"data: {json.dumps({'type': 'message_id', 'message_id': message_id})}\n\n"
                
                # Send done signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/api/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        messages = await cosmos_service.get_session_history(session_id)
        metadata = await cosmos_service.get_session_metadata(session_id)
        
        if not messages and not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            metadata=metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat history"
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


@app.post("/api/chat/summary/{session_id}")
async def generate_conversation_summary(session_id: str):
    """
    Generate an AI-powered summary of the conversation
    Includes user questions and recommendations provided
    """
    try:
        # Get chat history
        messages = await cosmos_service.get_session_history(session_id)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Build conversation text for summarization
        conversation_text = "\n\n".join([
            f"{'User' if msg.role == MessageRole.USER else 'Assistant'}: {msg.content}"
            for msg in messages
        ])
        
        # Generate summary using GPT
        summary_prompt = f"""Please create a concise summary of this conversation between a user and an AI assistant helping find Microsoft partner solutions.

Include:
1. **User's Key Questions**: List the main questions or topics the user asked about
2. **Recommendations Provided**: Summarize the partner solutions that were recommended
3. **Key Insights**: Any important takeaways or patterns in what the user was looking for

Conversation:
{conversation_text}

Please format the summary in markdown with clear sections."""

        summary = await openai_service.generate_summary(summary_prompt)
        
        return {
            "session_id": session_id,
            "summary": summary,
            "message_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating summary"
        )


@app.get("/api/chat/export/{session_id}")
async def export_conversation(session_id: str, format: str = "markdown"):
    """
    Export conversation as downloadable file (markdown or text)
    Includes summary, full conversation, and citations
    """
    try:
        # Get chat history and metadata
        messages = await cosmos_service.get_session_history(session_id)
        metadata = await cosmos_service.get_session_metadata(session_id)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Generate summary first
        summary_response = await generate_conversation_summary(session_id)
        summary = summary_response["summary"]
        
        # Build export content
        if format.lower() == "markdown":
            content = f"""# Industry Solutions Directory - Conversation Export

**Session ID**: {session_id}
**Date**: {metadata.get('startTime', 'N/A') if metadata else 'N/A'}
**Messages**: {len(messages)}

---

## Summary

{summary}

---

## Full Conversation

"""
            # Add each message
            for i, msg in enumerate(messages, 1):
                role = "You" if msg.role == MessageRole.USER else "Assistant"
                content += f"\n### {role} (Message {i})\n\n{msg.content}\n"
                
                # Add citations if present
                if msg.citations:
                    content += "\n**Solutions Referenced:**\n"
                    for cit in msg.citations:
                        content += f"- **{cit.get('solution_name')}** by {cit.get('partner_name')}\n"
                        content += f"  - {cit.get('url')}\n"
                
                content += "\n---\n"
            
            content += f"\n\n*Exported from Industry Solutions Directory on {metadata.get('startTime', 'N/A') if metadata else 'N/A'}*\n"
        
        else:  # Plain text format
            content = f"""Industry Solutions Directory - Conversation Export
{'=' * 60}

Session ID: {session_id}
Date: {metadata.get('startTime', 'N/A') if metadata else 'N/A'}
Messages: {len(messages)}

{'=' * 60}
SUMMARY
{'=' * 60}

{summary}

{'=' * 60}
FULL CONVERSATION
{'=' * 60}

"""
            for i, msg in enumerate(messages, 1):
                role = "YOU" if msg.role == MessageRole.USER else "ASSISTANT"
                content += f"\n{role} (Message {i}):\n{'-' * 40}\n{msg.content}\n"
                
                if msg.citations:
                    content += "\nSolutions Referenced:\n"
                    for cit in msg.citations:
                        content += f"  - {cit.get('solution_name')} by {cit.get('partner_name')}\n"
                        content += f"    {cit.get('url')}\n"
                
                content += "\n"
            
            content += f"\n\nExported from Industry Solutions Directory on {metadata.get('startTime', 'N/A') if metadata else 'N/A'}\n"
        
        return {
            "session_id": session_id,
            "format": format,
            "content": content,
            "filename": f"conversation_{session_id}.{'md' if format.lower() == 'markdown' else 'txt'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting conversation"
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
