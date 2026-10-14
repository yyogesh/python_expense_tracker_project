"""Shared test setup.

pytest automatically loads this file. A *fixture* is a function that
prepares something a test needs. A test asks for it simply by using the
fixture's name as a parameter:

    def test_something(sample_expenses): ...
"""

import datetime as dt
from decimal import Decimal

import pytest

from expense_tracker.models import Expense
from expense_tracker.tracker import ExpenseTracker


@pytest.fixture
def sample_expenses() -> list[Expense]:
    return [
        Expense(1, Decimal("50.00"), "Food", "Groceries", dt.date(2026, 8, 5)),
        Expense(2, Decimal("20.00"), "Transport", "Bus pass", dt.date(2026, 8, 10)),
        Expense(3, Decimal("30.00"), "Food", "Restaurant", dt.date(2026, 9, 1)),
        Expense(4, Decimal("100.00"), "Housing", "Repairs", dt.date(2026, 9, 3)),
    ]


@pytest.fixture
def tracker(tmp_path) -> ExpenseTracker:
    """A tracker using a temporary folder.

    ``tmp_path`` is a built-in pytest fixture: a fresh empty folder for each
    test, deleted afterwards. Tests never touch your real data.
    """
    return ExpenseTracker(tmp_path)
