"""Router Agent - Classifies queries and determines processing path."""

import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

# Heuristic keywords for fallback classification
DEBUG_KEYWORDS = [
    "error", "bug", "fix", "broken", "crash", "exception", "traceback",
    "not working", "fails", "wrong output", "unexpected", "issue",
]
EXPLAIN_KEYWORDS = [
    "explain", "what does", "how does", "why does", "understand",
    "what is", "describe", "clarify", "meaning", "purpose",
]
GENERATE_KEYWORDS = [
    "write", "create", "implement", "generate", "build", "make",
    "code for", "function that", "class that", "script to",
]
OPTIMIZE_KEYWORDS = [
    "optimize", "faster", "efficient", "improve", "performance",
    "reduce", "better", "refactor", "simplify", "speed up",
]

# Complexity indicators
COMPLEX_INDICATORS = [
    "algorithm", "data structure", "dynamic programming", "graph",
    "tree", "recursion", "concurrent", "distributed", "system design",
    "multiple", "complex", "advanced",
]


def classify_query_heuristic(question: str, code_snippet: str, error_message: str) -> str:
    """Classify query type using keyword heuristics.

    Args:
        question: The user's question
        code_snippet: Code provided by the user
        error_message: Error message if any

    Returns:
        Classified query type
    """
    question_lower = question.lower()

    # If error message is present, likely debugging
    if error_message:
        return "debug"

    # Check keywords in order of specificity
    for keyword in GENERATE_KEYWORDS:
        if keyword in question_lower:
            return "generate"

    for keyword in OPTIMIZE_KEYWORDS:
        if keyword in question_lower:
            return "optimize"

    for keyword in DEBUG_KEYWORDS:
        if keyword in question_lower:
            return "debug"

    for keyword in EXPLAIN_KEYWORDS:
        if keyword in question_lower:
            return "explain"

    # Default: if code is provided, assume debug; otherwise explain
    if code_snippet:
        return "debug"
    return "explain"


def estimate_complexity(question: str, code_snippet: str) -> str:
    """Estimate query complexity for resource allocation.

    Args:
        question: The user's question
        code_snippet: Code provided by the user

    Returns:
        Complexity level (simple, medium, complex)
    """
    combined = (question + " " + code_snippet).lower()

    complex_count = sum(1 for indicator in COMPLEX_INDICATORS if indicator in combined)
    code_lines = len(code_snippet.strip().split("\n")) if code_snippet.strip() else 0

    if complex_count >= 2 or code_lines > 50:
        return "complex"
    elif complex_count >= 1 or code_lines > 20:
        return "medium"
    return "simple"


def classify_with_llm(question: str, code_snippet: str, error_message: str) -> str | None:
    """Attempt to classify using Gemini LLM for ambiguous cases.

    Args:
        question: The user's question
        code_snippet: Code provided
        error_message: Error message if any

    Returns:
        Classified query type or None if LLM classification fails
    """
    try:
        import google.generativeai as genai

        api_key = settings.GEMINI_CONFIG["API_KEY"]
        if not api_key:
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            settings.GEMINI_CONFIG.get("MODEL", "gemini-3.5-flash")
        )

        prompt = f"""Classify the following coding question into exactly one category.
Categories: debug, explain, generate, optimize

Question: {question}
{"Code: " + code_snippet[:500] if code_snippet else ""}
{"Error: " + error_message[:200] if error_message else ""}

Respond with ONLY the category name (debug, explain, generate, or optimize):"""

        response = model.generate_content(prompt)
        result = response.text.strip().lower()

        if result in ("debug", "explain", "generate", "optimize"):
            return result

        # Try to extract from response
        for category in ("debug", "explain", "generate", "optimize"):
            if category in result:
                return category

        return None
    except Exception as e:
        logger.warning(f"LLM classification failed: {e}")
        return None


def route_query(state: dict) -> dict:
    """Router agent node - classifies the incoming query.

    Args:
        state: Current agent state

    Returns:
        Updated state with query_type and query_complexity
    """
    question = state["question"]
    code_snippet = state.get("code_snippet", "")
    error_message = state.get("error_message", "")
    provided_type = state.get("query_type", "")

    logger.info(f"Router Agent processing query: {question[:80]}...")

    # Use provided query type if valid
    if provided_type in ("debug", "explain", "generate", "optimize"):
        query_type = provided_type
    else:
        # Try LLM classification first, fall back to heuristics
        query_type = classify_with_llm(question, code_snippet, error_message)
        if query_type is None:
            query_type = classify_query_heuristic(question, code_snippet, error_message)

    complexity = estimate_complexity(question, code_snippet)

    logger.info(f"Router classified: type={query_type}, complexity={complexity}")

    return {
        **state,
        "query_type": query_type,
        "query_complexity": complexity,
    }
