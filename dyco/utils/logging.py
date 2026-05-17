import logging
import sys
from pathlib import Path


def create_logger(name: str, logfile_path: Path) -> logging.Logger:
    """Create (or return) a logger with file and stdout handlers.

    The parent directory of *logfile_path* is created if needed.
    """
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s:%(name)s:  %(message)s')

        if logfile_path:
            logfile_path.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(logfile_path)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger
