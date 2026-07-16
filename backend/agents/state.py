"""Agent state definition for the LangGraph pipeline."""

from typing import Any, TypedDict


class AgentState(TypedDict):
    """State shared across all agents in the LangGraph pipeline.

    Attributes:
        question: The user's original question
        code_snippet: Code provided by the user (may be empty)
        language: Programming language of the code
        error_message: Error message for debugging queries
        query_type: Classified type (debug, explain, generate, optimize)
        query_complexity: Estimated complexity (simple, medium, complex)
        optimized_query: Query optimized for retrieval
        retrieved_context: Documents retrieved from the knowledge base
        retrieval_scores: Relevance scores for retrieved documents
        retrieval_time_ms: Time taken for retrieval in milliseconds
        explanation: Generated explanation of the solution
        fixed_code: Generated or fixed code
        similar_problems: List of similar problems and approaches
        tokens_used: Total tokens consumed
        model_used: Model identifier used for generation
        iteration_count: Number of processing iterations
        errors: List of errors encountered during processing
    """

    # Input fields
    question: str
    code_snippet: str
    language: str
    error_message: str

    # Router output
    query_type: str
    query_complexity: str

    # Retriever output
    optimized_query: str
    retrieved_context: list[dict[str, Any]]
    retrieval_scores: list[float]
    retrieval_time_ms: int | None

    # Code agent output
    explanation: str
    fixed_code: str
    similar_problems: list[dict[str, str]]

    # Metadata
    tokens_used: int | None
    model_used: str
    iteration_count: int
    errors: list[str]
