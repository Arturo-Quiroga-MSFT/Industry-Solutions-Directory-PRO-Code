"""
Configuration for SQL-to-Azure AI Search ingestion pipeline.
Reads solutions directly from the ISD SQL database and indexes them
into Azure AI Search with vector embeddings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Azure AI Search ──────────────────────────────────────────────────────────
SEARCH_ENDPOINT = os.getenv(
    "AZURE_SEARCH_ENDPOINT",
    "https://aq-mysearch001.search.windows.net",
)
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")  # leave empty to use DefaultAzureCredential
INDEX_NAME = "isd-solutions-v1"

# ── Azure OpenAI ─────────────────────────────────────────────────────────────
OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://r2d2-foundry-001.openai.azure.com/",
)
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
EMBEDDING_DEPLOYMENT = "text-embedding-3-large"
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072

# ── SQL Database ─────────────────────────────────────────────────────────────
SQL_SERVER = os.getenv("SQL_SERVER", "mssoldir-prd-sql.database.windows.net")
SQL_DATABASE = os.getenv("SQL_DATABASE", "mssoldir-prd")
SQL_USERNAME = os.getenv("SQL_USERNAME", "isdapi")
SQL_PASSWORD = os.getenv("SQL_PASSWORD", "")
SQL_VIEW = "dbo.vw_ISDSolution_All"

# ── Ingestion settings ───────────────────────────────────────────────────────
BATCH_SIZE = 100          # documents per upload batch
EMBEDDING_BATCH_SIZE = 16  # texts per embedding API call
