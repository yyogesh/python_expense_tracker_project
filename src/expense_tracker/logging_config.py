"""Logging setup - where log messages go and what they look like."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# The name of our package. Every logger created with getLogger(__name__) in
# our files ("expense_tracker.cli", "expense_tracker.storage", ...) is a
# CHILD of this one, so configuring this logger configures all of them -
# and leaves other libraries' loggers (such as matplotlib's) alone.
PACKAGE_LOGGER = "expense_tracker"

# 2026-10-20 09:14:02 INFO     expense_tracker.tracker: Added expense #12
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# When the file reaches 1 MB it is renamed to .log.1 and a new one starts.
# Only 3 old files are kept, so the log can never fill your disk.
MAX_LOG_BYTES = 1_000_000
BACKUP_COUNT = 3


def setup_logging(log_file: Path, level: int | str = logging.INFO) -> None:
    """Send our package's log messages at ``level`` or above to ``log_file``.

    ``level`` can be a number (``logging.DEBUG``) or a name (``"DEBUG"``).
    """

    log_file.parent.mkdir(parents=True, exist_ok=True)  # create logs/ if needed

    handler = RotatingFileHandler(
        log_file, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )

    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    logger = logging.getLogger(PACKAGE_LOGGER)
    stop_logging()

    logger.addHandler(handler)
    logger.setLevel(level)


def stop_logging() -> None:
    """Stop sending our package's log messages to any file.

    This is useful in tests, so they don't create a log file.
    """

    logger = logging.getLogger(PACKAGE_LOGGER)
    for handler in logger.handlers:
        logger.removeHandler(handler)
        logger.close()  # close the file so other processes can read it
    logger.setLevel(logging.NOTSET)
