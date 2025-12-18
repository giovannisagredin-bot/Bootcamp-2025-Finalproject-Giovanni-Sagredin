"""
MongoDB database connection manager
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB connection singleton"""
    
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None

    
    @classmethod
    def connect(cls):
        """Connect to MongoDB"""
        if cls._client is None:
            logger.info(f"Connecting to MongoDB...")
            cls._client = MongoClient(settings.MONGO_URI)
            cls._database = cls._client[settings.MONGO_DATABASE]
            logger.info("MongoDB connected successfully")
    
    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_database(cls) -> Database:
        """Get database instance"""
        if cls._database is None:
            cls.connect()
        if cls._database is None:
            raise RuntimeError("Failed to connect to MongoDB")
        return cls._database
