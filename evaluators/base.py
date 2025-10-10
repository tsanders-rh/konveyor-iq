"""
Base evaluator interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseEvaluator(ABC):
    """Base class for all evaluators."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize evaluator with configuration.

        Args:
            config: Configuration dictionary for this evaluator
        """
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def evaluate(
        self,
        original_code: str,
        generated_code: str,
        expected_code: str = None,
        language: str = "java",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the generated code.

        Args:
            original_code: Original code with violation
            generated_code: LLM-generated fixed code
            expected_code: Expected correct code (if available)
            language: Programming language
            context: Additional context (rule info, etc.)

        Returns:
            Dictionary of metrics specific to this evaluator
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this evaluator is enabled."""
        return self.enabled
