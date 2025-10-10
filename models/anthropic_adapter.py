"""
Anthropic (Claude) model adapter.
"""
import os
from typing import Dict, Any
from anthropic import Anthropic

from .base import BaseModel


class AnthropicModel(BaseModel):
    """Adapter for Anthropic Claude models."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)

        # Initialize Anthropic client
        api_key = config.get("api_key", os.getenv("ANTHROPIC_API_KEY"))
        self.client = Anthropic(api_key=api_key)

        # Model identifier
        self.model = config.get("model", name)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using Anthropic API.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system="You are a code migration assistant that helps fix static analysis violations.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            generated_text = response.content[0].text

            # Anthropic doesn't provide token counts in the same way
            # Approximate based on text length
            tokens_used = self._estimate_tokens(prompt + generated_text)

            return {
                "response": generated_text,
                "tokens_used": tokens_used,
                "cost": self.calculate_cost(tokens_used, self.model),
                "raw_response": response,
                "finish_reason": response.stop_reason
            }

        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4
