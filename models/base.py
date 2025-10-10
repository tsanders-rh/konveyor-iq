"""
Base model interface for LLM adapters.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time


class BaseModel(ABC):
    """Base class for all LLM model adapters."""

    def __init__(
        self,
        name: str,
        config: Dict[str, Any]
    ):
        """
        Initialize model adapter.

        Args:
            name: Model name/identifier
            config: Model configuration (API keys, parameters, etc.)
        """
        self.name = name
        self.config = config
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 2000)

    @abstractmethod
    def generate(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from the model.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Dictionary containing:
                - response: str - Generated text
                - tokens_used: int - Total tokens used
                - response_time_ms: float - Response time
                - cost: float - Estimated cost in USD
                - raw_response: Any - Raw API response
        """
        pass

    def generate_with_timing(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response and track timing.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary with timing information
        """
        start_time = time.time()

        try:
            result = self.generate(prompt, **kwargs)
            end_time = time.time()

            result["response_time_ms"] = (end_time - start_time) * 1000
            return result

        except Exception as e:
            end_time = time.time()
            return {
                "response": "",
                "tokens_used": 0,
                "response_time_ms": (end_time - start_time) * 1000,
                "cost": 0.0,
                "error": str(e),
                "raw_response": None
            }

    def extract_code_and_explanation(
        self,
        response: str
    ) -> tuple[str, str]:
        """
        Extract code and explanation from model response.

        Assumes format:
        FIXED CODE:
        ```language
        code here
        ```

        EXPLANATION:
        explanation here

        Args:
            response: Raw model response

        Returns:
            (code, explanation) tuple
        """
        import re

        # Extract code block
        code_match = re.search(
            r'FIXED CODE:?\s*```\w*\n(.*?)```',
            response,
            re.DOTALL | re.IGNORECASE
        )

        if not code_match:
            # Try alternative format
            code_match = re.search(
                r'```\w*\n(.*?)```',
                response,
                re.DOTALL
            )

        code = code_match.group(1).strip() if code_match else ""

        # Extract explanation
        explanation_match = re.search(
            r'EXPLANATION:?\s*(.*)',
            response,
            re.DOTALL | re.IGNORECASE
        )

        if not explanation_match:
            # If no explicit explanation section, use text after code
            if code_match:
                explanation = response[code_match.end():].strip()
            else:
                explanation = response
        else:
            explanation = explanation_match.group(1).strip()

        return code, explanation

    def calculate_cost(
        self,
        tokens_used: int,
        model_name: str
    ) -> float:
        """
        Calculate estimated cost based on tokens.

        Args:
            tokens_used: Total tokens (prompt + completion)
            model_name: Model identifier

        Returns:
            Estimated cost in USD
        """
        # Pricing as of 2024 (approximate)
        pricing = {
            "gpt-4-turbo": 0.00003,  # $30 per 1M tokens
            "gpt-3.5-turbo": 0.000002,  # $2 per 1M tokens
            "claude-3-5-sonnet": 0.00003,  # $30 per 1M tokens
            "claude-3-opus": 0.00006,  # $60 per 1M tokens
        }

        # Default to average price if model not found
        price_per_token = pricing.get(model_name, 0.00002)
        return tokens_used * price_per_token
