import abc
import logging

class RuntimeContext(abc.ABC):
    """Abstract interface exposing the dynamic system runtime parameters."""
    
    @property
    @abc.abstractmethod
    def workflow_id(self) -> str | None:
        """The identifier of the active workflow task execution context."""
        pass

    @property
    @abc.abstractmethod
    def request_id(self) -> str:
        """The HTTP request trace identifier."""
        pass

    @property
    @abc.abstractmethod
    def correlation_id(self) -> str:
        """The distributed systems correlation tracing identifier."""
        pass

    @property
    @abc.abstractmethod
    def universe_id(self) -> str | None:
        """The targeted creative lore universe context."""
        pass

    @property
    @abc.abstractmethod
    def season_id(self) -> str | None:
        """The universe production season context."""
        pass

    @property
    @abc.abstractmethod
    def episode_id(self) -> str | None:
        """The specific episodic creation context."""
        pass

    @property
    @abc.abstractmethod
    def logger(self) -> logging.Logger:
        """A context-aware JSON structured logger engine."""
        pass
