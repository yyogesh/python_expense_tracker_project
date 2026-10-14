import datetime as dt
import json
from decimal import Decimal

import pytest

from expense_tracker.tracker import ExpenseNotFoundError, ExpenseTracker

DAY = dt.date(2026, 9, 1)
TEN = Decimal("10.00")


def test_add_gives_increasing_ids(tracker):
    first = tracker.add(TEN, "Food", "a", DAY)
    second = tracker.add(Decimal("20.00"), "Food", "b", DAY)
    assert (first.id, second.id) == (1, 2)


def test_data_survives_restart(tmp_path):
    ExpenseTracker(tmp_path).add(Decimal("19.99"), "Food", "Lunch", DAY)
    reopened = ExpenseTracker(tmp_path)  # like closing and reopening the app
    assert len(reopened.expenses) == 1
    assert reopened.expenses[0].description == "Lunch"
    assert reopened.expenses[0].amount == Decimal("19.99")  # not 19.98999...


def test_update_changes_only_given_fields(tracker):
    expense = tracker.add(TEN, "Food", "Lunch", DAY)
    updated = tracker.update(expense.id, amount=Decimal("12.00"))
    assert updated.amount == Decimal("12.00")
    assert updated.description == "Lunch"
    assert tracker.get(expense.id) == updated


def test_update_cannot_change_id(tracker):
    expense = tracker.add(TEN, "Food", "Lunch", DAY)
    with pytest.raises(ValueError):
        tracker.update(expense.id, id=99)


def test_delete_removes_expense(tracker):
    expense = tracker.add(TEN, "Food", "Lunch", DAY)
    tracker.delete(expense.id)
    assert tracker.expenses == []


def test_missing_id_raises(tracker):
    with pytest.raises(ExpenseNotFoundError):
        tracker.get(42)
    with pytest.raises(ExpenseNotFoundError):
        tracker.delete(42)


def test_expenses_sorted_by_date(tracker):
    tracker.add(TEN, "Food", "later", dt.date(2026, 9, 5))
    tracker.add(TEN, "Food", "earlier", dt.date(2026, 9, 1))
    assert [e.description for e in tracker.expenses] == ["earlier", "later"]


def test_budget_setting(tmp_path):
    tracker = ExpenseTracker(tmp_path)
    assert tracker.monthly_budget is None
    tracker.set_monthly_budget(Decimal("300.00"))
    assert ExpenseTracker(tmp_path).monthly_budget == Decimal("300.00")
    tracker.set_monthly_budget(None)
    assert ExpenseTracker(tmp_path).monthly_budget is None


def test_version_1_budget_still_loads(tmp_path):
    # Version 1 saved the budget as a JSON number.
    (tmp_path / "settings.json").write_text(json.dumps({"monthly_budget": 500.0}))
    assert ExpenseTracker(tmp_path).monthly_budget == Decimal("500.00")
