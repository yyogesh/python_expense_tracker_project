"""Input validation - turning raw text from the user into safe, typed values.

Why this file exists:
    ``input()`` always returns a string, and users type anything: "abc",
    "-5", "", "12,50", "tomorrow". Each function here takes that raw text and
    either returns a clean value or raises ``ValidationError`` with a friendly
    message. The CLI shows the message and asks again.

Why separate from cli.py?
    These functions do not print or read anything, so they are easy to test:
    ``parse_amount("12.5") == Decimal("12.50")``. That is the idea of *pure
    functions*.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal, InvalidOperation

from expense_tracker.config import (
    CATEGORIES,
    CURRENCY,
    DATE_FORMAT,
    MAX_AMOUNT,
    MAX_DESCRIPTION_LENGTH,
    MONTH_FORMAT,
)
from expense_tracker.models import to_money


class ValidationError(ValueError):
    """Raised when user input is invalid. The message is shown to the user.

    We create our own exception type so the CLI can catch *only* validation
    problems and let real bugs crash loudly (which is what we want while
    learning - hidden bugs are the worst kind).
    """


def parse_amount(text: str) -> Decimal:
    """Convert text like "12.50", "$1,200" into a positive Decimal in cents.

    The user typed TEXT, so we build the Decimal straight from that text and
    never go through float: "19.99" stays exactly 19.99.
    """
    cleaned = text.strip().replace(",", "").removeprefix(CURRENCY).strip()
    if not cleaned:
        raise ValidationError("Amount cannot be empty.")
    try:
        value = Decimal(cleaned)
    # Decimal raises InvalidOperation, which is NOT a ValueError. Catching
    # ValueError here (as we did with float) would let "abc" crash the app.
    except InvalidOperation:
        # "from None" hides the original technical error from the traceback.
        raise ValidationError(f"'{text.strip()}' is not a number.") from None
    # Decimal, like float, accepts "nan" and "inf" - we must reject them.
    if not value.is_finite():
        raise ValidationError("Amount must be a real number.")
    if value > MAX_AMOUNT:
        raise ValidationError(f"Amount must be at most {MAX_AMOUNT:,}.")
    amount = to_money(value)
    # Check AFTER rounding: "0.001" is positive, but rounds to 0.00.
    if amount <= 0:
        raise ValidationError("Amount must be at least 0.01.")
    return amount


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


def parse_positive_int(text: str) -> int:
    """Used for expense IDs."""
    cleaned = text.strip()
    if not cleaned.isdigit() or int(cleaned) == 0:
        raise ValidationError("Please enter a positive whole number.")
    return int(cleaned)
