"""
Azure AI Search service for vector and hybrid search
Implements RAG pattern for retrieving relevant partner solutions
"""
import logging
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
from openai import AzureOpenAI

from app.config import settings
from app.models.schemas import SearchFilter, Citation

logger = logging.getLogger(__name__)


class SearchService:
    """Service for interacting with Azure AI Search"""
    
    def __init__(self):
        """Initialize the search client"""
        try:
            # Use Azure CLI authentication
            credential = DefaultAzureCredential()
            
            self.client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index_name,
                credential=credential
            )
            
            # Initialize OpenAI client for generating embeddings
            self.openai_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
                azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
            )
            
            logger.info(f"Search client initialized for index: {settings.azure_search_index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize search client: {e}")
            raise
    
    async def hybrid_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        top_k: int = None
    ) -> List[Citation]:
        """
        Perform hybrid search (vector + keyword) with optional filters
        
        Args:
            query: User's search query
            filters: Optional filters for industry/technology/partner
            top_k: Number of results to return
            
        Returns:
            List of citations with relevant solutions
        """
        top_k = top_k or settings.search_top_k
        
        try:
            # Build filter expression
            filter_expr = self._build_filter_expression(filters)
            
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            # Create vector query with the embedding
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k * 2,  # Request more for filtering
                fields="content_vector"
            )
            
            # Execute hybrid search
            results = self.client.search(
                search_text=query,  # Keyword search part
                vector_queries=[vector_query],  # Vector search part
                filter=filter_expr,
                select=[
                    "id",
                    "solution_name",
                    "partner_name",
                    "description",
                    "industries",
                    "technologies",
                    "solution_url",
                    "chunk_text"
                ],
                top=top_k,
                include_total_count=True
            )
            
            # Convert results to citations
            citations = []
            for result in results:
                try:
                    citation = Citation(
                        solution_name=result.get("solution_name", "Unknown"),
                        partner_name=result.get("partner_name", "Unknown"),
                        description=result.get("chunk_text", result.get("description", "")),
                        url=result.get("solution_url", ""),
                        relevance_score=result.get("@search.score", 0.0)
                    )
                    citations.append(citation)
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Hybrid search returned {len(citations)} results for query: {query[:50]}...")
            return citations
            
        except AzureError as e:
            logger.error(f"Azure Search error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Azure OpenAI"""
        response = self.openai_client.embeddings.create(
            input=text,
            model=settings.azure_openai_embedding_deployment
        )
        return response.data[0].embedding
    
    async def semantic_hybrid_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        top_k: int = None
    ) -> List[Citation]:
        """
        Perform semantic hybrid search with vector search
        (Note: Semantic reranking requires additional Azure AI Search configuration)
        
        Args:
            query: User's search query
            filters: Optional filters
            top_k: Number of results
            
        Returns:
            List of semantically ranked citations
        """
        top_k = top_k or settings.search_top_k
        
        try:
            filter_expr = self._build_filter_expression(filters)
            
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=50,  # Request more for better results
                fields="content_vector"
            )
            
            # Execute hybrid search (vector + keyword)
            # Note: Semantic ranking config would require index updates
            results = self.client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filter_expr,
                select=[
                    "id",
                    "solution_name",
                    "partner_name",
                    "description",
                    "industries",
                    "technologies",
                    "solution_url",
                    "chunk_text"
                ],
                top=top_k,
                include_total_count=True
            )
            
            citations = []
            for result in results:
                try:
                    # Use search score
                    relevance_score = result.get("@search.score", 0.0)
                    
                    citation = Citation(
                        solution_name=result.get("solution_name", "Unknown"),
                        partner_name=result.get("partner_name", "Unknown"),
                        description=result.get("chunk_text", result.get("description", "")),
                        url=result.get("solution_url", ""),
                        relevance_score=relevance_score
                    )
                    citations.append(citation)
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Semantic search returned {len(citations)} results")
            return citations
            
        except AzureError as e:
            logger.error(f"Azure Search error in semantic search: {e}")
            # Fall back to regular hybrid search
            logger.info("Falling back to regular hybrid search")
            return await self.hybrid_search(query, filters, top_k)
        except Exception as e:
            logger.error(f"Unexpected error during semantic search: {e}")
            raise
    
    def _build_filter_expression(self, filters: Optional[SearchFilter]) -> Optional[str]:
        """
        Build OData filter expression from search filters
        
        Args:
            filters: Search filters
            
        Returns:
            OData filter string or None
        """
        if not filters:
            return None
        
        filter_parts = []
        
        # Filter by industries
        if filters.industries:
            industry_filters = " or ".join([
                f"industries/any(i: i eq '{industry}')"
                for industry in filters.industries
            ])
            filter_parts.append(f"({industry_filters})")
        
        # Filter by technologies
        if filters.technologies:
            tech_filters = " or ".join([
                f"technologies/any(t: t eq '{tech}')"
                for tech in filters.technologies
            ])
            filter_parts.append(f"({tech_filters})")
        
        # Filter by partner name (exact match or contains)
        if filters.partner_name:
            filter_parts.append(f"search.ismatch('{filters.partner_name}', 'partner_name')")
        
        # Combine all filters with AND
        return " and ".join(filter_parts) if filter_parts else None
    
    async def get_facets(self) -> Dict[str, List[str]]:
        """
        Get available facets for industries and technologies
        Useful for UI filter dropdowns
        
        Returns:
            Dictionary with facet values
        """
        try:
            results = self.client.search(
                search_text="*",
                facets=["industries", "technologies", "partner_name"],
                top=0  # We only want facets, not results
            )
            
            facets = {}
            if hasattr(results, 'get_facets'):
                raw_facets = results.get_facets()
                for facet_name, facet_values in raw_facets.items():
                    facets[facet_name] = [fv['value'] for fv in facet_values]
            
            return facets
            
        except Exception as e:
            logger.error(f"Error retrieving facets: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """
        Check if search service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Perform a simple search to verify connectivity
            results = self.client.search(
                search_text="*",
                top=1
            )
            # Try to iterate to trigger actual API call
            next(iter(results), None)
            return True
        except Exception as e:
            logger.error(f"Search service health check failed: {e}")
            return False
