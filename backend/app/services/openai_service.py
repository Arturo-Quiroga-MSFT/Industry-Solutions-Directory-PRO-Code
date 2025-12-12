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
            
            # Add chat history if available (limit to 4 recent turns to reduce hallucination risk)
            # Keep history minimal to prevent context bleeding between unrelated topics
            if chat_history:
                recent_history = chat_history[-8:]  # Last 4 turns (4 user + 4 assistant)
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
    
    async def generate_response_stream(
        self,
        user_message: str,
        context: List[Citation],
        chat_history: Optional[List[ChatMessage]] = None
    ):
        """
        Generate a streaming response using RAG pattern
        
        Args:
            user_message: User's current message
            context: Retrieved context from search (citations)
            chat_history: Previous conversation messages
            
        Yields:
            Chunks of AI-generated response
        """
        try:
            # Build the system prompt with RAG context
            system_prompt = self._build_system_prompt(context)
            
            # Build messages list
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if available (limit to 4 recent turns to reduce hallucination risk)
            # Keep history minimal to prevent context bleeding between unrelated topics
            if chat_history:
                recent_history = chat_history[-8:]  # Last 4 turns (4 user + 4 assistant)
                for msg in recent_history:
                    if msg.role == MessageRole.USER:
                        messages.append({"role": "user", "content": msg.content})
                    elif msg.role == MessageRole.ASSISTANT:
                        messages.append({"role": "assistant", "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate streaming response
            stream = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=settings.temperature,
                top_p=settings.top_p,
                stream=True
            )
            
            # Stream the response
            full_response = ""
            for chunk in stream:
                # Check if choices exist and has content
                if chunk.choices and len(chunk.choices) > 0:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content
            
            logger.info(f"Streamed response with {len(full_response)} characters")
            
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
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
Your role is to help users discover the right partner solutions based on ONLY the information provided below.

UNDERSTANDING USER BROWSING PATTERNS:
Users can browse the directory in TWO ways:
1. **By Industry** (e.g., Healthcare, Education, Financial Services, Manufacturing)
2. **By Technology** (e.g., AI Business Solutions, Cloud and AI Platforms, Security)

You MUST be able to handle both types of queries:
- Industry-focused: "What solutions are available for healthcare?"
- Technology-focused: "Show me AI Business Solutions"
- Combined: "What AI solutions are available for financial services?"

CRITICAL ANTI-HALLUCINATION RULES:
⚠️ ONLY recommend solutions that appear in the "RELEVANT PARTNER SOLUTIONS" section below
⚠️ NEVER mention partners, solutions, or companies that are NOT explicitly listed in the retrieved context
⚠️ If the user asks about a topic and NO relevant solutions are found, clearly state "I don't have any relevant partner solutions for that specific topic in the directory" and ask clarifying questions
⚠️ Do NOT use general knowledge about Microsoft partners - ONLY use the solutions explicitly provided
⚠️ When the user changes topics, treat it as a NEW query - do not mix information from previous unrelated conversations
⚠️ If previous conversation topics are unrelated to the current question, ignore them entirely

INSTRUCTIONS:
- Recognize whether the user is browsing by INDUSTRY, by TECHNOLOGY, or by BOTH
- Provide clear, concise, and helpful recommendations based ONLY on the solutions below
- Always cite your sources using the exact partner and solution names from the context
- Be conversational and professional
- If context doesn't match the query, acknowledge it honestly
- When appropriate, mention both the industry focus AND technology capabilities of solutions

RESPONSE FORMAT:
1. Start with a brief summary of what you found
2. List relevant solutions with:
   - Solution name and partner (exactly as shown below)
   - Key capabilities from the description
   - Industries AND technologies supported (mention both when relevant)
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
        Generate contextual follow-up questions by extracting and converting
        the "Next Steps" section from the assistant's response into clickable questions
        
        Args:
            user_query: The user's original question
            assistant_response: The assistant's response
            citations: List of Citation objects with solution information
            
        Returns:
            List of 3-4 suggested follow-up questions based on Next Steps
        """
        try:
            # Try to extract questions from "Next Steps:" section
            import re
            
            # Look for "Next Steps:" section and extract the bullet points
            next_steps_match = re.search(
                r'Next Steps:\s*\n((?:\s*[•\-\*]\s*.+\n?)+)',
                assistant_response,
                re.IGNORECASE | re.MULTILINE
            )
            
            if next_steps_match:
                # Extract the bullet points
                next_steps_text = next_steps_match.group(1)
                # Parse bullet points - remove bullets and clean up
                bullet_pattern = r'^\s*[•\-\*]\s*(.+)$'
                bullets = re.findall(bullet_pattern, next_steps_text, re.MULTILINE)
                
                if bullets:
                    # Convert statements into questions using GPT
                    prompt = f"""Convert these next step statements into natural follow-up questions that a user would ask. Keep them conversational and concise.

STATEMENTS:
{chr(10).join(f"- {b}" for b in bullets)}

REQUIREMENTS:
- Convert each statement into a clear question
- Keep questions under 15 words
- Make them conversational and natural
- Remove any question marks or numbers from the original text
- Return ONLY the questions, one per line, without numbering or bullet points"""

                    response = self.client.chat.completions.create(
                        model=self.chat_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that converts statements into natural follow-up questions."},
                            {"role": "user", "content": prompt}
                        ],
                        top_p=0.9
                    )
                    
                    questions_text = response.choices[0].message.content.strip()
                    questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
                    
                    # Clean up questions - remove any remaining bullets or numbers
                    questions = [re.sub(r'^\d+[\.\)]\s*', '', q) for q in questions]
                    questions = [re.sub(r'^[•\-\*]\s*', '', q) for q in questions]
                    
                    # Limit to 3-4 questions
                    if len(questions) > 4:
                        questions = questions[:4]
                    
                    if len(questions) >= 2:  # At least 2 questions extracted
                        logger.info(f"Extracted {len(questions)} follow-up questions from Next Steps")
                        return questions
            
            # Fallback: Generate questions based on conversation context if no Next Steps found
            logger.info("No Next Steps found, generating contextual questions")
            
            # Build context about the solutions mentioned
            solutions_context = ""
            if citations:
                solutions_context = "\n\nSolutions mentioned:\n"
                for citation in citations[:3]:
                    solutions_context += f"- {citation.solution_name} by {citation.partner_name}\n"
            
            prompt = f"""Based on this conversation, generate 3 specific follow-up questions that would help the user explore the solutions deeper.

USER QUESTION: {user_query}

ASSISTANT RESPONSE (first 500 chars): {assistant_response[:500]}
{solutions_context}

REQUIREMENTS:
- Generate exactly 3 questions
- Make them specific to the solutions mentioned
- Focus on practical aspects (implementation, costs, integration, comparisons)
- Keep under 15 words each
- Return ONLY the questions, one per line, without numbering"""

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates relevant follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                top_p=0.9
            )
            
            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            # Ensure we have 3 questions
            if len(questions) > 3:
                questions = questions[:3]
            elif len(questions) < 3:
                questions = [
                    "Can you tell me more about these solutions?",
                    "What are the implementation requirements?",
                    "How do these compare to other options?"
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

