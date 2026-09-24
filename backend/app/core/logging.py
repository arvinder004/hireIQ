import logging
import sys

def setup_logging() -> logging.Logger:
    """Configure structured logging for the entire application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    ))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # Avoid duplicate handlers if uvicorn --reload re-imports this
    if not root.handlers:
        root.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logging.getLogger("hireiq")

log = setup_logging()
