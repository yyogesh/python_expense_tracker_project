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
"""

from __future__ import annotations

# Treat my type hints as strings for now; don't try to evaluate them immediately.
import datetime as dt
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Expense:
    """One spending record."""

    id: int
    amount: float
    category: str
    description: str
    date: dt.date

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["date"] = data["date"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Expense:
        """Build an Expense from a dictionary loaded from JSON.

        ``@classmethod`` means we call it on the class itself:
        ``Expense.from_dict({...})``. It is an "alternative constructor".
        """
        return cls(
            id=int(data["id"]),
            amount=float(data["amount"]),
            category=str(data["category"]),
            description=str(data.get("description", "")),
            date=dt.date.fromisoformat(data["date"]),
        )
