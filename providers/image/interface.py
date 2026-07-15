from abc import ABC, abstractmethod
from typing import Any

class ImageProvider(ABC):
    """Abstract interface contract for all downstream Image Generation providers."""
    
    @abstractmethod
    async def generate_image(self, prompt: str, seed: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Triggers text-to-image asset generation, returning local or remote storage paths and cost."""
        pass
