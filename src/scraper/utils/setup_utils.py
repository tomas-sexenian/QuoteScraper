import logging
import os
import shutil

from src.scraper.utils.constants import LOG_FORMAT, OUTPUT_FOLDER


def setup_logger(log_file: str) -> None:
    """
    Sets up the root logger to log messages to the specified file and console.
    """
    log_formatter = logging.Formatter(LOG_FORMAT)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Console handler for logging to stdout. Commented out as it was only used for developing
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(log_formatter)
    # root_logger.addHandler(console_handler)


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)


logger = get_logger(__name__)


def clear_last_execution_data() -> None:
    """
    Deletes all files and subdirectories inside the 'outputs' folder.
    """
    outputs_dir = os.path.join(os.getcwd(), OUTPUT_FOLDER)

    if not os.path.exists(outputs_dir):
        return

    for filename in os.listdir(outputs_dir):
        file_path = os.path.join(outputs_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
