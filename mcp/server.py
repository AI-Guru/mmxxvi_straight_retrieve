"""MCP Server for RAG document search using LangGraph's BaseStore."""

import os
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP
from langgraph.store.postgres import AsyncPostgresStore

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://raguser:ragpassword@localhost:9802/ragdb"
)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://172.17.0.1:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "qwen3-embedding:0.6b")
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))

# Default namespace for RAG documents
DEFAULT_NAMESPACE = ("rag", "chunks")

mcp = FastMCP("RAG Search MCP Server")

# Store instance and context manager (initialized on first use)
_store: Optional[AsyncPostgresStore] = None
_store_cm = None


async def get_store() -> AsyncPostgresStore:
    """Get or create the async store instance."""
    global _store, _store_cm
    if _store is None:
        # Build embed string - add ollama: prefix if not already present
        embed_model = OLLAMA_EMBED_MODEL
        if not embed_model.startswith("ollama:"):
            embed_model = f"ollama:{embed_model}"

        # Create the context manager
        _store_cm = AsyncPostgresStore.from_conn_string(
            DATABASE_URL,
            index={
                "embed": embed_model,
                "dims": EMBEDDING_DIMENSION,
            }
        )
        # Enter the context manager to get the store
        _store = await _store_cm.__aenter__()
        await _store.setup()
    return _store


@mcp.tool
async def search_memory(
    query: str,
    limit: int = 10,
    offset: int = 0,
    filter: Optional[Dict[str, Any]] = None,
    namespace: Optional[List[str]] = None,
) -> dict:
    """
    Search the vector database for documents similar to the query.

    Matches the langmem search_memory signature.

    Args:
        query: Search query to match against memories
        limit: Maximum number of results to return (default 10)
        offset: Number of results to skip (default 0)
        filter: Additional filter criteria
        namespace: Optional namespace list (defaults to ["rag", "chunks"])

    Returns:
        Search results with document chunks and metadata
    """
    store = await get_store()

    ns = tuple(namespace) if namespace else DEFAULT_NAMESPACE

    results = await store.asearch(
        ns,
        query=query,
        limit=limit,
        offset=offset,
        filter=filter,
    )

    # Serialize results
    serialized = []
    for item in results:
        serialized.append({
            "key": item.key,
            "namespace": list(item.namespace),
            "value": item.value,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        })

    return {
        "query": query,
        "results": serialized,
        "total": len(serialized),
    }


@mcp.tool
async def list_namespaces(
    prefix: Optional[List[str]] = None,
    max_depth: int = 3,
) -> dict:
    """
    List available namespaces in the store.

    Args:
        prefix: Optional namespace prefix to filter
        max_depth: Maximum depth of namespaces to return

    Returns:
        List of namespace tuples
    """
    store = await get_store()

    namespaces = await store.alist_namespaces(
        prefix=tuple(prefix) if prefix else None,
        max_depth=max_depth,
    )

    return {
        "namespaces": [list(ns) for ns in namespaces],
        "total": len(namespaces),
    }


@mcp.tool
async def get_item(
    namespace: List[str],
    key: str,
) -> dict:
    """
    Get a specific item from the store.

    Args:
        namespace: The namespace as a list of strings
        key: The item key

    Returns:
        The item value and metadata
    """
    store = await get_store()

    item = await store.aget(
        namespace=tuple(namespace),
        key=key,
    )

    if item is None:
        return {"found": False, "key": key, "namespace": namespace}

    return {
        "found": True,
        "key": item.key,
        "namespace": list(item.namespace),
        "value": item.value,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000, host="0.0.0.0")
