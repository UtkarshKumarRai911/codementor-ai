"""Evaluation metrics for CodeMentor AI pipeline quality assessment."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class HallucinationDetector:
    """Detect hallucinations in generated responses.

    Checks if the generated explanation contradicts known facts
    or introduces unsupported claims.
    """

    # Known incorrect statements to check against
    KNOWN_CONTRADICTIONS = [
        ("dijkstra", "negative weights", "works with negative"),
        ("binary search", "unsorted", "works on unsorted"),
        ("hash map", "O(n)", "always O(1)"),
        ("quicksort", "stable", "quicksort is stable"),
        ("BFS", "weighted", "BFS finds shortest path in weighted"),
    ]

    def detect(
        self,
        explanation: str,
        question: str,
        context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Detect potential hallucinations in the explanation.

        Args:
            explanation: Generated explanation text
            question: Original question
            context: Retrieved context documents

        Returns:
            Dictionary with hallucination score and details
        """
        if not explanation:
            return {"score": 0.0, "issues": ["Empty explanation"]}

        issues = []
        explanation_lower = explanation.lower()

        # Check for known contradictions
        for topic, context_word, contradiction in self.KNOWN_CONTRADICTIONS:
            if topic in explanation_lower and contradiction in explanation_lower:
                issues.append(
                    f"Potential contradiction: claims '{contradiction}' "
                    f"regarding '{topic}'"
                )

        # Check for unsupported certainty markers
        certainty_phrases = [
            "always works", "never fails", "guaranteed to be",
            "impossible to", "100% correct",
        ]
        for phrase in certainty_phrases:
            if phrase in explanation_lower:
                issues.append(f"Overconfident claim: '{phrase}'")

        # Check context grounding
        if context:
            context_text = " ".join(
                doc.get("content", "") for doc in context
            ).lower()
            # Check if key claims are grounded in context
            sentences = re.split(r"[.!?]+", explanation)
            ungrounded_count = 0
            for sentence in sentences:
                if len(sentence.strip()) > 50:  # Only check substantial claims
                    words = set(sentence.lower().split())
                    context_words = set(context_text.split())
                    overlap = len(words & context_words) / max(len(words), 1)
                    if overlap < 0.1:
                        ungrounded_count += 1

            if ungrounded_count > len(sentences) * 0.5:
                issues.append(
                    f"Many claims ({ungrounded_count}) have low context grounding"
                )

        # Calculate hallucination score (0 = no hallucination, 1 = severe)
        score = min(len(issues) * 0.2, 1.0)

        return {"score": score, "issues": issues}


class RetrievalEvaluator:
    """Evaluate the quality of retrieved context."""

    def evaluate(
        self,
        query: str,
        retrieved_docs: list[dict[str, Any]],
        expected_keywords: list[str],
    ) -> dict[str, Any]:
        """Evaluate retrieval quality.

        Args:
            query: Original query
            retrieved_docs: Retrieved documents
            expected_keywords: Keywords expected in relevant docs

        Returns:
            Dictionary with precision, recall, and relevance score
        """
        if not retrieved_docs:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "relevance_score": 0.0,
                "details": "No documents retrieved",
            }

        # Check keyword coverage in retrieved documents
        all_text = " ".join(
            doc.get("content", "") for doc in retrieved_docs
        ).lower()

        keywords_found = sum(
            1 for kw in expected_keywords if kw.lower() in all_text
        )
        recall = keywords_found / max(len(expected_keywords), 1)

        # Estimate precision: what fraction of retrieved docs are relevant
        relevant_docs = 0
        for doc in retrieved_docs:
            content = doc.get("content", "").lower()
            if any(kw.lower() in content for kw in expected_keywords):
                relevant_docs += 1

        precision = relevant_docs / max(len(retrieved_docs), 1)

        # F1-like relevance score
        if precision + recall > 0:
            relevance_score = 2 * precision * recall / (precision + recall)
        else:
            relevance_score = 0.0

        return {
            "precision": precision,
            "recall": recall,
            "relevance_score": relevance_score,
            "keywords_found": keywords_found,
            "total_keywords": len(expected_keywords),
        }


class CodeFixEvaluator:
    """Evaluate the quality of generated code fixes."""

    def evaluate(
        self,
        generated_code: str,
        expected_contains: str,
        original_code: str = "",
    ) -> dict[str, Any]:
        """Evaluate code fix quality.

        Args:
            generated_code: Generated/fixed code
            expected_contains: String expected in the fix
            original_code: Original buggy code

        Returns:
            Dictionary with correctness metrics
        """
        if not expected_contains:
            return {"score": 1.0, "contains_fix": True, "details": "No fix expected"}

        if not generated_code:
            return {"score": 0.0, "contains_fix": False, "details": "No code generated"}

        contains_fix = expected_contains.lower() in generated_code.lower()

        # Check if the fix is different from original
        is_different = generated_code.strip() != original_code.strip()

        # Check for common code quality indicators
        has_comments = "#" in generated_code or '"""' in generated_code
        has_proper_indentation = not re.search(r"^\S.*\n\s+\S", generated_code)

        score = 0.0
        if contains_fix:
            score += 0.5
        if is_different:
            score += 0.2
        if has_comments:
            score += 0.15
        if has_proper_indentation:
            score += 0.15

        return {
            "score": min(score, 1.0),
            "contains_fix": contains_fix,
            "is_different": is_different,
            "has_comments": has_comments,
            "details": "Fix found" if contains_fix else "Expected fix not found",
        }


def run_full_evaluation(
    category: str = "all",
    verbose: bool = False,
) -> dict[str, Any]:
    """Run the full evaluation suite.

    Args:
        category: Category to evaluate ("all", "debug", "explain", "generate")
        verbose: Whether to print detailed results

    Returns:
        Dictionary with evaluation results
    """
    from agents.graph import run_agent_pipeline

    from .eval_dataset import EVAL_DATASET

    # Filter dataset by category
    if category != "all":
        dataset = [d for d in EVAL_DATASET if d["category"] == category]
    else:
        dataset = EVAL_DATASET

    hallucination_detector = HallucinationDetector()
    retrieval_evaluator = RetrievalEvaluator()
    code_fix_evaluator = CodeFixEvaluator()

    results = {
        "total_cases": len(dataset),
        "passed": 0,
        "failed": 0,
        "hallucination_rate": 0.0,
        "retrieval_precision": 0.0,
        "code_fix_accuracy": 0.0,
        "overall_score": 0.0,
        "details": [],
    }

    hallucination_scores = []
    retrieval_scores = []
    fix_scores = []

    for i, sample in enumerate(dataset):
        logger.info(f"Evaluating sample {i+1}/{len(dataset)}: {sample['question'][:50]}...")

        try:
            # Run the pipeline
            result = run_agent_pipeline(
                question=sample["question"],
                code_snippet=sample.get("code_snippet", ""),
                language=sample.get("language", "python"),
                error_message=sample.get("error_message", ""),
                query_type=sample["category"],
            )

            # Evaluate hallucination
            hallucination = hallucination_detector.detect(
                explanation=result.get("explanation", ""),
                question=sample["question"],
                context=result.get("retrieved_context", []),
            )
            hallucination_scores.append(hallucination["score"])

            # Evaluate retrieval
            retrieval = retrieval_evaluator.evaluate(
                query=sample["question"],
                retrieved_docs=result.get("retrieved_context", []),
                expected_keywords=sample["expected_keywords"],
            )
            retrieval_scores.append(retrieval["relevance_score"])

            # Evaluate code fix
            fix_eval = code_fix_evaluator.evaluate(
                generated_code=result.get("fixed_code", "") or result.get("explanation", ""),
                expected_contains=sample.get("expected_fix_contains", ""),
                original_code=sample.get("code_snippet", ""),
            )
            fix_scores.append(fix_eval["score"])

            # Determine pass/fail
            passed = (
                hallucination["score"] < 0.5
                and (retrieval["relevance_score"] > 0.3 or not sample["expected_keywords"])
                and fix_eval["score"] > 0.3
            )
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1

            if verbose:
                detail = {
                    "question": sample["question"][:80],
                    "category": sample["category"],
                    "passed": passed,
                    "hallucination_score": hallucination["score"],
                    "retrieval_score": retrieval["relevance_score"],
                    "fix_score": fix_eval["score"],
                }
                results["details"].append(detail)
                logger.info(f"  Result: {'PASS' if passed else 'FAIL'} "
                           f"(H:{hallucination['score']:.2f}, R:{retrieval['relevance_score']:.2f}, "
                           f"F:{fix_eval['score']:.2f})")

        except Exception as e:
            logger.error(f"Evaluation failed for sample {i+1}: {e}")
            results["failed"] += 1
            hallucination_scores.append(1.0)
            retrieval_scores.append(0.0)
            fix_scores.append(0.0)

    # Compute aggregate metrics
    if hallucination_scores:
        results["hallucination_rate"] = sum(hallucination_scores) / len(hallucination_scores)
    if retrieval_scores:
        results["retrieval_precision"] = sum(retrieval_scores) / len(retrieval_scores)
    if fix_scores:
        results["code_fix_accuracy"] = sum(fix_scores) / len(fix_scores)

    results["overall_score"] = (
        (1.0 - results["hallucination_rate"])
        + results["retrieval_precision"]
        + results["code_fix_accuracy"]
    ) / 3.0

    return results
