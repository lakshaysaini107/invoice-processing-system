from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.auth import router as auth_router
from backend.api.erp import router as erp_router
from backend.api.export import router as export_router
from backend.api.process import router as process_router
from backend.api.review import router as review_router
from backend.api.upload import router as upload_router
from backend.app.config import settings
from backend.core.logging import logger
from backend.database.mysql import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database connection...")
    await db_manager.connect()
    yield
    logger.info("Closing database connection pool...")
    await db_manager.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Invoice Processing System API",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Checks
@app.get("/health", tags=["Health"])
@app.get("/healthz", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

# Mount API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(process_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(erp_router, prefix="/api")
