from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import MongoDB
from app.core.config import settings
from app.api import routes_predict, routes_prompts





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
