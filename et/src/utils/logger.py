# ./src/utils/logger.py
"""
Logging utility module.

This module is responsible for creating, configuring, and managing a consistent logger configuration for the entire application.
"""


import logging
import os
import re
from datetime import datetime
from utils.paths import LOGS_DIR


# One log file per session: named with the start time, and with the participant ID once it is known
_SESSION_STAMP = datetime.now().strftime("%Y_%m_%d_%H%M%S")
_log_path = LOGS_DIR / f"ET_{_SESSION_STAMP}.log"
_file_handlers: list[logging.FileHandler] = []


def name_log_with_pid(pid: str) -> None:
    """
    Rename the session log file to include the participant ID.

    :param pid: Participant ID
    :type pid: str
    """
    global _log_path
    new_path = LOGS_DIR / f"ET_{_SESSION_STAMP}_{re.sub(r'[^A-Za-z0-9_-]', '_', pid)}.log"

    # Windows cannot rename a file that is open; closed handlers reopen it on the next record
    for handler in _file_handlers:
        handler.close()
    try:
        os.replace(_log_path, new_path)
        _log_path = new_path
    except OSError:
        pass    # keep the current name
    for handler in _file_handlers:
        handler.baseFilename = str(_log_path)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with both file and console output.
    
    :param name: Logger name (recommended: module name)
    :type name: str
    
    :return: Configured logger instance
    :rtype: Logger
    """

    # Ensure the log directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Log file of this session
    log_filename = _log_path

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Record all levels by default

    # Avoid adding duplicate handlers
    if not logger.handlers:

        # File handler (write to file)
        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        _file_handlers.append(file_handler)

        # Console handler (output to terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger