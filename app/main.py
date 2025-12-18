from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import MongoDB
from app.core.config import settings
from app.core.logging import setup_logging
from app.api import routes_scouting, routes_search

# Setup logging at startup
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Startup
    MongoDB.connect()
    yield
    # Shutdown
    MongoDB.close()


app = FastAPI(
    title="GenAI Bootcamp Project",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(routes_scouting.router)
app.include_router(routes_search.router)

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to GenAI Bootcamp Project",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "mongodb",
        "environment": settings.ENVIRONMENT
    }
