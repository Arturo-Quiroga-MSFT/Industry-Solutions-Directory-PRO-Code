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
        Scrape partner solutions from the website using the discovered API
        API structure: Get menu → Get theme details with solutions
        """
        logger.info("Starting web scraping from Industry Solutions Directory API...")
        
        solutions = []
        api_base = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        try:
            # Step 1: Get the menu with all industries and themes
            logger.info("Fetching industry menu...")
            menu_response = requests.get(f"{api_base}/getMenu", headers=headers, timeout=30)
            
            if menu_response.status_code != 200:
                raise Exception(f"Failed to fetch menu: {menu_response.status_code}")
            
            menu_data = menu_response.json()
            logger.info(f"Found {len(menu_data)} industries in menu")
            
            # Step 2: For each industry theme, get the partner solutions
            for industry in menu_data:
                industry_name = industry.get('industryName', 'Unknown')
                logger.info(f"Processing industry: {industry_name}")
                
                for sub_industry in industry.get('subIndustries', []):
                    theme_slug = sub_industry.get('industryThemeSlug')
                    sub_industry_name = sub_industry.get('subIndustryName', 'Unknown')
                    
                    if not theme_slug:
                        logger.debug(f"Skipping {sub_industry_name} - no theme slug")
                        continue
                    
                    logger.info(f"  Fetching solutions for: {sub_industry_name}")
                    
                    try:
                        # Get theme details with partner solutions
                        theme_response = requests.get(
                            f"{api_base}/GetThemeDetalsByViewId",
                            params={'slug': theme_slug},
                            headers=headers,
                            timeout=30
                        )
                        
                        if theme_response.status_code == 200:
                            theme_data = theme_response.json()
                            
                            # Solutions are nested in themeSolutionAreas
                            theme_solution_areas = theme_data.get('themeSolutionAreas', [])
                            solution_count = 0
                            
                            for area in theme_solution_areas:
                                area_name = area.get('solutionAreaName', 'Unknown Area')
                                partner_solutions = area.get('partnerSolutions', [])
                                
                                for ps in partner_solutions:
                                    solutions.append(self._parse_partner_solution(
                                        ps, industry_name, sub_industry_name, area_name
                                    ))
                                    solution_count += 1
                            
                            # Also get spotlight solutions
                            spotlight_solutions = theme_data.get('spotLightPartnerSolutions', [])
                            for ps in spotlight_solutions:
                                solutions.append(self._parse_partner_solution(
                                    ps, industry_name, sub_industry_name, "Spotlight"
                                ))
                                solution_count += 1
                            
                            logger.info(f"    Found {solution_count} solutions")
                        else:
                            logger.warning(f"    Failed to fetch theme {theme_slug}: {theme_response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"    Error fetching theme {theme_slug}: {e}")
                        continue
            
            if not solutions:
                logger.warning("No solutions found from API, using sample data")
                solutions = self._get_sample_solutions()
                
        except Exception as e:
            logger.error(f"Error during API scraping: {e}")
            logger.info("Falling back to sample data")
            solutions = self._get_sample_solutions()
        
        logger.info(f"Retrieved {len(solutions)} total solutions")
        return solutions
    
    def _parse_partner_solution(self, ps_data: Dict, industry: str, sub_industry: str, solution_area: str = "") -> Dict[str, Any]:
        """Parse a partner solution from the API response"""
        technologies = [solution_area] if solution_area else []
        
        return {
            "solution_name": ps_data.get('solutionName', 'Unknown Solution'),
            "partner_name": ps_data.get('orgName', 'Unknown Partner'),
            "description": ps_data.get('solutionDescription', ''),
            "industries": [industry, sub_industry],
            "technologies": technologies,
            "solution_url": f"{self.base_url}/solution/{ps_data.get('partnerSolutionSlug', '')}",
            "full_content": ps_data.get('solutionDescription', ''),
            "logo_url": ps_data.get('logoFileLink', ''),
            "partner_solution_id": ps_data.get('partnerSolutionId', '')
        }
    
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
