"""
Explainability evaluation.
Assesses the quality of explanations and comments.
"""
import re
from typing import Dict, Any

from .base import BaseEvaluator


class ExplainabilityEvaluator(BaseEvaluator):
    """Evaluates explanation quality."""

    def evaluate(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str = None,
        language: str = "java",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate explainability.

        Returns:
            - has_explanation: bool
            - explanation_quality_score: float (0-10)
            - has_inline_comments: bool
            - comment_density: float
        """
        if not self.enabled:
            return {}

        context = context or {}
        explanation = context.get("explanation", "")

        results = {
            "has_explanation": bool(explanation),
            "has_inline_comments": self._has_comments(generated_code, language),
            "comment_density": self._calculate_comment_density(generated_code, language)
        }

        # Grade explanation quality
        if explanation and self.config.get("use_llm_grader", False):
            results["explanation_quality_score"] = self._grade_explanation(
                explanation,
                original_code,
                generated_code,
                context
            )
        elif explanation:
            # Simple heuristic-based scoring
            results["explanation_quality_score"] = self._heuristic_score(explanation)

        return results

    def _has_comments(self, code: str, language: str) -> bool:
        """Check if code has inline comments."""
        if language in ["java", "javascript", "typescript"]:
            # Check for // or /* */ style comments
            return bool(re.search(r'//|/\*', code))
        elif language == "python":
            # Check for # comments
            return bool(re.search(r'#', code))
        return False

    def _calculate_comment_density(self, code: str, language: str) -> float:
        """
        Calculate comment density (ratio of comment lines to code lines).

        Returns:
            Float between 0 and 1
        """
        lines = code.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        comment_lines = 0

        if language in ["java", "javascript", "typescript"]:
            comment_lines = len([l for l in lines if l.strip().startswith('//')])
        elif language == "python":
            comment_lines = len([l for l in lines if l.strip().startswith('#')])

        return comment_lines / total_lines if total_lines > 0 else 0.0

    def _heuristic_score(self, explanation: str) -> float:
        """
        Simple heuristic scoring of explanation quality.

        Checks for:
        - Length (not too short, not too long)
        - Mentions specific changes
        - Clear structure

        Returns:
            Score from 0-10
        """
        score = 5.0  # Base score

        word_count = len(explanation.split())

        # Penalize very short explanations
        if word_count < 10:
            score -= 3
        elif word_count < 20:
            score -= 1

        # Penalize very long explanations
        if word_count > 200:
            score -= 1

        # Bonus for mentioning key terms
        key_terms = ['changed', 'replaced', 'updated', 'migrated', 'fixed']
        if any(term in explanation.lower() for term in key_terms):
            score += 1

        # Bonus for structure (bullets, numbered lists)
        if re.search(r'^\s*[-*\d]+\.', explanation, re.MULTILINE):
            score += 1

        # Bonus for code references
        if '`' in explanation or 'code' in explanation.lower():
            score += 1

        return max(0, min(10, score))

    def _grade_explanation(
        self,
        explanation: str,
        original_code: str,
        generated_code: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Use an LLM to grade explanation quality.

        This would call another LLM to evaluate the explanation.
        Returns score from 0-10.
        """
        # Placeholder for LLM grading
        # In production, this would call the configured grader model
        grader_model = self.config.get("grader_model", "gpt-4-turbo")

        # Prompt for grading:
        # "Rate the following explanation for a code fix on a scale of 0-10..."
        # Return the score

        # For now, return heuristic score
        return self._heuristic_score(explanation)
