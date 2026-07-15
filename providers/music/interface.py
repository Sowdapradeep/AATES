from abc import ABC, abstractmethod
from typing import Any

class MusicProvider(ABC):
    """Abstract interface contract for all downstream Music Generation providers."""
    
    @abstractmethod
    async def generate_music(self, mood: str, duration: float, **kwargs: Any) -> dict[str, Any]:
        """Triggers theme soundtrack generation, returning S3 storage locations and metrics."""
        pass
