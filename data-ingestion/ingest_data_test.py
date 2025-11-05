"""
Quick test script for ingesting a small subset of partner solutions
Only processes 2 industries and limits solutions per industry for fast testing
"""
import asyncio
import logging
from typing import List, Dict, Any
import requests
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

# Load environment variables
from pathlib import Path
backend_env = Path(__file__).parent.parent / "backend" / ".env"
if backend_env.exists():
    load_dotenv(backend_env)
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TEST CONFIGURATION
MAX_INDUSTRIES = 2  # Only process first 2 industries
MAX_SOLUTIONS_PER_THEME = 5  # Only process first 5 solutions per theme


class DataIngestionPipeline:
    """Pipeline for scraping and indexing partner solutions - TEST VERSION"""
    
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "partner-solutions-index")
        
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-large")
        
        self.api_base_url = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
        
        # Use Azure CLI authentication
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
        
        # Delete existing index if it exists
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
        """Scrape partner solutions from the API - TESTING LIMITED SET"""
        logger.info("Starting API data collection (TEST MODE - LIMITED DATA)...")
        
        solutions = []
        
        try:
            # Get menu structure with all industries and themes
            menu_url = f"{self.api_base_url}/getMenu"
            logger.info(f"Fetching menu from: {menu_url}")
            
            response = requests.get(menu_url, timeout=30)
            response.raise_for_status()
            menu_data = response.json()
            
            logger.info(f"Found {len(menu_data)} total industries")
            
            # Process only first MAX_INDUSTRIES industries
            for industry in menu_data[:MAX_INDUSTRIES]:
                industry_name = industry.get('industryName', 'Unknown')
                logger.info(f"\nProcessing industry: {industry_name}")
                
                sub_industries = industry.get('subIndustries', [])
                logger.info(f"  Found {len(sub_industries)} sub-industries")
                
                for sub_industry in sub_industries:
                    theme_slug = sub_industry.get('industryThemeSlug')
                    sub_industry_name = sub_industry.get('subIndustryName', 'Unknown')
                    
                    if not theme_slug:
                        continue
                    
                    logger.info(f"  Fetching solutions for: {sub_industry_name}")
                    
                    # Get partner solutions for this theme
                    theme_url = f"{self.api_base_url}/GetThemeDetalsByViewId"
                    params = {'slug': theme_slug}
                    
                    try:
                        theme_response = requests.get(theme_url, params=params, timeout=30)
                        theme_response.raise_for_status()
                        theme_data = theme_response.json()
                        
                        # Extract solutions from themeSolutionAreas
                        theme_solutions = self._parse_theme_solutions(
                            theme_data, 
                            industry_name, 
                            sub_industry_name
                        )
                        
                        # LIMIT solutions per theme for testing
                        theme_solutions_limited = theme_solutions[:MAX_SOLUTIONS_PER_THEME]
                        logger.info(f"    Retrieved {len(theme_solutions_limited)} solutions (limited from {len(theme_solutions)} total)")
                        solutions.extend(theme_solutions_limited)
                        
                    except Exception as e:
                        logger.warning(f"    Error fetching theme details: {e}")
                        continue
            
            logger.info(f"\nTotal solutions collected: {len(solutions)}")
            
        except Exception as e:
            logger.error(f"Error during API data collection: {e}")
            raise
        
        return solutions
    
    def _parse_theme_solutions(
        self, 
        theme_data: Dict[str, Any], 
        industry_name: str,
        sub_industry_name: str
    ) -> List[Dict[str, Any]]:
        """Parse solutions from GetThemeDetalsByViewId response"""
        solutions = []
        
        # Get solutions from themeSolutionAreas
        theme_solution_areas = theme_data.get('themeSolutionAreas', [])
        
        for area in theme_solution_areas:
            area_name = area.get('solutionAreaName', 'Unknown')
            partner_solutions = area.get('partnerSolutions', [])
            
            for ps in partner_solutions:
                solution = {
                    'solution_name': ps.get('solutionName', 'Unknown Solution'),
                    'partner_name': ps.get('orgName', 'Unknown Partner'),
                    'description': ps.get('solutionDescription', ''),
                    'industry': industry_name,
                    'sub_industry': sub_industry_name,
                    'solution_area': area_name,
                    'solution_url': f"https://solutions.microsoftindustryinsights.com/solutiondetails/{ps.get('partnerSolutionSlug', '')}",
                    'logo_url': ps.get('logoFileLink', ''),
                    'partner_id': ps.get('partnerId', ''),
                    'solution_id': ps.get('partnerSolutionId', str(uuid.uuid4()))
                }
                solutions.append(solution)
        
        return solutions
    
    async def index_solutions(self, solutions: List[Dict[str, Any]]):
        """Index solutions with embeddings in Azure AI Search"""
        if not solutions:
            logger.warning("No solutions to index")
            return
        
        logger.info(f"Indexing {len(solutions)} solutions...")
        
        # Create search client
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        documents = []
        for solution in solutions:
            # Chunk the content
            chunks = self._chunk_text(solution)
            
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"Generating embedding for: {solution['solution_name']} (chunk {i}/{len(chunks)})")
                
                # Generate embedding
                embedding = self._generate_embedding(chunk)
                
                # Create document
                doc = {
                    'id': f"{solution['solution_id']}_chunk{i}",
                    'solution_name': solution['solution_name'],
                    'partner_name': solution['partner_name'],
                    'description': solution['description'],
                    'industries': [solution['industry'], solution['sub_industry']],
                    'technologies': [solution['solution_area']],
                    'solution_url': solution['solution_url'],
                    'chunk_text': chunk,
                    'content_vector': embedding,
                    'metadata': f"Industry: {solution['industry']}, Sub-Industry: {solution['sub_industry']}, Area: {solution['solution_area']}"
                }
                documents.append(doc)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)
            logger.info(f"Uploaded batch {i//batch_size + 1}, {len(batch)} documents")
        
        logger.info(f"Successfully indexed {len(documents)} document chunks")
    
    def _chunk_text(self, solution: Dict[str, Any], chunk_size: int = 1000) -> List[str]:
        """Split solution text into chunks"""
        full_text = f"{solution['solution_name']}\n\n{solution['description']}"
        
        if len(full_text) <= chunk_size:
            return [full_text]
        
        chunks = []
        words = full_text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Azure OpenAI"""
        response = self.openai_client.embeddings.create(
            input=text,
            model=self.embedding_deployment
        )
        return response.data[0].embedding
    
    async def run(self):
        """Run the complete pipeline"""
        try:
            # Create index
            await self.create_index()
            
            # Scrape solutions
            solutions = await self.scrape_solutions()
            
            # Index solutions
            await self.index_solutions(solutions)
            
            logger.info("Data ingestion pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in data ingestion pipeline: {e}")
            raise


async def main():
    pipeline = DataIngestionPipeline()
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
