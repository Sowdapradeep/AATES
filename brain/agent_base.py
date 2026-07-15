import abc
import time
from typing import Any
from sqlalchemy.orm import Session
from contracts.interfaces.lifecycle import LifecycleComponent
from contracts.interfaces.runtime_context import RuntimeContext
from runtime.dependency.injector import dependency_resolver
from core.database.session import SessionLocal
from core.database.models import DecisionLog, DecisionReason, DecisionConfidence


class AgentBase(LifecycleComponent, abc.ABC):
    """Base framework class for all AATES autonomous AI agents."""
    
    def __init__(self, name: str, version: str) -> None:
        self.name = name
        self.version = version
        self.context: RuntimeContext | None = None
        self.status: str = "offline"
        self.metrics: dict[str, Any] = {
            "execution_count": 0,
            "total_latency_ms": 0,
            "failure_count": 0
        }

    async def initialize(self) -> None:
        """Initializes dependencies and checks parameters before boot."""
        self.status = "initialized"

    async def start(self) -> None:
        """Transitions agent to active running state."""
        self.status = "running"

    async def pause(self) -> None:
        """Pauses processing tasks without disposing connection handlers."""
        self.status = "paused"

    async def resume(self) -> None:
        """Resumes processing from paused state."""
        self.status = "running"

    async def stop(self) -> None:
        """Halts active task executions."""
        self.status = "stopped"

    async def shutdown(self) -> None:
        """Disposes resources and transitions to offline state."""
        self.status = "offline"

    def inject_context(self, context: RuntimeContext) -> None:
        """Injects active workflow telemetry parameters and JSON logging context."""
        self.context = context

    def get_dependency(self, interface_type: type[Any]) -> Any:
        """Resolves generic provider dependencies dynamically from the Runtime Layer container."""
        return dependency_resolver.resolve(interface_type)

    async def log_decision(
        self,
        decision_type: str,
        inputs: dict[str, Any],
        constraints: list[str],
        alternatives: list[Any],
        selected: Any,
        confidence: float,
        referenced_memory: str | None = None,
        referenced_story_bible: str | None = None,
        db: Session = None
    ) -> None:
        """Registers an explainability decision audit log entry in the database."""
        session = db or SessionLocal()
        try:
            # Persist main decision details
            log_entry = DecisionLog(
                actor_name=self.name,
                decision_type=decision_type,
                payload={
                    "inputs": inputs,
                    "constraints": constraints,
                    "alternatives_considered": alternatives,
                    "selected_outcome": selected,
                    "referenced_memory": referenced_memory,
                    "referenced_story_bible_entries": referenced_story_bible
                }
            )
            session.add(log_entry)
            session.flush()
            
            # Persist confidence score
            conf_entry = DecisionConfidence(
                decision_id=log_entry.id,
                confidence_score=confidence
            )
            session.add(conf_entry)
            
            # Persist rational explanation reason
            reason_entry = DecisionReason(
                decision_id=log_entry.id,
                reason_text=f"Decision by {self.name} on {decision_type}. Selected option: {selected}."
            )
            session.add(reason_entry)
            
            if not db:
                session.commit()
            
            if self.context and self.context.logger:
                self.context.logger.info(f"Decision logged: {self.name} -> {decision_type}")
        except Exception as e:
            if not db:
                session.rollback()
            if self.context and self.context.logger:
                self.context.logger.error(f"Agent '{self.name}' failed to write decision to DB: {str(e)}")
        finally:
            if not db:
                session.close()

    @abc.abstractmethod
    async def run_task(self, task_payload: dict[str, Any]) -> dict[str, Any]:
        """Core decision execution method implemented by individual agent roles."""
        pass
