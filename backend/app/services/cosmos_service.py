"""
Azure Cosmos DB service for storing chat sessions and history
Implements conversation persistence and retrieval
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import DefaultAzureCredential

from app.config import settings
from app.models.schemas import ChatMessage, MessageRole

logger = logging.getLogger(__name__)


class CosmosDBService:
    """Service for Cosmos DB operations"""
    
    def __init__(self):
        """Initialize Cosmos DB client"""
        try:
            credential = DefaultAzureCredential()
            self.client = CosmosClient(
                url=settings.azure_cosmos_endpoint,
                credential=credential
            )
            
            # Get or create database
            self.database = self.client.create_database_if_not_exists(
                id=settings.azure_cosmos_database_name
            )
            
            # Get or create container with sessionId as partition key
            self.container = self.database.create_container_if_not_exists(
                id=settings.azure_cosmos_container_name,
                partition_key=PartitionKey(path="/sessionId"),
                offer_throughput=400  # Start with minimal RU/s
            )
            
            logger.info(f"Cosmos DB initialized: {settings.azure_cosmos_database_name}/{settings.azure_cosmos_container_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    async def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new chat session
        
        Args:
            session_id: Optional session ID, generates new one if not provided
            
        Returns:
            Session ID
        """
        session_id = session_id or str(uuid.uuid4())
        
        try:
            session_doc = {
                "id": session_id,
                "sessionId": session_id,
                "messages": [],
                "metadata": {
                    "startTime": datetime.utcnow().isoformat(),
                    "lastActivity": datetime.utcnow().isoformat()
                }
            }
            
            self.container.create_item(body=session_doc)
            logger.info(f"Created new session: {session_id}")
            return session_id
            
        except exceptions.CosmosResourceExistsError:
            # Session already exists
            logger.info(f"Session already exists: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        follow_up_questions: Optional[List[str]] = None
    ) -> str:
        """
        Add a message to a session
        
        Args:
            session_id: Session ID
            role: Message role (user/assistant)
            content: Message content
            citations: Optional citations for assistant messages
            follow_up_questions: Optional follow-up questions for assistant messages
            
        Returns:
            Message ID
        """
        try:
            # Retrieve session
            session = self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            
            # Create message
            message_id = f"msg-{uuid.uuid4()}"
            message = {
                "id": message_id,
                "role": role.value,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "citations": citations or []
            }
            
            # Add follow-up questions if provided (for assistant messages)
            if follow_up_questions:
                message["follow_up_questions"] = follow_up_questions
            
            # Add message to session
            session["messages"].append(message)
            session["metadata"]["lastActivity"] = datetime.utcnow().isoformat()
            
            # Update session
            self.container.replace_item(
                item=session_id,
                body=session
            )
            
            logger.info(f"Added {role.value} message to session {session_id}")
            return message_id
            
        except exceptions.CosmosResourceNotFoundError:
            # Session doesn't exist, create it
            await self.create_session(session_id)
            return await self.add_message(session_id, role, content, citations)
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    async def get_session_history(self, session_id: str) -> List[ChatMessage]:
        """
        Get chat history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of chat messages
        """
        try:
            session = self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            
            messages = []
            for msg in session.get("messages", []):
                messages.append(ChatMessage(
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]),
                    citations=msg.get("citations")
                ))
            
            return messages
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Session not found: {session_id}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving session history: {e}")
            raise
    
    async def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata
        
        Args:
            session_id: Session ID
            
        Returns:
            Session metadata or None if not found
        """
        try:
            session = self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            return session.get("metadata")
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error retrieving session metadata: {e}")
            return None
    
    async def update_session_metadata(
        self,
        session_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session metadata (e.g., industries, technologies of interest)
        
        Args:
            session_id: Session ID
            metadata_updates: Dictionary of metadata fields to update
            
        Returns:
            True if successful
        """
        try:
            session = self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            
            session["metadata"].update(metadata_updates)
            session["metadata"]["lastActivity"] = datetime.utcnow().isoformat()
            
            self.container.replace_item(
                item=session_id,
                body=session
            )
            
            logger.info(f"Updated metadata for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session metadata: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            self.container.delete_item(
                item=session_id,
                partition_key=session_id
            )
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        Check if Cosmos DB is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to read database properties
            self.database.read()
            return True
        except Exception as e:
            logger.error(f"Cosmos DB health check failed: {e}")
            return False
