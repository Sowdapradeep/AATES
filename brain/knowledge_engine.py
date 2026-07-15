import os
import yaml
from typing import Any

class KnowledgeEngine:
    """Core knowledge engine parsing externalized reusable cinematic and cultural parameter templates."""
    
    def __init__(self, base_path: str = "./knowledge") -> None:
        self.base_path = base_path
        self._data: dict[str, Any] = {}

    def load_knowledge(self) -> None:
        """Parses and loads the external YAML definitions into the active memory cache."""
        file_path = os.path.join(self.base_path, "genres", "definitions.yaml")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}

    def get_genre_info(self, genre_name: str) -> dict[str, Any]:
        """Retrieves narrative structure rules and archetypes for a given genre."""
        if not self._data:
            self.load_knowledge()
        return self._data.get("genres", {}).get(genre_name, {})

    def get_slang_vocabulary(self, region: str) -> list[str]:
        """Retrieves regional Tamil dialogue slang vocabularies list."""
        if not self._data:
            self.load_knowledge()
        return self._data.get("tamil_culture", {}).get("regional_slang", {}).get(region, [])

    def get_cinematography_profile(self, category: str) -> dict[str, Any]:
        """Retrieves cinematographic camera framing directions parameters."""
        if not self._data:
            self.load_knowledge()
        return self._data.get("tamil_culture", {}).get("cinematic_techniques", {}).get(category, {})

knowledge_engine = KnowledgeEngine()
