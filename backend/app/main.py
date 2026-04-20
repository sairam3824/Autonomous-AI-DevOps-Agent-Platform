from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import agents, auth, infra, logs, pipelines, projects
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import init_db
from app.db.redis_cache import redis_cache
from app.ml.vector_store import vector_store

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", version=settings.APP_VERSION)
    await init_db()
    logger.info("database_initialized")

    await redis_cache.connect()

    loaded = vector_store.load()
    if loaded:
        logger.info("vector_store_loaded_from_disk")
    else:
        logger.info("vector_store_empty_starting_fresh")

    yield

    await redis_cache.disconnect()
    logger.info("app_shutdown_complete")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Autonomous AI DevOps Agent Platform - Multi-agent system for infrastructure "
        "management, CI/CD optimization, and automated diagnostics. "
        "Powered by Ollama LLM with FAISS RAG."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(projects.router)
app.include_router(pipelines.router)
app.include_router(logs.router)
app.include_router(infra.router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    services = {}

    services["database"] = {"status": "healthy", "type": "sqlite"}

    services["redis"] = {
        "status": "healthy" if redis_cache.is_available else "unavailable",
        "type": "redis",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                services["ollama"] = {"status": "healthy", "models": models}
            else:
                services["ollama"] = {"status": "unhealthy"}
    except Exception:
        services["ollama"] = {"status": "unreachable"}

    stats = vector_store.get_stats()
    services["faiss"] = {
        "status": "healthy",
        "documents": stats["total_documents"],
        "chunks": stats["total_chunks"],
    }

    overall = "healthy" if all(
        s.get("status") == "healthy" for s in services.values()
    ) else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "services": services,
    }
