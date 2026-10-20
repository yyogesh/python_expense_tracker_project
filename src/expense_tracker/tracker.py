"""ExpenseTracker - the "brain" that manages expenses.

Why this file exists:
    The CLI should only talk to the user; storage should only read/write files.
    Something in the middle must turn user actions into storage calls and
    report problems such as a missing ID. That is this class.

    Because it never uses input() or print(), the same tracker could power a
    GUI or web app in Version 2 without changes.

Key idea - encapsulation:
    Attributes starting with ``_`` (like ``_conn``) are "private by
    convention". Outside code uses the public methods (add, update, delete),
    so the tracker can guarantee every change is saved.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from expense_tracker.config import DATABASE_FILE, EXPENSES_FILE, SETTINGS_FILE
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
    """Reads and writes expenses through the SQLite database."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._conn = connect(data_dir / DATABASE_FILE)  # "/" joins paths
        # Version 1 kept data in JSON files: move it into the database once.
        try:
            self.imported = migrate_from_json(
                self._conn, data_dir / EXPENSES_FILE, data_dir / SETTINGS_FILE
            )
        except Exception:
            self._conn.close()
            raise

    def close(self) -> None:
        self._conn.close()

    # with block __enter__ and __exit__ lets callers write:

    def __enter__(self) -> ExpenseTracker:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -- Reading -----------------------------------------------------------

    @property
    def expenses(self) -> list[Expense]:
        """All expenses, oldest first.

        ``@property`` lets callers write ``tracker.expenses`` (no brackets).
        """
        return load_expenses(self._conn)

    def get(self, expense_id: int) -> Expense:
        expense = get_expense(self._conn, expense_id)
        if expense is None:
            raise ExpenseNotFoundError(f"No expense with ID {expense_id}.")
        return expense

    # -- Changing ----------------------------------------------------------

    def add(
        self, amount: Decimal, category: str, description: str, date: dt.date
    ) -> Expense:
        # The database chooses the ID and never gives it out again.
        return insert_expense(self._conn, amount, category, description, date)

    def update(self, expense_id: int, **changes: Any) -> Expense:
        """Change fields of an expense, e.g. ``update(3, amount=Decimal("9.99"))``.

        ``**changes`` collects keyword arguments into a dictionary.
        """
        if "id" in changes:
            raise ValueError("The ID of an expense cannot be changed.")
        old = self.get(expense_id)
        new = replace(old, **changes)  # frozen dataclass -> build a new object
        update_expense(self._conn, new)
        return new

    def delete(self, expense_id: int) -> Expense:
        expense = self.get(expense_id)
        delete_expense(self._conn, expense_id)
        return expense

    # -- Budget setting ----------------------------------------------------

    @property
    def monthly_budget(self) -> Decimal | None:
        value = get_setting(self._conn, "monthly_budget")
        # Version 1 saved 500.0 (a number), which was migrated as "500.0".
        return to_money(value) if value is not None else None

    def set_monthly_budget(self, amount: Decimal | None) -> None:
        """Set the budget, or pass None to remove it."""
        value = None if amount is None else str(amount)
        set_setting(self._conn, "monthly_budget", value)
