"""
BionicPRO Reports Service - Main Application Entry Point.

FastAPI service for retrieving prosthesis usage reports from ClickHouse OLAP database.
Reports are pre-aggregated by ETL pipeline - this service performs simple SELECT queries.

API Endpoints:
    GET  /api/reports          - List available reports for user
    GET  /api/reports/summary  - Get user's overall summary
    GET  /api/reports/{date}   - Get detailed daily report
    DELETE /api/reports/cache  - Clear user's cache

Authentication:
    Bearer token (JWT) from Keycloak via bionicpro-auth BFF.
    Users can only access their own reports.

Caching:
    Redis cache with 5-minute TTL for report data.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import reports
from app.services.clickhouse_service import get_clickhouse_service
from app.services.cache_service import get_cache_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")

    yield

    # Shutdown
    logger.info("Shutting down Reports Service")
    get_clickhouse_service().close()
    get_cache_service().close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=__doc__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(reports.router)


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/", tags=["info"])
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Checks connectivity to ClickHouse and Redis.
    """
    clickhouse_ok = get_clickhouse_service().health_check()
    redis_ok = get_cache_service().health_check()

    status = "healthy" if (clickhouse_ok and redis_ok) else "degraded"

    return {
        "status": status,
        "dependencies": {
            "clickhouse": "ok" if clickhouse_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """
    Readiness check for Kubernetes.

    Returns 200 if service is ready to accept traffic.
    """
    clickhouse_ok = get_clickhouse_service().health_check()

    if not clickhouse_ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "ClickHouse unavailable"},
        )

    return {"status": "ready"}


@app.get("/health/live", tags=["health"])
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Returns 200 if service is alive.
    """
    return {"status": "alive"}


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None,
        },
    )


# ============================================================================
# Run with Uvicorn (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
    )
