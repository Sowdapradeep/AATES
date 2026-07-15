import logging
from contracts.interfaces.runtime_context import RuntimeContext

class RuntimeContextImpl(RuntimeContext):
    """Concrete implementation of the Runtime Context variables mapping."""
    
    def __init__(
        self,
        request_id: str,
        correlation_id: str,
        workflow_id: str | None = None,
        universe_id: str | None = None,
        season_id: str | None = None,
        episode_id: str | None = None,
        logger: logging.Logger | None = None
    ) -> None:
        self._request_id = request_id
        self._correlation_id = correlation_id
        self._workflow_id = workflow_id
        self._universe_id = universe_id
        self._season_id = season_id
        self._episode_id = episode_id
        self._logger = logger or logging.getLogger("runtime_context")

    @property
    def workflow_id(self) -> str | None:
        return self._workflow_id

    @property
    def request_id(self) -> str:
        return self._request_id

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    @property
    def universe_id(self) -> str | None:
        return self._universe_id

    @property
    def season_id(self) -> str | None:
        return self._season_id

    @property
    def episode_id(self) -> str | None:
        return self._episode_id

    @property
    def logger(self) -> logging.Logger:
        return self._logger
pre_configured_context = RuntimeContextImpl("sys-req", "sys-corr")
