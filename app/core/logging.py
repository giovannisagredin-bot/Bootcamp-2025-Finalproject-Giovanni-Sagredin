import logging
import sys
from pathlib import Path


def setup_logging():
    """Configure logging to both console and file"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    
    # File handler (rotating log file)
    file_handler = logging.FileHandler(
        log_dir / "app.log",
        mode="a",
        encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()  # Remove any existing handlers
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    
    logging.info("=" * 80)
    logging.info("Logging configured - Console: INFO, File: DEBUG (logs/app.log)")
    logging.info("=" * 80)