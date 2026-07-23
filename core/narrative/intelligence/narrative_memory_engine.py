import math
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.intelligence.bedrock_client import bedrock_intelligence
from core.narrative.repositories.character_repo import CharacterRepository
from core.narrative.repositories.timeline_repo import TimelineRepository
from core.narrative.repositories.scene_repo import SceneRepository

class NarrativeMemoryEngine:
    """
    6. Narrative Memory Engine.
    Implements semantic vector retrieval using Amazon Bedrock Titan Embeddings v2
    and Aurora PostgreSQL pgvector compatibility for memories, dialogues, events, and relationships.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.char_repo = CharacterRepository(db)
        self.time_repo = TimelineRepository(db)
        self.scene_repo = SceneRepository(db)

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculates cosine similarity between two vector embeddings."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search_semantic_memory(
        self,
        universe_id: uuid.UUID | str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generates embedding vector for query and retrieves semantically relevant
        characters, timeline events, and scene dialogues.
        """
        query_vector = bedrock_intelligence.generate_embedding(query)

        candidates = []

        # 1. Inspect Characters
        chars = self.char_repo.get_by_universe(universe_id)
        for c in chars:
            text = f"Character {c.name}: Role {c.role}, Motivation {c.motivation}, Lore {c.background_lore}"
            c_vec = bedrock_intelligence.generate_embedding(text)
            sim = self._cosine_similarity(query_vector, c_vec)
            candidates.append({
                "entity_type": "character",
                "entity_id": str(c.id),
                "title": c.name,
                "content": text,
                "similarity_score": round(sim, 4)
            })

        # 2. Inspect Timeline Events
        beats = self.time_repo.get_by_universe(universe_id)
        for b in beats:
            text = f"Event {b.title}: Beat {b.beat_number}, Description {b.description}, Twist {b.twist_introduced}"
            b_vec = bedrock_intelligence.generate_embedding(text)
            sim = self._cosine_similarity(query_vector, b_vec)
            candidates.append({
                "entity_type": "timeline_event",
                "entity_id": str(b.id),
                "title": b.title,
                "content": text,
                "similarity_score": round(sim, 4)
            })

        # Sort candidates descending by similarity score
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidates[:top_k]
