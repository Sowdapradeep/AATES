import abc
from typing import Callable, Coroutine, Any

class SchedulerProvider(abc.ABC):
    """Abstract interface defining standard job scheduling capabilities."""
    
    @abc.abstractmethod
    async def add_job(
        self,
        job_id: str,
        trigger_type: str,
        expression: str,
        job_func: Callable[..., Coroutine[Any, Any, None]],
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Schedules a recurring task job in the executor loop."""
        pass

    @abc.abstractmethod
    async def remove_job(self, job_id: str) -> None:
        """Removes a planned task from the active scheduler executor queue."""
        pass

    @abc.abstractmethod
    async def start(self) -> None:
        """Starts the background worker queue scheduler loops."""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Performs a clean system shutdown of active task runners."""
        pass
