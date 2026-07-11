from pathlib import Path
from loguru import logger
from config import settings

# Consolidate all logs under agentflow/logs/. No stdout sink.
# LOG_DIR is relative to api/ (e.g. "../logs" -> agentflow/logs/).
LOG_DIR = (Path(__file__).parent.parent.parent / settings.LOG_DIR).resolve()
if not LOG_DIR.is_absolute():
    LOG_DIR = (Path(__file__).parent.parent / settings.LOG_DIR).resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def setup_logger():
    logger.remove()  # drop default stderr sink
    logger.add(
        LOG_FILE,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
        enqueue=True,
    )
    return logger
