"""
Main FastAPI application for Multi-Tenant RAG System
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.database import init_db, create_tables
from app.services.vector_service import QdrantVectorService
from app.api import auth_router, documents_router, queries_router, tenants_router

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown
    """
    # Startup
    logger.info("Starting Multi-Tenant RAG System")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize Qdrant vector store
        vector_service = QdrantVectorService()
        await vector_service.init_collection()
        logger.info("Vector store initialized successfully")
        
        # Health check for Qdrant
        is_healthy = await vector_service.health_check()
        if is_healthy:
            logger.info("Vector store health check passed")
        else:
            logger.warning("Vector store health check failed")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Tenant RAG System")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A production-grade Multi-Tenant Retrieval-Augmented Generation (RAG) System",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts if settings.allowed_hosts != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging"""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging"""
    logger.error(
        "Unhandled exception occurred",
        exception=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if not settings.debug else str(exc),
            "status_code": 500
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "app_name": settings.app_name
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including dependencies"""
    try:
        # Check database
        from app.database.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check vector store
    try:
        vector_service = QdrantVectorService()
        vector_healthy = await vector_service.health_check()
        vector_status = "healthy" if vector_healthy else "unhealthy"
    except Exception as e:
        vector_status = f"unhealthy: {str(e)}"
    
    # Check LLM services
    try:
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        available_providers = llm_service.get_available_providers()
        llm_status = f"healthy: {', '.join(available_providers)}"
    except Exception as e:
        llm_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "app_name": settings.app_name,
        "components": {
            "database": db_status,
            "vector_store": vector_status,
            "llm_services": llm_status
        }
    }


# API Routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(queries_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
        "health_check": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )