"""Code Agent - Generates explanations, fixes, and code using Gemini."""

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

CURRENT_GEMINI_MODEL = "gemini-3.5-flash"


def _is_model_unavailable_error(error: Exception) -> bool:
    """Return whether Gemini rejected an unavailable or retired model."""
    message = str(error).lower()
    return (
        ("404" in message or "not found" in message or "no longer available" in message)
        and ("model" in message or "models/" in message)
    )


# System prompts for different query types
SYSTEM_PROMPTS = {
    "debug": """You are an expert debugging assistant. Your task is to:
1. Analyze the code and error message provided
2. Identify the root cause of the bug
3. Provide a clear, step-by-step explanation of the issue
4. Suggest a corrected version of the code
5. Mention any related common pitfalls

Use the retrieved context to inform your answer where relevant.
Always explain WHY the fix works, not just what to change.""",

    "explain": """You are an expert code explainer and teacher. Your task is to:
1. Break down the code or concept into understandable parts
2. Explain the algorithm/approach step by step
3. Discuss time and space complexity
4. Provide examples or analogies where helpful
5. Reference similar problems or patterns

Use the retrieved context to provide comprehensive explanations.
Adjust your explanation level based on the question's complexity.""",

    "generate": """You are an expert code generator. Your task is to:
1. Understand the requirements from the question
2. Design an efficient solution
3. Write clean, well-documented code
4. Include comments explaining key decisions
5. Suggest test cases or edge cases to consider

Use the retrieved context for relevant algorithms and patterns.
Write production-quality code with proper error handling.""",

    "optimize": """You are an expert code optimizer. Your task is to:
1. Analyze the existing code for performance bottlenecks
2. Identify algorithmic improvements
3. Suggest optimized implementations
4. Compare time/space complexity before and after
5. Note any trade-offs in the optimization

Use the retrieved context for optimization patterns and techniques.
Always explain the optimization rationale.""",
}


def format_context(retrieved_context: list[dict[str, Any]]) -> str:
    """Format retrieved context for inclusion in the prompt.

    Args:
        retrieved_context: List of retrieved document chunks

    Returns:
        Formatted context string
    """
    if not retrieved_context:
        return "No relevant context was retrieved from the knowledge base."

    formatted_parts = ["## Relevant Knowledge Base Context:\n"]
    for i, doc in enumerate(retrieved_context, 1):
        content = doc.get("content", doc.get("text", ""))
        source = doc.get("source", "Unknown")
        formatted_parts.append(f"### Source {i} ({source}):\n{content}\n")

    return "\n".join(formatted_parts)


def build_prompt(state: dict) -> str:
    """Build the complete prompt for the Gemini model.

    Args:
        state: Current agent state

    Returns:
        Complete prompt string
    """
    query_type = state.get("query_type", "debug")
    question = state["question"]
    code_snippet = state.get("code_snippet", "")
    language = state.get("language", "python")
    error_message = state.get("error_message", "")
    retrieved_context = state.get("retrieved_context", [])

    # Build user message
    user_parts = [f"**Question:** {question}"]

    if code_snippet:
        user_parts.append(f"\n**Code ({language}):**\n```{language}\n{code_snippet}\n```")

    if error_message:
        user_parts.append(f"\n**Error Message:**\n```\n{error_message}\n```")

    # Add retrieved context
    context_str = format_context(retrieved_context)
    user_parts.append(f"\n{context_str}")

    # Add response format instructions
    user_parts.append("""
**Please respond in the following JSON format:**
{
    "explanation": "Your detailed explanation here",
    "fixed_code": "The corrected/generated code here (if applicable)",
    "similar_problems": [
        {"title": "Problem title", "approach": "Brief approach description"}
    ]
}""")

    return "\n".join(user_parts)


def parse_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM response into structured data.

    Args:
        response_text: Raw response from Gemini

    Returns:
        Parsed response dictionary
    """
    # Try to extract JSON from the response
    try:
        # Look for JSON block in the response
        json_match = None
        if "```json" in response_text:
            start = response_text.index("```json") + 7
            end = response_text.index("```", start)
            json_match = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.index("```") + 3
            end = response_text.index("```", start)
            json_match = response_text[start:end].strip()
        elif "{" in response_text:
            # Try to find JSON object directly
            start = response_text.index("{")
            # Find matching closing brace
            depth = 0
            for i in range(start, len(response_text)):
                if response_text[i] == "{":
                    depth += 1
                elif response_text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        json_match = response_text[start:i + 1]
                        break

        if json_match:
            parsed = json.loads(json_match)
            return {
                "explanation": parsed.get("explanation", ""),
                "fixed_code": parsed.get("fixed_code", ""),
                "similar_problems": parsed.get("similar_problems", []),
            }
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON response: {e}")

    # Fallback: treat entire response as explanation
    return {
        "explanation": response_text,
        "fixed_code": "",
        "similar_problems": [],
    }


def generate_response(state: dict) -> dict:
    """Code agent node - generates response using Gemini.

    Args:
        state: Current agent state

    Returns:
        Updated state with explanation, fixed_code, and similar_problems
    """
    query_type = state.get("query_type", "debug")
    logger.info(f"Code Agent generating response for type: {query_type}")

    try:
        import google.generativeai as genai

        api_key = settings.GEMINI_CONFIG["API_KEY"]
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        genai.configure(api_key=api_key)

        # Configure the model
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=settings.GEMINI_CONFIG["MAX_OUTPUT_TOKENS"],
            temperature=settings.GEMINI_CONFIG["TEMPERATURE"],
            top_p=settings.GEMINI_CONFIG["TOP_P"],
        )

        # google-generativeai 0.3.x does not support the system_instruction
        # constructor argument. Include the role instructions in the prompt so
        # the same behavior works across legacy and newer SDK releases.
        system_prompt = SYSTEM_PROMPTS.get(query_type, SYSTEM_PROMPTS["debug"])
        prompt = f"{system_prompt}\n\n{build_prompt(state)}"

        configured_model = settings.GEMINI_CONFIG["MODEL"]
        model_candidates = [configured_model]
        if configured_model != CURRENT_GEMINI_MODEL:
            model_candidates.append(CURRENT_GEMINI_MODEL)

        response = None
        model_used = configured_model
        for model_name in model_candidates:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                )
                response = model.generate_content(prompt)
                model_used = model_name
                break
            except Exception as model_error:
                if (
                    model_name != CURRENT_GEMINI_MODEL
                    and _is_model_unavailable_error(model_error)
                ):
                    logger.warning(
                        "Configured Gemini model %s is unavailable; retrying with %s",
                        model_name,
                        CURRENT_GEMINI_MODEL,
                    )
                    continue
                raise

        if response is None:
            raise RuntimeError("Gemini did not return a response")

        # Parse response
        parsed = parse_response(response.text)

        # Extract token usage
        tokens_used = None
        if hasattr(response, "usage_metadata"):
            tokens_used = (
                getattr(response.usage_metadata, "total_token_count", None)
                or getattr(response.usage_metadata, "candidates_token_count", 0)
                + getattr(response.usage_metadata, "prompt_token_count", 0)
            )

        logger.info(f"Code Agent generated response (tokens: {tokens_used})")

        return {
            **state,
            "explanation": parsed["explanation"],
            "fixed_code": parsed["fixed_code"],
            "similar_problems": parsed["similar_problems"],
            "tokens_used": tokens_used,
            "model_used": model_used,
        }

    except Exception as e:
        logger.error(f"Code Agent generation failed: {e}", exc_info=True)
        errors = state.get("errors", [])
        errors.append(f"Generation error: {str(e)}")
        return {
            **state,
            "explanation": f"I encountered an error while processing your request: {str(e)}. "
                          "Please check your API key configuration and try again.",
            "fixed_code": "",
            "similar_problems": [],
            "tokens_used": None,
            "model_used": settings.GEMINI_CONFIG.get("MODEL", "unknown"),
            "errors": errors,
        }
