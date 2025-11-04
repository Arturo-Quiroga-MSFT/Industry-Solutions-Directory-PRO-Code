"""
Data ingestion script for scraping and indexing partner solutions
Scrapes the Industry Solutions Directory website and indexes content in Azure AI Search
"""
import asyncio
import logging
from typing import List, Dict, Any
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
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndex
)
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import EmbeddingsClient
from azure.ai.inference.models import EmbeddingInput
import os
from dotenv import load_dotenv
import uuid
import json

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Pipeline for scraping and indexing partner solutions"""
    
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "partner-solutions-index")
        
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.openai_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        self.base_url = "https://solutions.microsoftindustryinsights.com"
        
        self.credential = AzureKeyCredential(self.search_key)
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
    async def create_index(self):
        """Create the search index with vector search configuration"""
        logger.info(f"Creating index: {self.index_name}")
        
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
                vector_search_dimensions=1536,  # text-embedding-3-large dimensions
                vector_search_profile_name="myHnswProfile"
            ),
            SimpleField(name="metadata", type=SearchFieldDataType.String)
        ]
        
        # Configure vector search with HNSW algorithm and Azure OpenAI vectorizer
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="myHnsw")
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm_configuration_name="myHnsw",
                    vectorizer_name="myOpenAI"
                )
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    vectorizer_name="myOpenAI",
                    kind="azureOpenAI",
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=self.openai_endpoint,
                        deployment_name=self.embedding_deployment,
                        model_name=self.embedding_deployment
                    )
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
        This is a placeholder - actual implementation will depend on website structure
        """
        logger.info("Starting web scraping...")
        
        # TODO: Implement actual web scraping based on website structure
        # For now, return sample data
        
        sample_solutions = [
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
        
        logger.info(f"Scraped {len(sample_solutions)} solutions")
        return sample_solutions
    
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
                
                document = {
                    "id": doc_id,
                    "solution_name": solution["solution_name"],
                    "partner_name": solution["partner_name"],
                    "description": solution["description"],
                    "industries": solution["industries"],
                    "technologies": solution["technologies"],
                    "solution_url": solution["solution_url"],
                    "chunk_text": chunk,
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
