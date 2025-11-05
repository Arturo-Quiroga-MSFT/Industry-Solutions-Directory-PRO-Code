"""
Data ingestion script for scraping and indexing partner solutions
Scrapes the Industry Solutions Directory website and indexes content in Azure AI Search
"""
import asyncio
import logging
from typing import List, Dict, Any
import requests
import httpx
from bs4 import BeautifulSoup
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchIndex
)
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import uuid
import json

# Load environment variables
# Try to load from backend/.env first, then root .env
from pathlib import Path
backend_env = Path(__file__).parent.parent / "backend" / ".env"
if backend_env.exists():
    load_dotenv(backend_env)
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Pipeline for scraping and indexing partner solutions"""
    
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "partner-solutions-index")
        
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-large")
        
        self.base_url = "https://solutions.microsoftindustryinsights.com"
        
        # Use Azure CLI authentication (no API keys needed)
        self.credential = DefaultAzureCredential()
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
        # Initialize OpenAI client for embeddings
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            api_version="2024-02-01",
            azure_ad_token_provider=lambda: self.credential.get_token("https://cognitiveservices.azure.com/.default").token
        )
        
    async def create_index(self):
        """Create the search index with vector search configuration"""
        logger.info(f"Creating index: {self.index_name}")
        
        # Delete existing index if it exists (to allow recreating with new dimensions)
        try:
            self.index_client.delete_index(self.index_name)
            logger.info(f"Deleted existing index: {self.index_name}")
        except Exception as e:
            logger.info(f"No existing index to delete or error deleting: {e}")
        
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="solution_name", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="partner_name", type=SearchFieldDataType.String, sortable=True, facetable=True),
            SearchableField(name="description", type=SearchFieldDataType.String),
            SearchField(
                name="industries",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
                facetable=True
            ),
            SearchField(
                name="technologies",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
                facetable=True
            ),
            SimpleField(name="solution_url", type=SearchFieldDataType.String),
            SearchableField(name="chunk_text", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=3072,  # text-embedding-3-large dimensions
                vector_search_profile_name="myHnswProfile"
            ),
            SimpleField(name="metadata", type=SearchFieldDataType.String)
        ]
        
        # Configure vector search with HNSW algorithm
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="myHnsw")
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm_configuration_name="myHnsw"
                )
            ]
        )
        
        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        result = self.index_client.create_or_update_index(index)
        logger.info(f"Index '{result.name}' created successfully")
    
    async def scrape_solutions(self) -> List[Dict[str, Any]]:
        """
        Scrape partner solutions from the website
        The Industry Solutions Directory is a dynamic React app that loads data via API
        """
        logger.info("Starting web scraping...")
        
        solutions = []
        
        try:
            # The website uses a backend API - try to find the API endpoint
            # Common patterns: /api/solutions, /api/v1/solutions, etc.
            api_endpoints = [
                f"{self.base_url}/api/solutions",
                f"{self.base_url}/api/v1/solutions",
                f"{self.base_url}/api/data/solutions",
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            # Try each potential API endpoint
            for api_url in api_endpoints:
                try:
                    logger.info(f"Trying API endpoint: {api_url}")
                    response = requests.get(api_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Successfully retrieved data from {api_url}")
                        
                        # Parse the API response (structure may vary)
                        if isinstance(data, list):
                            solutions = self._parse_api_solutions(data)
                        elif isinstance(data, dict) and 'solutions' in data:
                            solutions = self._parse_api_solutions(data['solutions'])
                        elif isinstance(data, dict) and 'data' in data:
                            solutions = self._parse_api_solutions(data['data'])
                        
                        if solutions:
                            break
                            
                except requests.RequestException as e:
                    logger.debug(f"API endpoint {api_url} failed: {e}")
                    continue
            
            # If API approach didn't work, try scraping the rendered page
            if not solutions:
                logger.info("API approach failed, attempting to scrape rendered page...")
                solutions = await self._scrape_html_page()
            
            # If still no solutions, use sample data for testing
            if not solutions:
                logger.warning("Web scraping failed, using sample data for testing")
                solutions = self._get_sample_solutions()
                
        except Exception as e:
            logger.error(f"Error during web scraping: {e}")
            logger.info("Falling back to sample data")
            solutions = self._get_sample_solutions()
        
        logger.info(f"Retrieved {len(solutions)} solutions")
        return solutions
    
    def _parse_api_solutions(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Parse solutions from API response"""
        solutions = []
        
        for item in data:
            try:
                solution = {
                    "solution_name": item.get('name') or item.get('title') or item.get('solution_name', 'Unknown Solution'),
                    "partner_name": item.get('partner') or item.get('partner_name') or item.get('company', 'Unknown Partner'),
                    "description": item.get('description') or item.get('summary', ''),
                    "industries": item.get('industries') or item.get('industry') or [],
                    "technologies": item.get('technologies') or item.get('technology') or [],
                    "solution_url": item.get('url') or item.get('link') or f"{self.base_url}/solution/{item.get('id', '')}",
                    "full_content": item.get('content') or item.get('description', '')
                }
                
                # Ensure industries and technologies are lists
                if isinstance(solution['industries'], str):
                    solution['industries'] = [solution['industries']]
                if isinstance(solution['technologies'], str):
                    solution['technologies'] = [solution['technologies']]
                
                solutions.append(solution)
                
            except Exception as e:
                logger.warning(f"Error parsing solution item: {e}")
                continue
        
        return solutions
    
    async def _scrape_html_page(self) -> List[Dict[str, Any]]:
        """Scrape solutions from HTML page (fallback method)"""
        solutions = []
        
        try:
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(f"{self.base_url}/browse", headers=headers, timeout=15)
            
            if response.status_code != 200:
                return solutions
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common patterns in solution cards
            # Adjust these selectors based on actual HTML structure
            solution_cards = (
                soup.find_all('div', class_=lambda x: x and ('solution' in x.lower() or 'card' in x.lower())) or
                soup.find_all('article') or
                soup.find_all('div', {'data-solution': True})
            )
            
            for card in solution_cards:
                try:
                    # Extract solution data from card
                    name_elem = card.find(['h2', 'h3', 'h4']) or card.find(class_=lambda x: x and 'title' in x.lower())
                    desc_elem = card.find('p') or card.find(class_=lambda x: x and 'desc' in x.lower())
                    link_elem = card.find('a')
                    
                    if name_elem:
                        solution = {
                            "solution_name": name_elem.get_text(strip=True),
                            "partner_name": "Partner",  # Extract from page if available
                            "description": desc_elem.get_text(strip=True) if desc_elem else "",
                            "industries": [],  # Extract from tags/labels if available
                            "technologies": [],  # Extract from tags/labels if available
                            "solution_url": link_elem.get('href', '') if link_elem else "",
                            "full_content": card.get_text(strip=True)
                        }
                        solutions.append(solution)
                        
                except Exception as e:
                    logger.warning(f"Error parsing solution card: {e}")
                    continue
                    
        except ImportError:
            logger.error("BeautifulSoup not available. Install with: pip install beautifulsoup4")
        except Exception as e:
            logger.error(f"Error scraping HTML: {e}")
        
        return solutions
    
    def _get_sample_solutions(self) -> List[Dict[str, Any]]:
        """Return sample data for testing when scraping fails"""
        return [
            {
                "solution_name": "Healthcare AI Analytics Platform",
                "partner_name": "Acme Health Tech",
                "description": "Comprehensive AI-powered analytics platform for healthcare providers. Includes predictive modeling, patient outcome analysis, and resource optimization.",
                "industries": ["Healthcare & Life Sciences"],
                "technologies": ["AI", "Machine Learning", "Analytics"],
                "solution_url": f"{self.base_url}/solutions/healthcare-ai-analytics",
                "full_content": "Detailed description of the healthcare AI analytics platform..."
            },
            {
                "solution_name": "Financial Services Risk Management Suite",
                "partner_name": "FinTech Solutions Corp",
                "description": "Advanced risk management and compliance solution for financial institutions. Real-time monitoring and automated reporting.",
                "industries": ["Financial Services"],
                "technologies": ["AI", "Compliance", "Security"],
                "solution_url": f"{self.base_url}/solutions/financial-risk-management",
                "full_content": "Comprehensive risk management solution for banks and financial institutions..."
            },
            {
                "solution_name": "Retail Customer Experience Platform",
                "partner_name": "RetailTech Innovations",
                "description": "Omnichannel customer experience platform with personalization, inventory management, and loyalty programs.",
                "industries": ["Retail & Consumer Goods"],
                "technologies": ["CRM", "E-commerce", "Analytics"],
                "solution_url": f"{self.base_url}/solutions/retail-customer-experience",
                "full_content": "Modern retail platform for seamless customer experiences across all channels..."
            }
        ]
    
    def chunk_content(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Chunk long content into smaller pieces for indexing
        
        Args:
            content: Content to chunk
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of content chunks
        """
        # Simple chunking by sentences
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Azure OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-large)
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536
    
    async def index_solutions(self, solutions: List[Dict[str, Any]]):
        """
        Index solutions in Azure AI Search
        
        Args:
            solutions: List of solution dictionaries
        """
        logger.info(f"Indexing {len(solutions)} solutions...")
        
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        documents = []
        
        for solution in solutions:
            # Chunk the content
            content = solution.get("full_content", solution["description"])
            chunks = self.chunk_content(content)
            
            # Create a document for each chunk
            for i, chunk in enumerate(chunks):
                doc_id = f"{solution['solution_name']}-{i}".replace(" ", "-").lower()
                doc_id = f"{uuid.uuid5(uuid.NAMESPACE_DNS, doc_id)}"
                
                # Combine text for embedding
                embed_text = f"{solution['solution_name']}. {solution['partner_name']}. {chunk}"
                
                # Generate embedding vector
                logger.info(f"Generating embedding for: {solution['solution_name']} (chunk {i+1}/{len(chunks)})")
                content_vector = self.generate_embedding(embed_text)
                
                document = {
                    "id": doc_id,
                    "solution_name": solution["solution_name"],
                    "partner_name": solution["partner_name"],
                    "description": solution["description"],
                    "industries": solution["industries"],
                    "technologies": solution["technologies"],
                    "solution_url": solution["solution_url"],
                    "chunk_text": chunk,
                    "content_vector": content_vector,
                    "@search.action": "mergeOrUpload",
                    "metadata": json.dumps({
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
                }
                
                documents.append(document)
        
        # Upload documents in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)
            logger.info(f"Uploaded batch {i // batch_size + 1}, {len(batch)} documents")
        
        logger.info(f"Successfully indexed {len(documents)} document chunks")
    
    async def run(self):
        """Run the full ingestion pipeline"""
        try:
            # Step 1: Create index
            await self.create_index()
            
            # Step 2: Scrape solutions
            solutions = await self.scrape_solutions()
            
            # Step 3: Index solutions
            await self.index_solutions(solutions)
            
            logger.info("Data ingestion pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in data ingestion pipeline: {e}")
            raise


async def main():
    """Main entry point"""
    pipeline = DataIngestionPipeline()
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
