"""Document ingestion service with hierarchical splitting."""

from typing import List, Dict, Any

from markitdown import MarkItDown
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from config import settings


class IngestionService:
    """Service for document ingestion with hierarchical splitting.

    Note: Embedding is handled by the LangGraph store, not this service.
    """

    def __init__(self):
        # Headers to split on (markdown levels 1-6)
        self.headers_to_split_on = [
            ("#" * level, f"Level_{level}") for level in range(1, 7)
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(self.headers_to_split_on)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=int(settings.chunk_size * settings.chunk_overlap_ratio),
        )
        self.markitdown = MarkItDown(enable_plugins=False)

    def convert_to_markdown(self, file_path: str, content_type: str) -> str:
        """Convert a document to markdown format."""
        if content_type and content_type.startswith("text/markdown"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        # Use markitdown for other formats (PDF, EPUB, DOCX, etc.)
        result = self.markitdown.convert(file_path)
        return result.text_content

    def hierarchical_split(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Split markdown content hierarchically by headers."""
        # First split by markdown headers
        header_splits = self.markdown_splitter.split_text(markdown_content)

        all_chunks = []
        global_chunk_index = 0

        for doc in header_splits:
            # Get hierarchical metadata
            metadata = doc.metadata
            content = doc.page_content

            # Further split by chunk size
            text_chunks = self.text_splitter.split_text(content)

            for chunk_text in text_chunks:
                # Flatten metadata
                flattened = {}
                for level in range(1, 7):
                    key = f"Level_{level}"
                    flattened[f"level{level}"] = metadata.get(key, "")

                # Create section path
                header_parts = [
                    metadata.get(f"Level_{i}", "") for i in range(1, 7)
                ]
                header_parts = [p for p in header_parts if p]
                section_path = " > ".join(header_parts) if header_parts else ""
                section_level = len(header_parts)

                # Use "text" field for the store's embedding
                all_chunks.append({
                    "text": chunk_text,
                    "level1": flattened["level1"],
                    "level2": flattened["level2"],
                    "level3": flattened["level3"],
                    "level4": flattened["level4"],
                    "level5": flattened["level5"],
                    "level6": flattened["level6"],
                    "section_path": section_path,
                    "section_level": section_level,
                    "chunk_index": global_chunk_index,
                })
                global_chunk_index += 1

        return all_chunks

    def flat_split(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Split content by chunk size only (no header-based hierarchy)."""
        text_chunks = self.text_splitter.split_text(markdown_content)

        all_chunks = []
        for chunk_index, chunk_text in enumerate(text_chunks):
            all_chunks.append({
                "text": chunk_text,
                "level1": "",
                "level2": "",
                "level3": "",
                "level4": "",
                "level5": "",
                "level6": "",
                "section_path": "",
                "section_level": 0,
                "chunk_index": chunk_index,
            })

        return all_chunks

    def process_document(
        self, file_path: str, content_type: str, hierarchical: bool = True
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Process a document: convert and split.

        Note: Embedding is handled by the LangGraph store via aput().

        Args:
            file_path: Path to the document file
            content_type: MIME type of the document
            hierarchical: If True, split by markdown headers then chunk size.
                         If False, split only by chunk size.

        Returns:
            Tuple of (markdown_content, list of chunk dictionaries ready for store.aput)
        """
        # Convert to markdown
        markdown_content = self.convert_to_markdown(file_path, content_type)

        # Split based on mode
        if hierarchical:
            chunks_data = self.hierarchical_split(markdown_content)
        else:
            chunks_data = self.flat_split(markdown_content)

        return markdown_content, chunks_data


# Singleton instance
ingestion_service = IngestionService()
