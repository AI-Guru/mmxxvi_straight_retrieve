"""Routers package for RAG API."""

from .upload import router as upload_router
from .documents import router as documents_router
from .search import router as search_router

__all__ = ["upload_router", "documents_router", "search_router"]
