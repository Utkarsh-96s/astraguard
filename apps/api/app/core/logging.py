"""Structured logging configuration for ASTRA-GUARD."""
import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Initialize structured logging format."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


logger = logging.getLogger("astraguard")
