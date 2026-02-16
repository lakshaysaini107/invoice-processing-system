import logging
import logging.handlers
from pathlib import Path
from backend.app.config import settings


# Create logs directory
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(parents=True, exist_ok=True)


# Configure logging
logger = logging.getLogger("invoice_system")
logger.setLevel(settings.LOG_LEVEL)


# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# File handler
file_handler = logging.handlers.RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=10 * 1024 * 1024, # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)


# Formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)


# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# Export logger
__all__ = ["logger"]