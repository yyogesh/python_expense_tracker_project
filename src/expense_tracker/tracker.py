"""ExpenseTracker - the "brain" that manages expenses.

Why this file exists:
    The CLI should only talk to the user; storage should only read/write files.
    Something in the middle must hold the list of expenses, give out new IDs,
    and save after every change. That is this class.

    Because it never uses input() or print(), the same tracker could power a
    GUI or web app in Version 2 without changes.

Key idea - encapsulation:
    Attributes starting with ``_`` (like ``_expenses``) are "private by
    convention". Outside code uses the public methods (add, update, delete),
    so the tracker can guarantee data is always saved and IDs stay unique.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from expense_tracker.config import EXPENSES_FILE, SETTINGS_FILE
from expense_tracker.models import Expense, to_money
from expense_tracker.storage import (
    connect,
    delete_expense,
    get_expense,
    get_setting,
    insert_expense,
    load_expenses,
    migrate_from_json,
    set_setting,
    update_expense,
)


class ExpenseNotFoundError(LookupError):
    """Raised when no expense has the requested ID."""


class ExpenseTracker:
    """Keeps expenses in memory and saves every change to disk."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._expenses_path = data_dir / EXPENSES_FILE  # "/" joins paths
        self._settings_path = data_dir / SETTINGS_FILE
        self._expenses: list[Expense] = load_expenses(self._expenses_path)
        self._settings: dict[str, Any] = load_settings(self._settings_path)

    # -- Reading -----------------------------------------------------------

    @property
    def expenses(self) -> list[Expense]:
        """All expenses, oldest first.

        ``@property`` lets callers write ``tracker.expenses`` (no brackets).
        ``sorted`` returns a NEW list, so callers cannot accidentally modify
        our internal list.
        """
        return sorted(self._expenses, key=lambda e: (e.date, e.id))

    def get(self, expense_id: int) -> Expense:
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        raise ExpenseNotFoundError(f"No expense with ID {expense_id}.")

    # -- Changing ----------------------------------------------------------

    def add(
        self, amount: Decimal, category: str, description: str, date: dt.date
    ) -> Expense:
        expense = Expense(
            id=self._next_id(),
            amount=amount,
            category=category,
            description=description,
            date=date,
        )
        self._expenses.append(expense)
        self._save()
        return expense

    def update(self, expense_id: int, **changes: Any) -> Expense:
        """Change fields of an expense, e.g. ``update(3, amount=Decimal("9.99"))``.

        ``**changes`` collects keyword arguments into a dictionary.
        """
        if "id" in changes:
            raise ValueError("The ID of an expense cannot be changed.")
        old = self.get(expense_id)
        new = replace(old, **changes)  # frozen dataclass -> build a new object
        self._expenses[self._expenses.index(old)] = new
        self._save()
        return new

    def delete(self, expense_id: int) -> Expense:
        expense = self.get(expense_id)
        self._expenses.remove(expense)
        self._save()
        return expense

    # -- Budget setting ----------------------------------------------------

    @property
    def monthly_budget(self) -> Decimal | None:
        value = self._settings.get("monthly_budget")
        # str() first: Version 1 saved 500.0 (a number), Version 2 saves "500.00".
        return to_money(str(value)) if value is not None else None

    def set_monthly_budget(self, amount: Decimal | None) -> None:
        """Set the budget, or pass None to remove it."""
        if amount is None:
            self._settings.pop("monthly_budget", None)
        else:
            # json.dumps() cannot write a Decimal, so we save it as text.
            self._settings["monthly_budget"] = str(amount)
        save_settings(self._settings, self._settings_path)

    # -- Private helpers ---------------------------------------------------

    def _next_id(self) -> int:
        """Largest existing ID + 1.

        Simple and good enough for Version 1. (If the newest expense is
        deleted, its ID can be given out again - Version 2 fixes this.)
        """
        return max((e.id for e in self._expenses), default=0) + 1

    def _save(self) -> None:
        save_expenses(self._expenses, self._expenses_path)
