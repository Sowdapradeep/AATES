import uuid
import datetime
from typing import Any
from sqlalchemy.orm import Session
from core.database.session import SessionLocal
from core.database.models import SystemState

class StoryBibleEngine:
    """Core story bible engine managing versioned updates and audit histories tracking changes delta details."""
    
    def get_bible(self, universe_id: str, db: Session = None) -> dict[str, Any]:
        """Retrieves the active story bible state for a given universe."""
        session = db or SessionLocal()
        try:
            state = session.query(SystemState).filter(SystemState.state_key == f"bible-{universe_id}").first()
            return state.state_value if state else {
                "characters": {},
                "locations": {},
                "timeline": [],
                "rules": [],
                "version": 1
            }
        finally:
            if not db:
                session.close()

    def update_bible(
        self,
        universe_id: str,
        section: str,
        key: str,
        new_value: Any,
        author: str,
        reason: str,
        workflow_id: str | None = None,
        db: Session = None
    ) -> None:
        """Applies a versioned change and logs an audit log trail inside the database."""
        session = db or SessionLocal()
        try:
            state_key = f"bible-{universe_id}"
            state = session.query(SystemState).filter(SystemState.state_key == state_key).first()
            
            bible_data = state.state_value if state else {
                "characters": {},
                "locations": {},
                "timeline": [],
                "rules": [],
                "version": 1
            }
            
            # Fetch previous value for delta tracking
            if isinstance(bible_data.get(section), dict):
                prev_value = bible_data[section].get(key)
            elif isinstance(bible_data.get(section), list):
                prev_value = f"list-index-{key}"
            else:
                prev_value = None
            
            # Write new value
            if isinstance(bible_data.get(section), dict):
                bible_data[section][key] = new_value
            elif isinstance(bible_data.get(section), list):
                bible_data[section].append(new_value)
            else:
                bible_data[section] = {key: new_value}
                
            bible_data["version"] = bible_data.get("version", 1) + 1
            
            if not state:
                state = SystemState(state_key=state_key, state_value=bible_data)
                session.add(state)
            else:
                # Force SQLAlchemy to detect changes inside dict
                state.state_value = {}
                session.flush()
                state.state_value = bible_data
            session.flush()
            
            # Generate auditable change record
            history_key = f"bible-history-{universe_id}"
            history_state = session.query(SystemState).filter(SystemState.state_key == history_key).first()
            
            audit_record = {
                "change_id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "authoring_agent": author,
                "reason": reason,
                "section": section,
                "key": key,
                "previous_value": prev_value,
                "new_value": new_value,
                "workflow_id": workflow_id
            }
            
            if not history_state:
                history_state = SystemState(state_key=history_key, state_value=[audit_record])
                session.add(history_state)
            else:
                hist_list = list(history_state.state_value)
                hist_list.append(audit_record)
                history_state.state_value = []
                session.flush()
                history_state.state_value = hist_list
                
            if not db:
                session.commit()
        except Exception as e:
            if not db:
                session.rollback()
            raise e
        finally:
            if not db:
                session.close()

story_bible_engine = StoryBibleEngine()
