"""LangGraph pipeline for the CodeMentor AI multi-agent system."""

import logging
from typing import Any

from django.conf import settings
from langgraph.graph import END, StateGraph

from .code_agent import generate_response
from .retriever_agent import retrieve_context
from .router_agent import route_query
from .state import AgentState

logger = logging.getLogger(__name__)


def should_retrieve(state: AgentState) -> str:
    """Determine if retrieval is needed based on query type and complexity.

    Args:
        state: Current agent state

    Returns:
        Next node name ("retrieve" or "generate")
    """
    query_type = state.get("query_type", "debug")
    complexity = state.get("query_complexity", "medium")

    # Always retrieve for complex queries
    if complexity == "complex":
        return "retrieve"

    # Skip retrieval for simple generation requests
    if query_type == "generate" and complexity == "simple":
        return "generate"

    # Retrieve for everything else
    return "retrieve"


def build_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the multi-agent pipeline.

    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("route", route_query)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)

    # Set entry point
    workflow.set_entry_point("route")

    # Add conditional edges from router
    workflow.add_conditional_edges(
        "route",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "generate": "generate",
        },
    )

    # Retriever always leads to code generation
    workflow.add_edge("retrieve", "generate")

    # Code agent leads to end
    workflow.add_edge("generate", END)

    return workflow.compile()


# Module-level compiled graph (singleton)
_compiled_graph = None


def get_graph():
    """Get or create the compiled graph singleton.

    Returns:
        Compiled StateGraph instance
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agent_pipeline(
    question: str,
    code_snippet: str = "",
    language: str = "python",
    error_message: str = "",
    query_type: str = "debug",
) -> dict[str, Any]:
    """Entry point for running the multi-agent pipeline.

    Args:
        question: The user's question
        code_snippet: Code provided by the user
        language: Programming language
        error_message: Error message for debugging
        query_type: Pre-classified query type

    Returns:
        Dictionary with pipeline results
    """
    logger.info(f"Starting agent pipeline for query: {question[:80]}...")

    # Initialize state
    initial_state: AgentState = {
        "question": question,
        "code_snippet": code_snippet,
        "language": language,
        "error_message": error_message,
        "query_type": query_type,
        "query_complexity": "",
        "optimized_query": "",
        "retrieved_context": [],
        "retrieval_scores": [],
        "retrieval_time_ms": None,
        "explanation": "",
        "fixed_code": "",
        "similar_problems": [],
        "tokens_used": None,
        "model_used": "",
        "iteration_count": 0,
        "errors": [],
    }

    try:
        # Run the graph
        graph = get_graph()
        config = {"recursion_limit": settings.LANGGRAPH_CONFIG["RECURSION_LIMIT"]}
        final_state = graph.invoke(initial_state, config=config)

        logger.info(
            f"Pipeline completed. Type: {final_state.get('query_type')}, "
            f"Tokens: {final_state.get('tokens_used')}"
        )

        return {
            "explanation": final_state.get("explanation", ""),
            "fixed_code": final_state.get("fixed_code", ""),
            "similar_problems": final_state.get("similar_problems", []),
            "retrieved_context": [
                {"content": doc.get("content", doc.get("text", "")), "source": doc.get("source", "")}
                for doc in final_state.get("retrieved_context", [])
            ],
            "retrieval_time_ms": final_state.get("retrieval_time_ms"),
            "tokens_used": final_state.get("tokens_used"),
            "model_used": final_state.get("model_used", ""),
        }

    except Exception as e:
        logger.error(f"Agent pipeline failed: {e}", exc_info=True)
        raise
