"""Configuration settings for the RAG API."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://raguser:ragpassword@localhost:9802/ragdb"

    # Ollama embeddings
    ollama_host: str = "http://172.17.0.1:11434"
    ollama_embed_model: str = "qwen3-embedding:0.6b"
    embedding_dimension: int = 1024

    # Chunking parameters
    chunk_size: int = 1000
    chunk_overlap_ratio: float = 0.1

    # Search defaults
    default_search_limit: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
