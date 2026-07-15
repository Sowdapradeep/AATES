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

# Initialize structured logging engine
setup_logging()
logger = get_logger("api_server")

app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="Autonomous AI Tamil Entertainment Studio foundation platform APIs.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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


