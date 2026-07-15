import logging
from typing import Callable, Coroutine, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contracts.interfaces.scheduler import SchedulerProvider

logger = logging.getLogger("apscheduler_provider")

class APSchedulerProvider(SchedulerProvider):
    """Production wrapper implementation of APScheduler complying with SchedulerProvider."""
    
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()

    async def add_job(
        self,
        job_id: str,
        trigger_type: str,
        expression: str,
        job_func: Callable[..., Coroutine[Any, Any, None]],
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Schedules tasks to execute at cron or interval-based triggers."""
        trigger_kwargs = {}
        if trigger_type == "cron":
            trigger_kwargs["trigger"] = "cron"
            parts = expression.split()
            if len(parts) == 5:
                trigger_kwargs["minute"] = parts[0]
                trigger_kwargs["hour"] = parts[1]
                trigger_kwargs["day"] = parts[2]
                trigger_kwargs["month"] = parts[3]
                trigger_kwargs["day_of_week"] = parts[4]
        elif trigger_type == "interval":
            trigger_kwargs["trigger"] = "interval"
            trigger_kwargs["seconds"] = int(expression)

        self._scheduler.add_job(
            job_func,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=True,
            **trigger_kwargs
        )
        logger.info(f"Scheduler: Registered job '{job_id}' ({trigger_type}: '{expression}')")

    async def remove_job(self, job_id: str) -> None:
        """Removes a job if it exists in the active queue list."""
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(f"Scheduler: Removed job '{job_id}'")

    async def start(self) -> None:
        """Starts the scheduler thread executor loop."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler: AsyncIO scheduler loop started.")

    async def shutdown(self) -> None:
        """Performs a clean shutdown halting all execution threads."""
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("Scheduler: AsyncIO scheduler loop stopped.")
