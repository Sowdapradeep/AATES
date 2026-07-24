from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging.logger import setup_logging, get_logger
from core.logging.middleware import LoggingMiddleware
from apps.api.v1.health import router as health_router
from apps.api.v1.version import router as version_router
from apps.api.v1.auth import router as auth_router
from apps.api.v1.cognitive import router as cognitive_router
from apps.api.v1.creative import router as creative_router
from apps.api.v1.production import router as production_router
from apps.api.v1.operations import router as operations_router
from apps.api.v1.validation import router as validation_router
from apps.api.v1.autonomy import router as autonomy_router
from apps.api.v1.runtime import router as runtime_router
from apps.api.v1.publishing import router as publishing_router

# Initialize structured logging engine
setup_logging()
logger = get_logger("api_server")

# Load and apply credentials from AWS Secrets Manager if enabled
from core.config.secrets import fetch_and_apply_secrets
fetch_and_apply_secrets()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app.env != "testing":
        from core.database.session import SessionLocal, engine, Base
        from providers.registry import provider_registry
        from providers.publishing.youtube import verify_youtube_startup
        
        # Ensure all tables (including Narrative Core v1) exist
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            health_map = await provider_registry.run_startup_checks(db)
            logger.info(f"AROS Startup Provider Health Audit Map: {health_map}")
        except Exception as startup_err:
            logger.error(f"Failed to execute startup health audit: {startup_err}")
        finally:
            db.close()

        await verify_youtube_startup()
        from brain.operations.publishing_worker import start_worker
        await start_worker()
        from brain.operations.research_agent import start_research_agent
        await start_research_agent()
        from brain.agents.script_agent import start_script_agent
        await start_script_agent()
        from brain.agents.image_agent import start_image_agent
        await start_image_agent()
        from brain.agents.voice_agent import start_voice_agent
        await start_voice_agent()
        from brain.agents.video_agent import start_video_agent
        await start_video_agent()
        from brain.agents.subtitle_agent import start_subtitle_agent
        await start_subtitle_agent()
        from brain.agents.music_agent import start_music_agent
        await start_music_agent()
        from brain.agents.thumbnail_agent import start_thumbnail_agent
        await start_thumbnail_agent()
        from brain.agents.quality_agent import start_quality_agent
        await start_quality_agent()
        from brain.operations.instagram_worker import start_instagram_worker
        await start_instagram_worker()
        from brain.agents.learning_agent import start_learning_agent
        await start_learning_agent()
        from brain.agents.automation_agent import start_automation_agent
        await start_automation_agent()
        from brain.agents.orchestrator_agent import start_orchestrator_agent
        await start_orchestrator_agent()

    yield

    if settings.app.env != "testing":
        from brain.operations.publishing_worker import stop_worker
        await stop_worker()
        from brain.operations.research_agent import stop_research_agent
        await stop_research_agent()
        from brain.agents.script_agent import stop_script_agent
        await stop_script_agent()
        from brain.agents.image_agent import stop_image_agent
        await stop_image_agent()
        from brain.agents.voice_agent import stop_voice_agent
        await stop_voice_agent()
        from brain.agents.video_agent import stop_video_agent
        await stop_video_agent()
        from brain.agents.subtitle_agent import stop_subtitle_agent
        await stop_subtitle_agent()
        from brain.agents.music_agent import stop_music_agent
        await stop_music_agent()
        from brain.agents.thumbnail_agent import stop_thumbnail_agent
        await stop_thumbnail_agent()
        from brain.agents.quality_agent import stop_quality_agent
        await stop_quality_agent()
        from brain.operations.instagram_worker import stop_instagram_worker
        await stop_instagram_worker()
        from brain.agents.learning_agent import stop_learning_agent
        await stop_learning_agent()
        from brain.agents.automation_agent import stop_automation_agent
        await stop_automation_agent()
        from brain.agents.orchestrator_agent import stop_orchestrator_agent
        await stop_orchestrator_agent()

app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="Autonomous AI Tamil Entertainment Studio foundation platform APIs.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject request context logging middleware
app.add_middleware(LoggingMiddleware)

# Centralized exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Global Exception Handler: {str(exc)} on path {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred."}
    )

# Version-first routing registrations
app.include_router(health_router, tags=["Health"])
app.include_router(version_router, tags=["Version"])
app.include_router(auth_router, prefix="/v1/auth", tags=["Auth"])
app.include_router(cognitive_router, prefix="/v1", tags=["Cognitive"])
app.include_router(creative_router, prefix="/v1", tags=["Creative"])
app.include_router(production_router, prefix="/v1", tags=["Production"])
app.include_router(operations_router, tags=["Operations"])
app.include_router(validation_router, prefix="/v1", tags=["Validation"])
app.include_router(autonomy_router, tags=["Autonomy"])
app.include_router(runtime_router, tags=["Runtime"])
app.include_router(publishing_router, tags=["Publishing"])

from apps.api.v1.research import router as research_router
app.include_router(research_router, prefix="/v1", tags=["Research"])

from apps.api.v1.scripts import router as scripts_router
app.include_router(scripts_router, prefix="/v1", tags=["Scripts"])

from apps.api.v1.images import router as images_router
app.include_router(images_router, prefix="/v1", tags=["Images"])

from apps.api.v1.voices import router as voices_router
app.include_router(voices_router, prefix="/v1", tags=["Voices"])

from apps.api.v1.videos import router as videos_router
app.include_router(videos_router, prefix="/v1", tags=["Videos"])

from apps.api.v1.subtitles import router as subtitles_router
app.include_router(subtitles_router, prefix="/v1", tags=["Subtitles"])

from apps.api.v1.music import router as music_router
app.include_router(music_router, prefix="/v1", tags=["Music"])

from apps.api.v1.thumbnails import router as thumbnails_router
app.include_router(thumbnails_router, prefix="/v1", tags=["Thumbnails"])

from apps.api.v1.quality import router as quality_router
app.include_router(quality_router, prefix="/v1", tags=["Quality"])

from apps.api.v1.instagram_publishing import router as instagram_publishing_router
app.include_router(instagram_publishing_router, prefix="/v1", tags=["Instagram Publishing"])

from apps.api.v1.learning import router as learning_router
app.include_router(learning_router, prefix="/v1", tags=["Learning Engine"])

from apps.api.v1.automation import router as automation_router
app.include_router(automation_router, prefix="/v1", tags=["Automation Engine"])

from apps.api.v1.orchestration import router as orchestration_router
app.include_router(orchestration_router, prefix="/v1", tags=["Multi-Agent Orchestrator"])

from core.narrative.api import narrative_router
app.include_router(narrative_router)

from core.narrative.intelligence.api import intelligence_router
app.include_router(intelligence_router)

from core.finance.api import finance_router
app.include_router(finance_router)

from core.marketing.api import marketing_router
app.include_router(marketing_router)

from core.revenue.api import revenue_router
app.include_router(revenue_router)







# Instantiate and register the Executive Council agents with the runtime registry
from brain.ceo.agent import CEOAgent
from brain.director.creative import CreativeDirectorAgent
from brain.director.production import ProductionDirectorAgent
from brain.director.technology import TechnologyDirectorAgent
from brain.director.analytics import AnalyticsDirectorAgent
from brain.budget.agent import BusinessDirectorAgent

CEOAgent()
CreativeDirectorAgent()
ProductionDirectorAgent()
TechnologyDirectorAgent()
AnalyticsDirectorAgent()
BusinessDirectorAgent()


