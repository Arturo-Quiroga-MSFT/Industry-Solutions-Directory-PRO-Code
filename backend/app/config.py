"""
Configuration settings for the Industry Solutions Chat API
Loads from environment variables with sensible defaults
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "Industry Solutions Chat API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_chat_deployment: str = "gpt-4-1-mini"  # or gpt-4.1, gpt-4o, etc.
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_embedding_dimensions: int = 1536
    
    # Azure AI Search
    azure_search_endpoint: str
    azure_search_api_key: str
    azure_search_index_name: str = "partner-solutions-index"
    
    # Azure Cosmos DB
    azure_cosmos_endpoint: str
    azure_cosmos_key: str
    azure_cosmos_database_name: str = "industry-solutions-db"
    azure_cosmos_container_name: str = "chat-sessions"
    
    # Chat Configuration
    max_history_messages: int = 10
    max_context_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.95
    
    # Search Configuration
    search_top_k: int = 5
    vector_search_threshold: float = 0.7
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    
    # CORS
    cors_origins: list[str] = [
        "https://solutions.microsoftindustryinsights.com",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
