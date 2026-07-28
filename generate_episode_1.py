import os
import sys
import asyncio
import logging

# Set up path to project root
sys.path.append("c:/finished project/AATES")

from core.database.session import SessionLocal, Base, engine
from core.narrative.services.universe_service import UniverseService
from core.narrative.dto.narrative_dto import UniverseCreateDTO
from core.revenue.revenue_engine import RevenueGenerationEngine

# Enable debug logging to see full execution details
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_test")

async def run_generation():
    print("\n=======================================================")
    print("STARTING LOCAL EPISODE 1 PRODUCTION & RENDER RUN (DRY RUN)")
    print("=======================================================\n")
    
    # 1. Initialize DB schema
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 2. Get or create Universe
        univ_service = UniverseService(db)
        universes = univ_service.list_universes()
        if not universes:
            u_dto = univ_service.create_universe(UniverseCreateDTO(
                name="AATES Studio Master Universe",
                genre="Epic Drama",
                core_themes=["Heritage", "Justice", "Technology"],
                world_rules=["Realistic contemporary Tamil Nadu setting"]
            ))
            universe_id = u_dto.id
            print(f"[+] Initialized Master Universe: {universe_id}")
        else:
            universe_id = universes[0].id
            print(f"[+] Loaded Master Universe: {universe_id}")
        
        # Bypass daily limit in os.environ for local test run
        os.environ["BYPASS_DAILY_LIMIT"] = "true"
        
        # Mock publishing providers to skip upload
        from providers.publishing.registry import publishing_registry
        yt = publishing_registry.get_provider("youtube")
        ig = publishing_registry.get_provider("instagram")
        
        async def mock_publish(master_reel_path, caption, metadata):
            print(f"\n[DRY RUN] Skipped uploading to platform for: {master_reel_path}")
            return {"status": "success", "detail": "Skipped real upload during local verification"}
            
        if yt:
            yt.publish = mock_publish
            print("[+] Mocked YouTube Publisher to prevent uploading.")
        if ig:
            ig.publish = mock_publish
            print("[+] Mocked Instagram Publisher to prevent uploading.")
            
        # 3. Instantiate and run cycle
        engine_inst = RevenueGenerationEngine(db)
        print("\nExecuting Autonomous Production Cycle...")
        
        result = await engine_inst.execute_autonomous_production_cycle(
            universe_id=universe_id,
            season=1,
            episode=1,
            objective_prompt="Autonomous daily Tamil episode release (Season 1, Episode 1)"
        )
        
        print("\n=======================================================")
        print("EPISODE 1 PRODUCTION RUN COMPLETED")
        print("=======================================================")
        print(f"Status: {result.get('status')}")
        print(f"Details: {result.get('message', 'Cinematic video compilation completed.')}")
        
        video_file = "c:/finished project/AATES/video/outputs/output_1_preview.mp4"
        if os.path.exists(video_file):
            size_mb = os.path.getsize(video_file) / (1024 * 1024)
            print(f"[+] Compiled Video file: {video_file} ({size_mb:.2f} MB)")
        else:
            print("[-] Video file compilation was skipped or failed.")
            
    except Exception as e:
        logger.exception(f"Exception during run: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_generation())
