import logging
from typing import Any
from core.database.session import SessionLocal
from core.database.models import SystemState, Asset, AuditLog, DecisionLog

logger = logging.getLogger("memory_manager")

class MemoryManager:
    """Manages system memory lifecycles, scopes, and database adapters in AATES."""
    
    # 1. Short-Term Memory (Context-specific, ephemeral)
    def __init__(self) -> None:
        self._ephemeral_working_memory: dict[str, dict[str, Any]] = {}

    def get_working_memory(self, session_id: str, key: str) -> Any:
        """Retrieves ephemeral, session-bound short-term parameters."""
        session_data = self._ephemeral_working_memory.get(session_id, {})
        return session_data.get(key)

    def set_working_memory(self, session_id: str, key: str, value: Any) -> None:
        """Stores ephemeral, session-bound parameters in memory."""
        if session_id not in self._ephemeral_working_memory:
            self._ephemeral_working_memory[session_id] = {}
        self._ephemeral_working_memory[session_id][key] = value

    def clear_working_memory(self, session_id: str) -> None:
        """Cleans up and removes a session context from short-term memory."""
        if session_id in self._ephemeral_working_memory:
            del self._ephemeral_working_memory[session_id]
            logger.info(f"Memory: Cleared working memory for session '{session_id}'")

    # 2. Long-Term / Semantic Memory (Database-backed, permanent)
    def get_universe_lore_memory(self, universe_id: str) -> dict[str, Any]:
        """Queries permanent universe parameters and story rules."""
        db = SessionLocal()
        try:
            state = db.query(SystemState).filter(SystemState.state_key == f"lore-{universe_id}").first()
            return state.state_value if state else {}
        finally:
            db.close()

    def set_universe_lore_memory(self, universe_id: str, lore_data: dict[str, Any]) -> None:
        """Saves permanent universe lore details in the database state."""
        db = SessionLocal()
        try:
            state = db.query(SystemState).filter(SystemState.state_key == f"lore-{universe_id}").first()
            if not state:
                state = SystemState(state_key=f"lore-{universe_id}", state_value=lore_data)
                db.add(state)
            else:
                state.state_value = lore_data
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update universe lore memory: {str(e)}")
        finally:
            db.close()

    # 3. Episodic Memory (Asset and screenplay histories)
    def record_episodic_asset(self, asset_data: dict[str, Any]) -> None:
        """Logs an episodic asset metadata reference into the Assets registry."""
        db = SessionLocal()
        try:
            asset = Asset(**asset_data)
            db.add(asset)
            db.commit()
            logger.info(f"Memory: Registered asset metadata '{asset.id}' of type '{asset.type}'")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save episodic asset metadata: {str(e)}")
        finally:
            db.close()

memory_manager = MemoryManager()
