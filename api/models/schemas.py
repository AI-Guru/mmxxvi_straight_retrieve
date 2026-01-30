"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChunkResponse(BaseModel):
    """Response schema for a document chunk."""
    id: str
    document_id: str
    content: str
    level1: str = ""
    level2: str = ""
    level3: str = ""
    level4: str = ""
    level5: str = ""
    level6: str = ""
    section_path: Optional[str] = None
    section_level: Optional[int] = None
    chunk_index: Optional[int] = None
    created_at: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response schema for a document."""
    id: str
    filename: str
    content_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    chunk_count: int = 0


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""
    documents: List[DocumentResponse]
    total: int


class DocumentDetailResponse(BaseModel):
    """Response schema for document details with chunks."""
    document: DocumentResponse
    chunks: List[ChunkResponse]


class SearchRequest(BaseModel):
    """Request schema for vector search (matches langmem search_memory signature)."""
    query: str = Field(..., description="Search query to match against memories")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Additional filter criteria (document_id, level1, section_path, etc.)")


class SearchResult(BaseModel):
    """A single search result."""
    chunk_id: str
    document_id: str
    document_filename: str
    content: str
    section_path: Optional[str] = None
    similarity: float


class SearchResponse(BaseModel):
    """Response schema for vector search."""
    query: str
    results: List[SearchResult]
    total: int


class UploadResponse(BaseModel):
    """Response schema for document upload."""
    status: str
    document_id: str
    filename: str
    chunk_count: int
    message: str


class StatusResponse(BaseModel):
    """Response schema for health check."""
    status: str
    version: str = "1.0.0"
    database: str = "connected"
