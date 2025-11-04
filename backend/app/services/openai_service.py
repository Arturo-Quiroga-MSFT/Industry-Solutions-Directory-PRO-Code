"""
Azure OpenAI service for chat completions and embeddings
Implements the LLM interface for RAG pattern
"""
import logging
from typing import List, Optional
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential

from app.config import settings
from app.models.schemas import ChatMessage, MessageRole, Citation

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for Azure OpenAI chat and embeddings"""
    
    def __init__(self):
        """Initialize the Azure OpenAI client"""
        try:
            self.client = ChatCompletionsClient(
                endpoint=settings.azure_openai_endpoint,
                credential=AzureKeyCredential(settings.azure_openai_api_key)
            )
            self.chat_model = settings.azure_openai_chat_deployment
            logger.info(f"OpenAI client initialized with model: {self.chat_model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def generate_response(
        self,
        user_message: str,
        context: List[Citation],
        chat_history: Optional[List[ChatMessage]] = None
    ) -> str:
        """
        Generate a response using RAG pattern
        
        Args:
            user_message: User's current message
            context: Retrieved context from search (citations)
            chat_history: Previous conversation messages
            
        Returns:
            AI-generated response
        """
        try:
            # Build the system prompt with RAG context
            system_prompt = self._build_system_prompt(context)
            
            # Build messages list
            messages = [SystemMessage(content=system_prompt)]
            
            # Add chat history if available (limit to max_history_messages)
            if chat_history:
                recent_history = chat_history[-(settings.max_history_messages * 2):]
                for msg in recent_history:
                    if msg.role == MessageRole.USER:
                        messages.append(UserMessage(content=msg.content))
                    elif msg.role == MessageRole.ASSISTANT:
                        messages.append(AssistantMessage(content=msg.content))
            
            # Add current user message
            messages.append(UserMessage(content=user_message))
            
            # Generate response
            response = self.client.complete(
                messages=messages,
                temperature=settings.temperature,
                top_p=settings.top_p,
                model=self.chat_model
            )
            
            generated_text = response.choices[0].message.content
            logger.info(f"Generated response with {len(generated_text)} characters")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _build_system_prompt(self, context: List[Citation]) -> str:
        """
        Build system prompt with RAG context
        
        Args:
            context: Retrieved citations
            
        Returns:
            System prompt string
        """
        base_prompt = """You are an expert assistant for the Microsoft Industry Solutions Directory.
Your role is to help users discover the right partner solutions based on their needs.

INSTRUCTIONS:
- Provide clear, concise, and helpful recommendations
- Always cite your sources using the partner and solution names provided
- If the context doesn't contain relevant information, politely say so and ask clarifying questions
- Focus on matching user needs with solution capabilities
- Highlight the industries and technologies each solution supports
- Be conversational and professional

RESPONSE FORMAT:
1. Start with a brief summary of what you found
2. List relevant solutions with:
   - Solution name and partner
   - Key capabilities
   - Industries/technologies supported
3. Suggest next steps or ask clarifying questions if needed
"""
        
        # Add retrieved context
        if context:
            context_text = "\n\nRELEVANT PARTNER SOLUTIONS:\n"
            for i, citation in enumerate(context, 1):
                context_text += f"\n{i}. **{citation.solution_name}** by {citation.partner_name}\n"
                context_text += f"   Description: {citation.description}\n"
                context_text += f"   URL: {citation.url}\n"
                context_text += f"   Relevance Score: {citation.relevance_score:.2f}\n"
            
            return base_prompt + context_text
        else:
            return base_prompt + "\n\nNo specific solutions were found matching the query. Ask the user for more details about their needs."
    
    async def health_check(self) -> bool:
        """
        Check if OpenAI service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple test completion
            response = self.client.complete(
                messages=[UserMessage(content="test")],
                model=self.chat_model,
                max_tokens=5
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"OpenAI service health check failed: {e}")
            return False
