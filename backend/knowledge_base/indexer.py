"""Knowledge Base Indexer - orchestrates the full indexing pipeline."""

import logging
import time
from typing import Any

from .processor import EditorialProcessor
from .scraper import EditorialDataLoader

logger = logging.getLogger(__name__)


class KnowledgeBaseIndexer:
    """Orchestrates the knowledge base indexing pipeline.

    Pipeline steps:
    1. Load documents from source (sample JSON or scraped data)
    2. Process documents into chunks
    3. Generate embeddings and index into ChromaDB
    """

    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 100,
        batch_size: int = 50,
    ):
        """Initialize the indexer.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between consecutive chunks
            batch_size: Batch size for vector store operations
        """
        self.processor = EditorialProcessor(
            max_chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.loader = EditorialDataLoader()
        self.batch_size = batch_size

    def run(
        self,
        source: str = "sample",
        force: bool = False,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Run the full indexing pipeline.

        Args:
            source: Data source ("sample", "scraped", or "all")
            force: Force re-indexing even if data exists
            batch_size: Override default batch size

        Returns:
            Dictionary with indexing statistics
        """
        from rag.vectorstore import get_vectorstore

        start_time = time.time()
        batch_size = batch_size or self.batch_size

        stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "chunks_indexed": 0,
            "errors": 0,
            "elapsed_seconds": 0,
        }

        vectorstore = get_vectorstore()

        # Check if already indexed
        if not force and vectorstore.get_count() > 0:
            logger.info(
                f"Vector store already contains {vectorstore.get_count()} documents. "
                "Use --force to re-index."
            )
            stats["chunks_indexed"] = vectorstore.get_count()
            return stats

        # Reset if forcing
        if force and vectorstore.get_count() > 0:
            logger.info("Force re-indexing: resetting vector store")
            vectorstore.reset()

        # Step 1: Load documents
        logger.info(f"Loading documents from source: {source}")
        editorials = self._load_documents(source)
        stats["documents_processed"] = len(editorials)

        if not editorials:
            logger.warning("No documents loaded. Nothing to index.")
            return stats

        # Step 2: Process into chunks
        logger.info(f"Processing {len(editorials)} editorials into chunks")
        chunks = self.processor.process_batch(editorials)
        stats["chunks_created"] = len(chunks)

        if not chunks:
            logger.warning("No chunks created from documents.")
            return stats

        # Step 3: Index into vector store
        logger.info(f"Indexing {len(chunks)} chunks into vector store")
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [f"editorial_{i}" for i in range(len(chunks))]

        try:
            indexed = vectorstore.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                batch_size=batch_size,
            )
            stats["chunks_indexed"] = indexed
        except Exception as e:
            logger.error(f"Indexing failed: {e}", exc_info=True)
            stats["errors"] += 1

        stats["elapsed_seconds"] = round(time.time() - start_time, 2)
        logger.info(
            f"Indexing complete: {stats['chunks_indexed']}/{stats['chunks_created']} "
            f"chunks in {stats['elapsed_seconds']}s"
        )
        return stats

    def _load_documents(self, source: str):
        """Load documents based on specified source.

        Args:
            source: Source identifier

        Returns:
            List of Editorial objects
        """
        if source == "sample":
            return self.loader.load_sample_editorials()
        elif source == "scraped":
            # Placeholder for scraped data
            logger.info("Scraped source not yet implemented, falling back to sample")
            return self.loader.load_sample_editorials()
        elif source == "all":
            return self.loader.load_all()
        else:
            logger.warning(f"Unknown source: {source}, using sample")
            return self.loader.load_sample_editorials()
