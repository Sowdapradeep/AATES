import asyncio
import logging
import uuid
from core.config import settings
from core.logging.logger import setup_logging, get_logger
from core.database.session import SessionLocal, Base, engine
from core.narrative.services.universe_service import UniverseService
from core.narrative.dto.narrative_dto import UniverseCreateDTO
from core.revenue.revenue_engine import RevenueGenerationEngine

setup_logging()
logger = get_logger("worker")

async def main() -> None:
    """
    Main worker daemon execution loop.
    Autonomously executes studio revenue production cycles on scheduled heartbeats.
    """
    logger.info(f"Starting AATES Autonomous Production Worker Daemon in '{settings.app.env}' mode...")

    # Ensure database schema is ready
    Base.metadata.create_all(bind=engine)

    # Initialize default studio master universe if none exists
    db = SessionLocal()
    master_universe_id = None
    try:
        univ_service = UniverseService(db)
        universes = univ_service.list_universes()
        if not universes:
            u_dto = univ_service.create_universe(UniverseCreateDTO(
                name="AATES Studio Master Universe",
                genre="Epic Drama",
                core_themes=["Heritage", "Justice", "Technology"],
                world_rules=["Realistic contemporary Tamil Nadu setting"]
            ))
            master_universe_id = u_dto.id
            logger.info(f"Initialized AATES Master Universe: {master_universe_id}")
        else:
            master_universe_id = universes[0].id
            logger.info(f"Loaded existing Master Universe: {master_universe_id}")
    except Exception as e:
        logger.error(f"Error during worker initialization: {e}")
    finally:
        db.close()

    cycle_count = 1
    try:
        while True:
            logger.info(f"Worker heartbeat (Cycle #{cycle_count}): checking queues & financial ceilings...")
            db = SessionLocal()
            try:
                if master_universe_id:
                    rev_engine = RevenueGenerationEngine(db)
                    result = await rev_engine.execute_autonomous_production_cycle(
                        universe_id=master_universe_id,
                        season=1,
                        episode=cycle_count,
                        objective_prompt=f"Autonomous daily Tamil episode release #{cycle_count}"
                    )
                    logger.info(f"Autonomous Production Cycle #{cycle_count} Result: {result}")
            except Exception as loop_err:
                logger.error(f"Error executing autonomous production cycle #{cycle_count}: {loop_err}")
            finally:
                db.close()

            cycle_count += 1
            # Run heartbeat interval (e.g. 60 seconds in worker execution mode)
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("AATES Autonomous Worker Daemon shutting down gracefully.")

if __name__ == "__main__":
    asyncio.run(main())
