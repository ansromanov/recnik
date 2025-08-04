from datetime import datetime
import logging
import os


def setup_logger(name, level=None):
    """Setup logger with consistent formatting"""

    if level is None:
        level = logging.INFO
        if os.getenv("DEBUG", "false").lower() == "true":
            level = logging.DEBUG

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if logs directory exists)
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if os.path.exists(logs_dir):
        log_file = os.path.join(logs_dir, f"news-service-{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
