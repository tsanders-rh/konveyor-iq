"""
OpenAI model adapter.
"""
import os
from typing import Dict, Any
from openai import OpenAI

from .base import BaseModel


class OpenAIModel(BaseModel):
    """Adapter for OpenAI models (GPT-3.5, GPT-4, etc.)"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)

        # Initialize OpenAI client
        api_key = config.get("api_key", os.getenv("OPENAI_API_KEY"))
        self.client = OpenAI(api_key=api_key)

        # Model identifier
        self.model = config.get("model", name)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using OpenAI API.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (override defaults)

        Returns:
            Response dictionary with generated text and metadata
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code migration assistant that helps fix static analysis violations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )

            generated_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            return {
                "response": generated_text,
                "tokens_used": tokens_used,
                "cost": self.calculate_cost(tokens_used, self.model),
                "raw_response": response,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
