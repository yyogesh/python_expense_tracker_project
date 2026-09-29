"""Settings and constants used across the whole app.

Why this file exists:
    If the list of categories were typed inside five different files, changing
    it would mean hunting through all of them. Keeping every "magic value" here
    gives us ONE place to change things.

Convention:
    Names in UPPER_CASE are constants - values the program never changes while
    running.
"""

import os
from pathlib import Path

# Folder where data files are stored.
# os.environ.get() reads an environment variable if it is set, otherwise uses
# the default "data". This lets a user store data elsewhere without editing code.
DATA_DIR = Path(os.environ.get("EXPENSE_TRACKER_DATA_DIR", "data"))


EXPENSES_FILE = "expenses.json"
SETTINGS_FILE = "settings.json"
EXPORT_FILE = "expenses_export.csv"
CHARTS_DIR = "charts"


CATEGORIES: tuple[str, ...] = (
    "Food",
    "Transport",
    "Housing",
    "Utilities",
    "Health",
    "Entertainment",
    "Shopping",
    "Education",
    "Other",
)

DATE_FORMAT = "%Y-%m-%d"  # e.g. 2026-09-23 (ISO format, sorts correctly as text)
MONTH_FORMAT = "%Y-%m"  # e.g. 2026-09
CURRENCY = "$"


MAX_AMOUNT = 1_000_000  # underscores make big numbers readable
MAX_DESCRIPTION_LENGTH = 100

# Warn the user when they have spent this share of their monthly budget.
BUDGET_WARNING_RATIO = 0.8
