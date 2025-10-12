"""
Google Gemini model adapter.
"""
import os
from typing import Dict, Any
import google.generativeai as genai

from .base import BaseModel


class GoogleModel(BaseModel):
    """Adapter for Google Gemini models."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)

        # Initialize Google Generative AI
        api_key = config.get("api_key", os.getenv("GOOGLE_API_KEY"))
        genai.configure(api_key=api_key)

        # Model identifier
        self.model_name = config.get("model", name)
        self.model = genai.GenerativeModel(
            self.model_name,
            system_instruction=(
                "You are a code migration assistant specializing in migrating Java EE applications "
                "to Quarkus and Jakarta EE. Use Jakarta EE APIs (jakarta.*) and Quarkus-specific "
                "patterns, NOT Spring Framework. Focus on CDI (@ApplicationScoped, @Inject), "
                "Jakarta Persistence, and Jakarta Transactions."
            )
        )

        # Generation config
        self.generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using Google Gemini API.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        try:
            # Override generation config if kwargs provided
            generation_config = genai.GenerationConfig(
                temperature=kwargs.get("temperature", self.temperature),
                max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            generated_text = response.text

            # Extract usage metadata
            tokens_used = 0
            input_tokens = 0
            output_tokens = 0

            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                tokens_used = input_tokens + output_tokens

            # Calculate cost based on Gemini 1.5 Pro pricing
            # $1.25 per 1M input tokens, $5.00 per 1M output tokens
            input_cost = input_tokens * (1.25 / 1_000_000)
            output_cost = output_tokens * (5.0 / 1_000_000)
            total_cost = input_cost + output_cost

            return {
                "response": generated_text,
                "tokens_used": tokens_used,
                "cost": total_cost,
                "raw_response": response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "finish_reason": getattr(response.candidates[0] if response.candidates else None, 'finish_reason', None)
            }

        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")

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
