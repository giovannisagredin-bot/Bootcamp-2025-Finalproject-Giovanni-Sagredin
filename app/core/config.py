import os
import logging

DEFAULT_LOG_LEVEL = "INFO"

class AppConfig:
    APP_NAME = "Sports Analytics System"
    APP_VERSION = "0.1.0"
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    FILE_SNAPSHOT: bool = bool(int(os.getenv('FILE_SNAPSHOT', '0')))
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'player-dataset')
    MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'final-project')
    
    # ChromaDB Cloud Configuration
    CHROMA_API_KEY = os.getenv('CHROMA_API_KEY', None)
    CHROMA_TENANT = os.getenv('CHROMA_TENANT', None)
    CHROMA_DATABASE = os.getenv('CHROMA_DATABASE', None)
    
    log_file: str = "app.log"
    default_log_level: int = logging.INFO


# Global settings instance
settings = AppConfig()