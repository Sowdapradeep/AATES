import abc
from typing import Any

class LLMProvider(abc.ABC):
    """Abstract interface defining required LLM generating capabilities."""
    
    @abc.abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> str:
        """Invokes generation from an LLM model provider and returns text response."""
        pass
