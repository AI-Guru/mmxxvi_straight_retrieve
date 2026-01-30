"""Documents router for database exploration using LangGraph store."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from store import get_store, DOCUMENTS_NAMESPACE, CHUNKS_NAMESPACE
from models.schemas import (
    DocumentResponse,
    DocumentListResponse,
    ChunkResponse,
    DocumentDetailResponse,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List all documents with pagination."""
    store = await get_store()

    # Search documents namespace (no query = list all)
    results = await store.asearch(
        DOCUMENTS_NAMESPACE,
        query=None,
        limit=limit,
        offset=skip,
    )

    documents = []
    for item in results:
        doc_data = item.value
        documents.append(DocumentResponse(
            id=item.key,
            filename=doc_data.get("filename", "unknown"),
            content_type=doc_data.get("content_type"),
            metadata={"hierarchical_split": doc_data.get("hierarchical_split", True)},
            created_at=doc_data.get("created_at"),
            chunk_count=doc_data.get("chunk_count", 0),
        ))

    # Get total count (approximate - search all with high limit)
    all_docs = await store.asearch(DOCUMENTS_NAMESPACE, query=None, limit=10000)
    total = len(all_docs)

    return DocumentListResponse(
        documents=documents,
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str):
    """Get a document by ID with its chunks."""
    store = await get_store()

    # Get document metadata
    doc_item = await store.aget(DOCUMENTS_NAMESPACE, document_id)
    if doc_item is None:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_data = doc_item.value
    document = DocumentResponse(
        id=document_id,
        filename=doc_data.get("filename", "unknown"),
        content_type=doc_data.get("content_type"),
        metadata={"hierarchical_split": doc_data.get("hierarchical_split", True)},
        created_at=doc_data.get("created_at"),
        chunk_count=doc_data.get("chunk_count", 0),
    )

    # Get chunks for this document
    chunk_namespace = (*CHUNKS_NAMESPACE, document_id)
    chunk_results = await store.asearch(
        chunk_namespace,
        query=None,
        limit=1000,
    )

    chunks = []
    for item in chunk_results:
        chunk_data = item.value
        chunks.append(ChunkResponse(
            id=item.key,
            document_id=document_id,
            content=chunk_data.get("text", ""),
            level1=chunk_data.get("level1", ""),
            level2=chunk_data.get("level2", ""),
            level3=chunk_data.get("level3", ""),
            level4=chunk_data.get("level4", ""),
            level5=chunk_data.get("level5", ""),
            level6=chunk_data.get("level6", ""),
            section_path=chunk_data.get("section_path"),
            section_level=chunk_data.get("section_level"),
            chunk_index=chunk_data.get("chunk_index"),
            created_at=item.created_at.isoformat() if item.created_at else None,
        ))

    # Sort by chunk_index
    chunks.sort(key=lambda c: c.chunk_index or 0)

    return DocumentDetailResponse(
        document=document,
        chunks=chunks,
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks."""
    store = await get_store()

    # Check if document exists
    doc_item = await store.aget(DOCUMENTS_NAMESPACE, document_id)
    if doc_item is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete all chunks for this document
    chunk_namespace = (*CHUNKS_NAMESPACE, document_id)
    chunk_results = await store.asearch(chunk_namespace, query=None, limit=10000)
    for item in chunk_results:
        await store.adelete(chunk_namespace, item.key)

    # Delete document metadata
    await store.adelete(DOCUMENTS_NAMESPACE, document_id)

    return {"status": "success", "message": f"Document {document_id} deleted"}


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get chunks for a specific document."""
    store = await get_store()

    # Verify document exists
    doc_item = await store.aget(DOCUMENTS_NAMESPACE, document_id)
    if doc_item is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks
    chunk_namespace = (*CHUNKS_NAMESPACE, document_id)
    chunk_results = await store.asearch(
        chunk_namespace,
        query=None,
        limit=limit,
        offset=skip,
    )

    chunks = []
    for item in chunk_results:
        chunk_data = item.value
        chunks.append(ChunkResponse(
            id=item.key,
            document_id=document_id,
            content=chunk_data.get("text", ""),
            level1=chunk_data.get("level1", ""),
            level2=chunk_data.get("level2", ""),
            level3=chunk_data.get("level3", ""),
            level4=chunk_data.get("level4", ""),
            level5=chunk_data.get("level5", ""),
            level6=chunk_data.get("level6", ""),
            section_path=chunk_data.get("section_path"),
            section_level=chunk_data.get("section_level"),
            chunk_index=chunk_data.get("chunk_index"),
            created_at=item.created_at.isoformat() if item.created_at else None,
        ))

    # Sort by chunk_index
    chunks.sort(key=lambda c: c.chunk_index or 0)

    return chunks
