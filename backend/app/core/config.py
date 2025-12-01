"""
Application Configuration

This module contains the application settings and configuration.
Settings are loaded from environment variables with sensible defaults.
"""

from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    LLM Provider Options:
    - anthropic: Use Anthropic Claude API
    - openai: Use OpenAI API
    - azure_openai: Use Azure OpenAI Service
    """
    
    # Application
    PROJECT_NAME: str = "AI Meeting Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./meeting_assistant.db"
    DATABASE_ECHO: bool = False  # Set to True to log SQL queries

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # LLM Configuration
    LLM_PROVIDER: str = "azure_openai"  # Options: anthropic, openai, azure_openai
    LLM_MODEL: str = "gpt-4o-dev-aigateway-exception"
    LLM_API_KEY: str = ""
    
    # Azure OpenAI specific settings
    AZURE_OPENAI_ENDPOINT: Optional[str] = "https://dev-adhoc-ai-gateway-exception.openai.azure.com/"
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = "gpt-4o-dev-aigateway-exception"
    
    # LLM Request settings
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT: int = 60  # seconds
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

