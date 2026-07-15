from abc import ABC, abstractmethod
from typing import Any

class VoiceProvider(ABC):
    """Abstract interface contract for all downstream Text-to-Speech (Voice) providers."""
    
    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        emotional_tone: str,
        speaking_speed: float = 1.0,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Triggers voice synthesis, returning storage locations and metrics."""
        pass
