"""Logging configuration untuk distributed system"""

import sys
from loguru import logger
from pathlib import Path
from .config import Config


def setup_logger(node_id: str = None):
    """Setup logger dengan konfigurasi yang tepat"""
    
    # Remove default handler
    logger.remove()
    
    # Determine node ID
    if node_id is None:
        node_id = Config.NODE_ID
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               f"<cyan>{node_id}</cyan> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=Config.LOG_LEVEL,
        colorize=True
    )
    
    # File handler for all logs
    logger.add(
        log_dir / f"{node_id}_all.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="7 days",
        compression="zip"
    )
    
    # File handler for errors only
    logger.add(
        log_dir / f"{node_id}_error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="50 MB",
        retention="14 days",
        compression="zip"
    )
    
    logger.info(f"Logger initialized for node: {node_id}")
    return logger
