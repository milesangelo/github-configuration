"""
Logging utilities for the GitHub Organization Configurator
"""

import logging


def setup_logging(verbose=False, log_file=None):
    """
    Configure logging with optional file output and verbosity level.

    Args:
        verbose (bool): Enable verbose (DEBUG) logging
        log_file (str): Path to log file for output

    Returns:
        logging.Logger: Configured logger
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    return logging.getLogger("github-configurator")
