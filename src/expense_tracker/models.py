"""Data models - what an expense *is*.

Why this file exists:
    Every other part of the app works with expenses. Defining the shape of an
    expense in one place means everyone agrees on it: an expense always has an
    id, amount, category, description and date.

Key idea - dataclasses:
    ``@dataclass`` writes ``__init__``, ``__repr__`` and ``__eq__`` for us, so a
    class that holds data needs only a list of fields.

Key idea - frozen=True:
    A frozen object cannot be changed after creation (it is *immutable*). To
    "edit" an expense we create a new one with ``dataclasses.replace``. This
    prevents a whole family of bugs where data changes somewhere unexpected.

Key idea - Decimal money:
    A float stores numbers in binary, so 0.1 + 0.2 is 0.30000000000000004.
    ``Decimal`` stores them in base 10, exactly like we write money. Every
    amount in the app is a ``Decimal`` with exactly two decimal places.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from expense_tracker.config import CENT


def to_money(value: Decimal | int | str) -> Decimal:
    """Round to whole cents the way people expect: 2.675 -> 2.68.

    ``quantize(CENT)`` means "keep exactly as many decimal places as CENT has"
    (two). ROUND_HALF_UP rounds a 5 upwards, like at school. Decimal's default
    is ROUND_HALF_EVEN ("banker's rounding"), which would give 2.665 -> 2.66.
    """
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Expense:
    """One spending record."""

    id: int
    amount: Decimal
    category: str
    description: str
    date: dt.date

    def __post_init__(self) -> None:
        """Runs right after the generated ``__init__``.

        Type hints are not checked by Python, so ``Expense(1, 9.5, ...)`` would
        quietly store a float. We refuse it here, loudly, so a float can never
        sneak back into the app.
        """
        if not isinstance(self.amount, Decimal):
            raise TypeError(
                f"amount must be a Decimal, not {type(self.amount).__name__}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain dictionary that can be saved as JSON.

        JSON does not understand ``date`` or ``Decimal`` objects, so we turn
        the date into text like "2026-09-23" and the amount into text like
        "12.50". Text keeps every digit exactly; a JSON number would not.
        """
        data = asdict(self)
        data["amount"] = str(self.amount)
        data["date"] = self.date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Expense:
        """Build an Expense from a dictionary loaded from JSON.

        ``@classmethod`` means we call it on the class itself:
        ``Expense.from_dict({...})``. It is an "alternative constructor".

        Version 1 files store amounts as JSON numbers (19.99), Version 2 files
        as text ("19.99"). ``str()`` first turns both into text, so old files
        still load exactly: Decimal("19.99"), never the inexact Decimal(19.99).
        """
        return cls(
            id=int(data["id"]),
            amount=to_money(str(data["amount"])),
            category=str(data["category"]),
            description=str(data.get("description", "")),
            date=dt.date.fromisoformat(data["date"]),
        )
