"""Search router for vector similarity search using LangGraph store."""

from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException

from store import get_store, CHUNKS_NAMESPACE
from models.schemas import SearchRequest, SearchResult, SearchResponse

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search documents using vector similarity.

    Matches the langmem search_memory signature:
    - query: Search query to match against memories
    - limit: Maximum number of results to return (default 10)
    - offset: Number of results to skip (default 0)
    - filter: Additional filter criteria (document_id, level1-6, section_path, etc.)
    """
    store = await get_store()

    # Determine namespace based on filter
    # If document_id is specified, search only that document's chunks
    filter_dict = request.filter or {}
    document_id = filter_dict.pop("document_id", None)

    if document_id:
        namespace = (*CHUNKS_NAMESPACE, document_id)
    else:
        # Search across all chunks
        namespace = CHUNKS_NAMESPACE

    try:
        # Use store's asearch with vector similarity
        results = await store.asearch(
            namespace,
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            filter=filter_dict if filter_dict else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")

    search_results = []
    for item in results:
        chunk_data = item.value
        # Extract document_id from namespace or chunk data
        doc_id = chunk_data.get("document_id", "")
        if not doc_id and len(item.namespace) > 2:
            doc_id = item.namespace[2]  # ("rag", "chunks", doc_id)

        search_results.append(SearchResult(
            chunk_id=item.key,
            document_id=doc_id,
            document_filename=chunk_data.get("filename", "unknown"),
            content=chunk_data.get("text", ""),
            section_path=chunk_data.get("section_path"),
            similarity=0.0,  # Store doesn't return similarity score directly
        ))

    return SearchResponse(
        query=request.query,
        results=search_results,
        total=len(search_results),
    )
