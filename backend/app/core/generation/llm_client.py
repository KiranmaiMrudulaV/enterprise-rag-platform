"""
LLMClient — thin wrapper around the Anthropic SDK.

Isolated behind this class for the same reason VectorStore isolates ChromaDB:
if the model or provider changes, this is the only file that needs to change.
"""

from app.config import settings


class LLMClient:
    def __init__(self):
        from anthropic import Anthropic

        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model

    async def generate(self, prompt: str) -> dict:
        """Returns {"text": str, "token_count": int}."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=settings.llm_max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        text = "".join(block.text for block in response.content if block.type == "text")
        token_count = response.usage.input_tokens + response.usage.output_tokens

        return {"text": text, "token_count": token_count}
