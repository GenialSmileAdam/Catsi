import logging
import sys


def setup_logging():
    """
    Configure the root logger to output to console with a standard format.
    All loggers in the app will inherit this configuration.
    """
    # Remove any default handlers (like uvicorn's)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create a handler that writes to stderr (so it doesn't interfere with stdout if needed)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)

    # Define the format: timestamp | level | module | function | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Apply to the root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)  # Change to DEBUG for more details

    # Set specific levels for noisy libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # SQLAlchemy: keep it quiet unless DEBUG mode is on (we'll adjust in config)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)