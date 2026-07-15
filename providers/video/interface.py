from abc import ABC, abstractmethod
from typing import Any

class VideoProvider(ABC):
    """Abstract interface contract for all downstream Video Generation providers."""
    
    @abstractmethod
    async def generate_video(self, image_location: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Triggers image-to-video asset generation, returning local or remote storage paths and cost."""
        pass
