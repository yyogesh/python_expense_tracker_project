"""Shared test setup.

pytest automatically loads this file. A *fixture* is a function that
prepares something a test needs. A test asks for it simply by using the
fixture's name as a parameter:

    def test_something(sample_expenses): ...

Note: the ``tracker`` fixture is added in Lesson 5, once ExpenseTracker exists.
"""

import datetime as dt

import pytest

from expense_tracker.models import Expense
from expense_tracker.tracker import ExpenseTracker


@pytest.fixture
def sample_expenses() -> list[Expense]:
    return [
        Expense(1, 50.0, "Food", "Groceries", dt.date(2026, 8, 5)),
        Expense(2, 20.0, "Transport", "Bus pass", dt.date(2026, 8, 10)),
        Expense(3, 30.0, "Food", "Restaurant", dt.date(2026, 9, 1)),
        Expense(4, 100.0, "Housing", "Repairs", dt.date(2026, 9, 3)),
    ]


@pytest.fixture
def tracker(tmp_path) -> ExpenseTracker:
    """A tracker using a temporary folder.

    ``tmp_path`` is a built-in pytest fixture: a fresh empty folder for each
    test, deleted afterwards. Tests never touch your real data.
    """
    return ExpenseTracker(tmp_path)
