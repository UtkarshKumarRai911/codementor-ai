"""ChromaDB vector store management for CodeMentor AI."""

import logging
from typing import Any, ClassVar

import chromadb
from django.conf import settings

from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB persistent vector store wrapper.

    Provides methods for adding documents and querying similar content.
    Uses singleton pattern for the ChromaDB client.
    """

    _instance: ClassVar["VectorStore | None"] = None
    _client = None
    _collection = None

    def __new__(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> chromadb.ClientAPI:
        """Get or create the ChromaDB persistent client."""
        if self._client is None:
            persist_dir = settings.CHROMA_SETTINGS["PERSIST_DIRECTORY"]
            logger.info(f"Initializing ChromaDB client (persist_dir: {persist_dir})")
            self._client = chromadb.PersistentClient(path=persist_dir)
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the document collection."""
        if self._collection is None:
            collection_name = settings.CHROMA_SETTINGS["COLLECTION_NAME"]
            self._collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"Collection '{collection_name}' ready "
                f"(count: {self._collection.count()})"
            )
        return self._collection

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        batch_size: int = 50,
    ) -> int:
        """Add documents to the vector store.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional unique IDs for each document
            batch_size: Number of documents to add per batch

        Returns:
            Number of documents successfully added
        """
        if not documents:
            return 0

        embedding_model = get_embedding_model()
        total_added = 0

        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size] if metadatas else None

            try:
                # Generate embeddings
                embeddings = embedding_model.encode(batch_docs).tolist()

                # Add to collection
                self.collection.add(
                    documents=batch_docs,
                    embeddings=embeddings,
                    metadatas=batch_meta,
                    ids=batch_ids,
                )
                total_added += len(batch_docs)
                logger.debug(f"Added batch of {len(batch_docs)} documents")

            except Exception as e:
                logger.error(f"Failed to add batch starting at index {i}: {e}")
                continue

        logger.info(f"Added {total_added}/{len(documents)} documents to vector store")
        return total_added

    def query_similar(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query for similar documents.

        Args:
            query: Query text
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary with documents, metadatas, distances, and ids
        """
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.encode_single(query)

        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, self.collection.count() or 1),
        }
        if where:
            kwargs["where"] = where

        try:
            results = self.collection.query(**kwargs)

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            return {
                "documents": documents,
                "metadatas": metadatas,
                "distances": distances,
                "ids": ids,
            }
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}

    def get_count(self) -> int:
        """Get the total number of documents in the collection."""
        return self.collection.count()

    def reset(self) -> None:
        """Reset the collection (delete all documents)."""
        collection_name = settings.CHROMA_SETTINGS["COLLECTION_NAME"]
        self.client.delete_collection(collection_name)
        self._collection = None
        logger.warning(f"Collection '{collection_name}' has been reset")


def get_vectorstore() -> VectorStore:
    """Get the singleton vector store instance.

    Returns:
        VectorStore instance
    """
    return VectorStore()
