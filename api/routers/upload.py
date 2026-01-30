"""Upload router for document ingestion using LangGraph store."""

import asyncio
import hashlib
import os
import tempfile
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from store import get_store, DOCUMENTS_NAMESPACE, CHUNKS_NAMESPACE
from models.schemas import UploadResponse
from services.ingestion import ingestion_service

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    hierarchical_split: bool = Form(default=True, description="Enable hierarchical splitting by markdown headers"),
):
    """
    Upload a document for processing and embedding.

    Supports PDF, EPUB, DOCX, Markdown, and other text formats.
    Documents are converted to markdown, split into chunks (optionally hierarchically),
    and stored in the LangGraph store (embedding handled automatically).

    Args:
        file: The document file to upload
        hierarchical_split: If True, split by markdown headers then by chunk size.
                           If False, split only by chunk size (flat splitting).
    """
    # Save uploaded file temporarily
    suffix = os.path.splitext(file.filename)[1] if file.filename else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        store = await get_store()

        # Process document (convert + split, no embedding)
        markdown_content, chunks_data = ingestion_service.process_document(
            tmp_path,
            file.content_type,
            hierarchical=hierarchical_split,
        )

        # Generate document ID from content hash (prevents duplicates)
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        doc_id = f"{content_hash}"

        # Check if document already exists and delete old chunks
        existing_doc = await store.aget(DOCUMENTS_NAMESPACE, doc_id)
        if existing_doc:
            # Delete old chunks before re-uploading
            old_chunk_namespace = (*CHUNKS_NAMESPACE, doc_id)
            old_chunks = await store.asearch(old_chunk_namespace, query=None, limit=10000)
            for chunk in old_chunks:
                await store.adelete(old_chunk_namespace, chunk.key)

        # Store document metadata (index=False, no embedding needed)
        doc_metadata = {
            "filename": file.filename or "unknown",
            "content_type": file.content_type,
            "hierarchical_split": hierarchical_split,
            "chunk_count": len(chunks_data),
            "created_at": datetime.utcnow().isoformat(),
        }
        await store.aput(
            DOCUMENTS_NAMESPACE,
            doc_id,
            doc_metadata,
            index=False,
        )

        # Store each chunk with embedding in parallel (index=True by default)
        # Uses namespace per document for organization
        chunk_namespace = (*CHUNKS_NAMESPACE, doc_id)
        filename = file.filename or "unknown"

        async def store_chunk(chunk_data: dict) -> None:
            chunk_key = f"chunk_{chunk_data['chunk_index']}"
            chunk_data["document_id"] = doc_id
            chunk_data["filename"] = filename
            await store.aput(chunk_namespace, chunk_key, chunk_data)

        await asyncio.gather(*[store_chunk(chunk) for chunk in chunks_data])

        action = "updated" if existing_doc else "uploaded"
        return UploadResponse(
            status="success",
            document_id=doc_id,
            filename=file.filename or "unknown",
            chunk_count=len(chunks_data),
            message=f"Document {action} and processed into {len(chunks_data)} chunks",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
