"""Retriever Agent - Fetches relevant context from the knowledge base."""

import logging
import time
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def optimize_query(question: str, code_snippet: str, query_type: str, language: str) -> str:
    """Optimize the query for better retrieval from the vector store.

    Args:
        question: Original user question
        code_snippet: Code provided by user
        query_type: Classified query type
        language: Programming language

    Returns:
        Optimized query string for retrieval
    """
    # Extract key concepts from the question
    optimized_parts = [question]

    # Add language context
    if language and language != "unknown":
        optimized_parts.append(f"programming language: {language}")

    # Add query type context for better retrieval
    type_context = {
        "debug": "debugging error fix solution",
        "explain": "explanation algorithm concept",
        "generate": "implementation code generation",
        "optimize": "optimization performance improvement",
    }
    if query_type in type_context:
        optimized_parts.append(type_context[query_type])

    # Extract potential algorithm/data structure references from code
    if code_snippet:
        code_lower = code_snippet.lower()
        concepts = []
        concept_keywords = [
            "dynamic programming", "binary search", "dfs", "bfs",
            "dijkstra", "sorting", "graph", "tree", "stack", "queue",
            "linked list", "hash", "recursion", "greedy", "backtracking",
            "segment tree", "union find", "sliding window", "two pointer",
            "topological sort", "knapsack",
        ]
        for keyword in concept_keywords:
            if keyword in code_lower:
                concepts.append(keyword)
        if concepts:
            optimized_parts.append(" ".join(concepts))

    return " ".join(optimized_parts)


def retrieve_context(state: dict) -> dict:
    """Retriever agent node - fetches relevant context from ChromaDB.

    Args:
        state: Current agent state

    Returns:
        Updated state with retrieved context and scores
    """
    question = state["question"]
    code_snippet = state.get("code_snippet", "")
    query_type = state.get("query_type", "debug")
    language = state.get("language", "python")
    complexity = state.get("query_complexity", "medium")

    logger.info(f"Retriever Agent processing: type={query_type}, complexity={complexity}")

    start_time = time.time()
    retrieved_context: list[dict[str, Any]] = []
    retrieval_scores: list[float] = []

    try:
        from rag.retriever import RAGRetriever

        # Optimize query for retrieval
        optimized = optimize_query(question, code_snippet, query_type, language)

        # Determine number of results based on complexity
        n_results_map = {"simple": 3, "medium": 5, "complex": 8}
        n_results = n_results_map.get(complexity, 5)

        # Retrieve documents
        retriever = RAGRetriever()

        if complexity == "complex":
            # Use reranking for complex queries
            results = retriever.retrieve_with_reranking(
                query=optimized, n_results=n_results
            )
        else:
            results = retriever.retrieve(query=optimized, n_results=n_results)

        retrieved_context = results.get("documents", [])
        retrieval_scores = results.get("scores", [])

        logger.info(f"Retrieved {len(retrieved_context)} documents")

    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        state_errors = state.get("errors", [])
        state_errors.append(f"Retrieval error: {str(e)}")
        return {
            **state,
            "optimized_query": optimized if "optimized" in dir() else question,
            "retrieved_context": [],
            "retrieval_scores": [],
            "retrieval_time_ms": int((time.time() - start_time) * 1000),
            "errors": state_errors,
        }

    retrieval_time = int((time.time() - start_time) * 1000)

    return {
        **state,
        "optimized_query": optimized,
        "retrieved_context": retrieved_context,
        "retrieval_scores": retrieval_scores,
        "retrieval_time_ms": retrieval_time,
    }
