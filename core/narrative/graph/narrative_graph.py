import uuid
from typing import Any, List, Dict
from sqlalchemy.orm import Session
from core.narrative.services.character_service import CharacterService
from core.narrative.services.relationship_service import RelationshipService

class NarrativeGraphEngine:
    """
    Constructs in-memory character interaction graphs to analyze narrative tension,
    alliances, and character network centrality across a Universe.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.character_service = CharacterService(db)
        self.relationship_service = RelationshipService(db)

    def build_universe_graph(self, universe_id: uuid.UUID | str) -> Dict[str, Any]:
        chars = self.character_service.list_by_universe(universe_id)
        nodes = [{"id": str(c.id), "name": c.name, "role": c.role} for c in chars]
        
        edges = []
        for c in chars:
            rels = self.relationship_service.get_for_character(c.id)
            for r in rels:
                edge = {
                    "source": str(r.character_a_id),
                    "target": str(r.character_b_id),
                    "type": r.relationship_type,
                    "tension": r.tension_level
                }
                if edge not in edges:
                    edges.append(edge)
                    
        return {
            "universe_id": str(universe_id),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges
        }
