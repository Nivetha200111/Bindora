"""
Main FastAPI application for Bindora

AI-powered drug-target interaction prediction platform.
"""
import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import router
from app.database.db import create_tables, check_database_health

# Configure structured logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Bindora API", version=settings.API_VERSION)

    # Check database health
    db_healthy = await check_database_health()
    if not db_healthy.get("connection"):
        logger.warning("Database connection failed during startup")

    # Create tables if they don't exist
    try:
        await create_tables()
        logger.info("Database tables ready")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))

    # Test model loading
    try:
        from app.dependencies import get_protein_encoder, get_drug_encoder, get_binding_predictor

        # Trigger lazy loading of models
        protein_encoder = get_protein_encoder()
        drug_encoder = get_drug_encoder()
        binding_predictor = get_binding_predictor()

        logger.info(
            "AI models loaded successfully",
            protein_model=protein_encoder.model_name,
            drug_fp_size=drug_encoder.get_fingerprint_size(),
            device=protein_encoder.device
        )

    except Exception as e:
        logger.error("Failed to load AI models", error=str(e))
        raise RuntimeError(f"Critical: Could not load AI models: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Bindora API")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware (security)
if settings.API_HOST != "0.0.0.0":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add processing time to response headers
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Bindora API - AI-powered drug discovery",
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return await check_database_health()


# Include API routes
app.include_router(router, prefix="/api")

# Mount static files (frontend)
import os
from fastapi.responses import FileResponse

frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend/out")

# Serve static files
if os.path.exists(frontend_path):
    app.mount("/_next", StaticFiles(directory=os.path.join(frontend_path, "_next")), name="next")
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon"""
        favicon_path = os.path.join(frontend_path, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        return {"error": "Favicon not found"}
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Serve frontend files"""
        # Skip API routes
        if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc") or path.startswith("openapi.json"):
            return {"error": "API endpoint not found"}
        
        # Try to serve the specific file
        file_path = os.path.join(frontend_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # For SPA routing, serve index.html
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return {"error": "File not found", "path": path}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": time.time()
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting Bindora API server",
        host=settings.API_HOST,
        port=settings.API_PORT
    )

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
