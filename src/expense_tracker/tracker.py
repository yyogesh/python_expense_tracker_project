from __future__ import annotations

import datetime as dt
from dataclasses import replace
from pathlib import Path
from typing import Any

from expense_tracker.config import EXPENSES_FILE, SETTINGS_FILE
from expense_tracker.models import Expense
from expense_tracker.storage import (
    load_expenses,
    load_settings,
    save_expenses,
    save_settings,
)


class ExpenseNotFoundError(LookupError):
    """Raised when no expense has the requested ID."""


class ExpenseTracker:
    """Keeps expenses in memory and saves every change to disk."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._expenses_path = data_dir / EXPENSES_FILE
        self._settings_path = data_dir / SETTINGS_FILE
        self._expenses: list[Expense] = load_expenses(self._expenses_path)
        self._settings: dict[str, Any] = load_settings(self._settings_path)

    @property
    def expenses(self) -> list[Expense]:
        """All expenses, oldest first."""
        return sorted(self._expenses, key=lambda e: (e.date, e.id))

    def get(self, expense_id: int) -> Expense:
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        raise ExpenseNotFoundError(f"No expense with ID {expense_id}.")

    def add(
        self, amount: float, category: str, description: str, date: dt.date
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
        """Change fields of an expense, e.g. ``update(3, amount=9.99)``."""
        if "id" in changes:
            raise ValueError("The ID of an expense cannot be changed.")
        old = self.get(expense_id)
        new = replace(old, **changes)
        self._expenses[self._expenses.index(old)] = new
        self._save()
        return new

    def delete(self, expense_id: int) -> Expense:
        expense = self.get(expense_id)
        self._expenses.remove(expense)
        self._save()
        return expense

    @property
    def monthly_budget(self) -> float | None:
        value = self._settings.get("monthly_budget")
        return float(value) if value is not None else None

    def set_monthly_budget(self, amount: float | None) -> None:
        """Set the budget, or pass None to remove it."""
        if amount is None:
            self._settings.pop("monthly_budget", None)
        else:
            self._settings["monthly_budget"] = amount
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
