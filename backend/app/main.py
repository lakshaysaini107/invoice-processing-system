from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from backend.app.config import settings
from backend.core.logging import logger
import time

# Database imports
from backend.database.mysql import MySQLClient

# API Router imports
from backend.api import auth, upload, process, review, export, erp

# Database connection startup
async def startup_event():
    """Run on application startup"""
    logger.info("Application starting...")
    logger.info(f"App Name: {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Connect to MySQL (required)
    try:
        await MySQLClient.connect_mysql()
        logger.info("MySQL connected")
    except Exception as e:
        logger.exception("Failed to connect to MySQL: %s", str(e))
        raise


async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Application shutting down...")

    # Close MySQL connection
    try:
        await MySQLClient.close_mysql()
        logger.info("MySQL connection closed")
    except Exception as e:
        logger.error(f"Error closing MySQL: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered invoice data extraction system",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Trusted Host Middleware (Security)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(erp.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )
