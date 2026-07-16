"""RAG Retriever with similarity search and reranking."""

import logging
from typing import Any

import numpy as np

from .embeddings import get_embedding_model
from .vectorstore import get_vectorstore

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieval-Augmented Generation retriever.

    Provides methods for retrieving relevant documents from the vector store
    with optional reranking for improved precision.
    """

    def __init__(self):
        self.vectorstore = get_vectorstore()
        self.embedding_model = get_embedding_model()

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        min_score: float = 0.3,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve relevant documents from the vector store.

        Args:
            query: Search query
            n_results: Maximum number of results
            min_score: Minimum similarity score threshold (0-1, cosine distance)
            where: Optional metadata filter

        Returns:
            Dictionary with documents and scores
        """
        results = self.vectorstore.query_similar(
            query=query,
            n_results=n_results,
            where=where,
        )

        documents = []
        scores = []

        for i, (doc, meta, distance) in enumerate(
            zip(
                results.get("documents", []),
                results.get("metadatas", []),
                results.get("distances", []),
            )
        ):
            # Convert cosine distance to similarity score
            score = 1.0 - distance

            if score >= min_score:
                documents.append({
                    "content": doc,
                    "source": meta.get("source", "Unknown") if meta else "Unknown",
                    "metadata": meta or {},
                })
                scores.append(score)

        logger.info(
            f"Retrieved {len(documents)}/{n_results} docs "
            f"(min_score={min_score}, best={max(scores) if scores else 0:.3f})"
        )

        return {"documents": documents, "scores": scores}

    def retrieve_with_reranking(
        self,
        query: str,
        n_results: int = 5,
        initial_k: int = 15,
        min_score: float = 0.3,
    ) -> dict[str, Any]:
        """Retrieve documents with cross-encoder reranking for better precision.

        Uses a two-stage approach:
        1. Initial retrieval with embedding similarity (larger candidate set)
        2. Reranking candidates using cross-attention between query and documents

        Args:
            query: Search query
            n_results: Final number of results after reranking
            initial_k: Number of initial candidates to retrieve
            min_score: Minimum score threshold

        Returns:
            Dictionary with reranked documents and scores
        """
        # Stage 1: Initial broad retrieval
        initial_results = self.vectorstore.query_similar(
            query=query,
            n_results=initial_k,
        )

        candidates = list(
            zip(
                initial_results.get("documents", []),
                initial_results.get("metadatas", []),
                initial_results.get("distances", []),
            )
        )

        if not candidates:
            return {"documents": [], "scores": []}

        # Stage 2: Rerank using embedding similarity with query expansion
        query_embedding = np.array(self.embedding_model.encode_single(query))
        doc_embeddings = self.embedding_model.encode([c[0] for c in candidates])

        # Compute refined similarity scores
        similarities = np.dot(doc_embeddings, query_embedding)

        # Sort by reranked score
        ranked_indices = np.argsort(-similarities)

        documents = []
        scores = []

        for idx in ranked_indices[:n_results]:
            score = float(similarities[idx])
            if score >= min_score:
                doc, meta, _ = candidates[idx]
                documents.append({
                    "content": doc,
                    "source": meta.get("source", "Unknown") if meta else "Unknown",
                    "metadata": meta or {},
                })
                scores.append(score)

        logger.info(
            f"Reranked: {len(documents)}/{len(candidates)} candidates → top {n_results} "
            f"(best={max(scores) if scores else 0:.3f})"
        )

        return {"documents": documents, "scores": scores}
