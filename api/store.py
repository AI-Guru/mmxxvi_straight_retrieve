"""LangGraph store setup for RAG API."""

import os
from typing import Optional
from contextlib import asynccontextmanager

from langgraph.store.postgres import AsyncPostgresStore

from config import settings

# Namespaces
DOCUMENTS_NAMESPACE = ("rag", "documents")
CHUNKS_NAMESPACE = ("rag", "chunks")

# Store instance and context manager (initialized on first use)
_store: Optional[AsyncPostgresStore] = None
_store_cm = None


async def get_store() -> AsyncPostgresStore:
    """Get or create the async store instance."""
    global _store, _store_cm
    if _store is None:
        # Convert asyncpg URL to psycopg format if needed
        db_url = settings.database_url
        if "+asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")

        # Build embed string - add ollama: prefix if not already present
        embed_model = settings.ollama_embed_model
        if not embed_model.startswith("ollama:"):
            embed_model = f"ollama:{embed_model}"

        # Create the context manager
        _store_cm = AsyncPostgresStore.from_conn_string(
            db_url,
            index={
                "embed": embed_model,
                "dims": settings.embedding_dimension,
            }
        )
        # Enter the context manager to get the store
        _store = await _store_cm.__aenter__()
        await _store.setup()
    return _store


async def close_store():
    """Close the store connection."""
    global _store, _store_cm
    if _store is not None and _store_cm is not None:
        await _store_cm.__aexit__(None, None, None)
        _store = None
        _store_cm = None
