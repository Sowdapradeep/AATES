import asyncio
import logging
from core.config import settings
from core.logging.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("worker")

async def main() -> None:
    """Main worker daemon execution loop listening to scheduled events."""
    logger.info(f"Starting AATES Worker Daemon in '{settings.app.env}' mode...")
    try:
        while True:
            logger.info("Worker daemon heartbeat: checking queues...")
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Worker daemon shutting down gracefully.")

if __name__ == "__main__":
    asyncio.run(main())
