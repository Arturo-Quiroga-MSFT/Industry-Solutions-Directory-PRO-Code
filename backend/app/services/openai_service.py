"""
Azure OpenAI service for chat completions and embeddings
Implements the LLM interface for RAG pattern
"""
import logging
from typing import List, Optional
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

from app.config import settings
from app.models.schemas import ChatMessage, MessageRole, Citation

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for Azure OpenAI chat and embeddings"""
    
    def __init__(self):
        """Initialize the Azure OpenAI client"""
        try:
            credential = DefaultAzureCredential()
            self.client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
                azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
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
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if available (limit to max_history_messages)
            if chat_history:
                recent_history = chat_history[-(settings.max_history_messages * 2):]
                for msg in recent_history:
                    if msg.role == MessageRole.USER:
                        messages.append({"role": "user", "content": msg.content})
                    elif msg.role == MessageRole.ASSISTANT:
                        messages.append({"role": "assistant", "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=settings.temperature,
                top_p=settings.top_p
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
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    async def generate_summary(self, prompt: str) -> str:
        """
        Generate a summary using GPT
        
        Args:
            prompt: The prompt containing conversation to summarize
            
        Returns:
            Generated summary text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates clear, concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                top_p=0.95
            )
            
            summary = response.choices[0].message.content
            logger.info(f"Generated summary with {len(summary)} characters")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    async def generate_follow_up_questions(
        self, 
        user_query: str, 
        assistant_response: str, 
        citations: list
    ) -> list[str]:
        """
        Generate contextual follow-up questions based on the conversation
        
        Args:
            user_query: The user's original question
            assistant_response: The assistant's response
            citations: List of Citation objects with solution information
            
        Returns:
            List of 3-4 suggested follow-up questions
        """
        try:
            # Build context about the solutions mentioned
            solutions_context = ""
            if citations:
                solutions_context = "\n\nSolutions mentioned:\n"
                for citation in citations[:3]:  # Limit to top 3
                    solutions_context += f"- {citation.solution_name} by {citation.partner_name}\n"
                    solutions_context += f"  Industries: {', '.join(citation.industries) if citation.industries else 'N/A'}\n"
                    solutions_context += f"  Technologies: {', '.join(citation.technologies) if citation.technologies else 'N/A'}\n"
            
            prompt = f"""Based on this conversation about Microsoft partner solutions, generate 3-4 specific, helpful follow-up questions that would naturally guide the user to explore solutions deeper or ask related queries.

USER QUESTION: {user_query}

ASSISTANT RESPONSE: {assistant_response}
{solutions_context}

REQUIREMENTS:
- Generate exactly 3-4 questions
- Make questions specific to the solutions and context discussed
- Focus on practical next steps (e.g., implementation, costs, integration, use cases)
- Keep questions concise (one sentence each)
- Make questions actionable and valuable
- Vary the question types (details, comparisons, alternatives, specifics)

Return ONLY the questions, one per line, without numbering or bullet points."""

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates insightful follow-up questions to guide users exploring Microsoft partner solutions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher temperature for more creative questions
                top_p=0.9
            )
            
            questions_text = response.choices[0].message.content.strip()
            # Split by newlines and clean up
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            # Ensure we have 3-4 questions
            if len(questions) > 4:
                questions = questions[:4]
            elif len(questions) < 3:
                # Fallback generic questions if generation fails
                questions = [
                    "Can you provide more details about the implementation process?",
                    "What are the pricing models for these solutions?",
                    "How do these solutions integrate with existing systems?"
                ]
            
            logger.info(f"Generated {len(questions)} follow-up questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            # Return generic fallback questions
            return [
                "Can you tell me more about these solutions?",
                "What industries are these solutions best suited for?",
                "Are there similar solutions I should consider?"
            ]

