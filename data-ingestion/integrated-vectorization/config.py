"""
Configuration for integrated vectorization setup.
"""
import os

# Azure AI Search
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://indsolse-dev-srch-okumlm.search.windows.net")
INDEX_NAME = "partner-solutions-integrated"

# Azure OpenAI
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://indsolse-dev-ai-okumlm.openai.azure.com/")
OPENAI_API_VERSION = "2024-02-01"
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072

# Azure Blob Storage
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "aqstorage009876")
STORAGE_CONTAINER_NAME = "industry-solutions-data"
STORAGE_ACCOUNT_URL = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"

# Data Source
DATA_SOURCE_NAME = "industry-solutions-datasource"

# Skillset
SKILLSET_NAME = "industry-solutions-skillset"

# Indexer
INDEXER_NAME = "industry-solutions-indexer"

# Chunking Configuration
CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 200  # overlap between chunks

# ISD API Configuration
ISD_API_BASE = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
