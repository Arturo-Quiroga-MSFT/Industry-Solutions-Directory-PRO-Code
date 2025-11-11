"""
Azure AI Search service for vector and hybrid search
Implements RAG pattern for retrieving relevant partner solutions
"""
import logging
import httpx
from typing import List, Dict, Any, Optional
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError

from app.config import settings
from app.models.schemas import SearchFilter, Citation

logger = logging.getLogger(__name__)


class SearchService:
    """Service for interacting with Azure AI Search via REST API"""
    
    def __init__(self):
        """Initialize the search service with REST API"""
        try:
            # Use Azure CLI authentication
            self.credential = DefaultAzureCredential()
            self.endpoint = settings.azure_search_endpoint.rstrip('/')
            self.index_name = settings.azure_search_index_name
            self.api_version = "2024-07-01"  # API version that supports integrated vectorization
            
            # Get access token for Azure Search
            self._get_access_token()
            
            logger.info(f"Search service initialized for index: {self.index_name}")
            logger.info(f"Using REST API version: {self.api_version}")
            logger.info("Using integrated vectorization - queries auto-vectorized by Azure Search")
        except Exception as e:
            logger.error(f"Failed to initialize search service: {e}")
            raise
    
    def _get_access_token(self) -> str:
        """Get Azure Search access token"""
        token = self.credential.get_token("https://search.azure.com/.default")
        return token.token
    
    async def hybrid_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        top_k: int = None
    ) -> List[Citation]:
        """
        Perform hybrid search (vector + keyword) with optional filters using REST API
        
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
            
            # Build REST API request body with integrated vectorization
            request_body = {
                "search": query,  # Keyword search part
                "vectorQueries": [
                    {
                        "kind": "text",  # Use integrated vectorization
                        "text": query,  # Azure Search will auto-vectorize this
                        "fields": "content_vector",
                        "k": top_k * 2  # Request more for filtering
                    }
                ],
                "select": "id,solution_name,partner_name,description,industries,technologies,solution_url,chunk_text",
                "top": top_k,
                "count": True
            }
            
            if filter_expr:
                request_body["filter"] = filter_expr
            
            # Call Azure Search REST API
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            token = self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                if not response.is_success:
                    error_detail = response.text
                    logger.error(f"Azure Search API error: {response.status_code} - {error_detail}")
                response.raise_for_status()
                results = response.json()
            
            # Convert results to citations
            citations = []
            for result in results.get("value", []):
                try:
                    solution_name = result.get("solution_name", "Unknown")
                    # Create search URL instead of direct link due to website redirect issues
                    search_url = f"https://solutions.microsoftindustryinsights.com/?search={solution_name.replace(' ', '%20')}"
                    
                    # Use chunk_text if available, otherwise fall back to description
                    description_text = result.get("chunk_text") or result.get("description") or ""
                    
                    citation = Citation(
                        solution_name=solution_name,
                        partner_name=result.get("partner_name", "Unknown"),
                        description=description_text,
                        url=search_url,
                        relevance_score=result.get("@search.score", 0.0)
                    )
                    citations.append(citation)
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Hybrid search returned {len(citations)} results for query: {query[:50]}...")
            return citations
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Azure Search error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise
    
    async def semantic_hybrid_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        top_k: int = None
    ) -> List[Citation]:
        """
        Perform semantic hybrid search with vector search using REST API
        Includes L2 semantic reranking for improved relevance
        
        Args:
            query: User's search query
            filters: Optional filters
            top_k: Number of results
            
        Returns:
            List of semantically ranked citations
        """
        top_k = top_k or settings.search_top_k
        
        try:
            # Build filter expression
            filter_expr = self._build_filter_expression(filters)
            
            # Build REST API request body with semantic search + vector search
            request_body = {
                "search": query,
                "vectorQueries": [
                    {
                        "kind": "text",
                        "text": query,
                        "fields": "content_vector",
                        "k": top_k * 2
                    }
                ],
                "queryType": "semantic",
                "semanticConfiguration": "default",
                "captions": "extractive",
                "answers": "extractive|count-3",
                "select": "id,solution_name,partner_name,description,industries,technologies,solution_url,chunk_text",
                "top": top_k,
                "count": True
            }
            
            if filter_expr:
                request_body["filter"] = filter_expr
            
            # Call Azure Search REST API
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            token = self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                if not response.is_success:
                    # Fall back to regular hybrid if semantic fails (e.g., not configured)
                    logger.warning(f"Semantic search failed ({response.status_code}), falling back to hybrid")
                    return await self.hybrid_search(query, filters, top_k)
                
                results = response.json()
            
            # Convert results to citations
            citations = []
            for result in results.get("value", []):
                try:
                    solution_name = result.get("solution_name", "Unknown")
                    search_url = f"https://solutions.microsoftindustryinsights.com/?search={solution_name.replace(' ', '%20')}"
                    
                    # Use semantic caption if available, otherwise fall back to chunk_text/description
                    description_text = ""
                    captions = result.get("@search.captions")
                    if captions and len(captions) > 0:
                        description_text = captions[0].get("text", "")
                    
                    if not description_text:
                        description_text = result.get("chunk_text") or result.get("description") or ""
                    
                    # Use reranker score if available, otherwise fall back to regular score
                    score = result.get("@search.rerankerScore") or result.get("@search.score", 0.0)
                    
                    citation = Citation(
                        solution_name=solution_name,
                        partner_name=result.get("partner_name", "Unknown"),
                        description=description_text,
                        url=search_url,
                        relevance_score=score
                    )
                    citations.append(citation)
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Semantic hybrid search returned {len(citations)} results for query: {query[:50]}...")
            return citations
            
        except Exception as e:
            logger.error(f"Unexpected error during semantic search: {e}")
            # Fall back to regular hybrid search
            return await self.hybrid_search(query, filters, top_k)
    
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
        
        # Filter by industries (string field, not collection)
        if filters.industries:
            industry_filters = " or ".join([
                f"search.ismatch('{industry}', 'industries')"
                for industry in filters.industries
            ])
            filter_parts.append(f"({industry_filters})")
        
        # Filter by technologies (string field, not collection)
        if filters.technologies:
            tech_filters = " or ".join([
                f"search.ismatch('{tech}', 'technologies')"
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
        Get available facets for industries and technologies using REST API
        Useful for UI filter dropdowns
        
        Returns:
            Dictionary with facet values
        """
        try:
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            token = self._get_access_token()
            
            request_body = {
                "search": "*",
                "facets": ["industries", "technologies", "partner_name"],
                "top": 0  # We only want facets, not results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                results = response.json()
            
            facets = {}
            for facet_name, facet_values in results.get("@search.facets", {}).items():
                facets[facet_name] = [fv['value'] for fv in facet_values]
            
            return facets
            
        except Exception as e:
            logger.error(f"Error retrieving facets: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """
        Check if search service is healthy using REST API
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Perform a simple search to verify connectivity
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
            token = self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"search": "*", "top": 1},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Search service health check failed: {e}")
            return False
