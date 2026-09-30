from __future__ import annotations

import datetime as dt
import math

from expense_tracker.config import (
    CATEGORIES,
    CURRENCY,
    DATE_FORMAT,
    MAX_AMOUNT,
    MAX_DESCRIPTION_LENGTH,
    MONTH_FORMAT,
)


class ValidationError(ValueError):
    """Raised when user input is invalid. The message is shown to the user.

    We create our own exception type so the CLI can catch *only* validation
    problems and let real bugs crash loudly (which is what we want while
    learning - hidden bugs are the worst kind).
    """


def parse_amount(text: str) -> float:
    """Convert text like "12.50", "$1,200" into a positive float."""
    cleaned = text.strip().replace(",", "")
    cleaned = cleaned.removeprefix(CURRENCY).removesuffix(".").strip()

    if not cleaned:
        raise ValidationError("Amount cannot be empty.")

    try:
        value = float(cleaned)
    except ValueError:
        # "from None" hides the original technical error from the traceback.
        raise ValidationError(f"'{text.strip()}' is not a number.") from None
    # float() happily accepts "nan" and "inf" - we must reject them ourselves.
    if not math.isfinite(value):
        raise ValidationError("Amount must be a real number.")
    if value <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if value > MAX_AMOUNT:
        raise ValidationError(f"Amount must be at most {MAX_AMOUNT:,}.")
    return round(value, 2)


def parse_category(text: str) -> str:
    """Accept a category number ("1") or name ("food", any case)."""
    cleaned = text.strip()
    if cleaned.isdigit():
        index = int(cleaned)
        if 1 <= index <= len(CATEGORIES):
            return CATEGORIES[index - 1]  # users count from 1, lists from 0
        raise ValidationError(f"Choose a number from 1 to {len(CATEGORIES)}.")
    for category in CATEGORIES:
        if category.lower() == cleaned.lower():
            return category
    raise ValidationError(f"Unknown category '{cleaned}'.")


def parse_description(text: str) -> str:
    """Descriptions are optional, but not too long."""
    cleaned = text.strip()
    if len(cleaned) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
        )
    return cleaned


def parse_date(text: str, *, today: dt.date | None = None) -> dt.date:
    """Convert "YYYY-MM-DD" to a date. Empty input means today.
    name = value
    The ``*`` makes ``today`` keyword-only. Tests pass a fixed ``today`` so
    results never depend on the day the tests happen to run.
    """
    today = today or dt.date.today()
    cleaned = text.strip()
    if not cleaned:
        return today
    try:
        parsed = dt.datetime.strptime(cleaned, DATE_FORMAT).date()
    except ValueError:
        raise ValidationError("Date must look like 2026-09-23 (YYYY-MM-DD).") from None
    if parsed > today:
        raise ValidationError("Date cannot be in the future.")
    return parsed


# def parse_date(text: str, today: dt.date | None = None):

# parse_date("2026-09-30")
# parse_date("2026-09-30", dt.date(2026, 9, 29))

# def parse_date(text: str, *, today: dt.date | None = None):
# parse_date("2026-09-30")
# # parse_date("2026-09-30", today=dt.date(2026, 9, 29))


def parse_positive_int(text: str) -> int:
    """Used for expense IDs."""
    cleaned = text.strip()
    if not cleaned.isdigit() or int(cleaned) == 0:
        raise ValidationError("Please enter a positive whole number.")
    return int(cleaned)


def parse_month(text: str, *, today: dt.date | None = None) -> tuple[int, int]:
    """Convert "YYYY-MM" to (year, month). Empty input means this month."""
    today = today or dt.date.today()
    cleaned = text.strip()
    if not cleaned:
        return today.year, today.month
    try:
        parsed = dt.datetime.strptime(cleaned, MONTH_FORMAT)
    except ValueError:
        raise ValidationError("Month must look like 2026-09 (YYYY-MM).") from None
    return parsed.year, parsed.month
