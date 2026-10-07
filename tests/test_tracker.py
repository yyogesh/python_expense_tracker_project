import datetime as dt

import pytest

from expense_tracker.tracker import ExpenseNotFoundError, ExpenseTracker

DAY = dt.date(2026, 9, 1)


def test_add_gives_increasing_ids(tracker):
    first = tracker.add(10.0, "Food", "a", DAY)
    second = tracker.add(20.0, "Food", "b", DAY)
    assert (first.id, second.id) == (1, 2)


def test_data_survives_restart(tmp_path):
    ExpenseTracker(tmp_path).add(10.0, "Food", "Lunch", DAY)
    reopened = ExpenseTracker(tmp_path)  # like closing and reopening the app
    assert len(reopened.expenses) == 1
    assert reopened.expenses[0].description == "Lunch"


def test_update_changes_only_given_fields(tracker):
    expense = tracker.add(10.0, "Food", "Lunch", DAY)
    updated = tracker.update(expense.id, amount=12.0)
    assert updated.amount == 12.0
    assert updated.description == "Lunch"
    assert tracker.get(expense.id) == updated


def test_update_cannot_change_id(tracker):
    expense = tracker.add(10.0, "Food", "Lunch", DAY)
    with pytest.raises(ValueError):
        tracker.update(expense.id, id=99)


def test_delete_removes_expense(tracker):
    expense = tracker.add(10.0, "Food", "Lunch", DAY)
    tracker.delete(expense.id)
    assert tracker.expenses == []


def test_missing_id_raises(tracker):
    with pytest.raises(ExpenseNotFoundError):
        tracker.get(42)
    with pytest.raises(ExpenseNotFoundError):
        tracker.delete(42)


def test_expenses_sorted_by_date(tracker):
    tracker.add(1.0, "Food", "later", dt.date(2026, 9, 5))
    tracker.add(2.0, "Food", "earlier", dt.date(2026, 9, 1))
    assert [e.description for e in tracker.expenses] == ["earlier", "later"]


def test_budget_setting(tmp_path):
    tracker = ExpenseTracker(tmp_path)
    assert tracker.monthly_budget is None
    tracker.set_monthly_budget(300.0)
    assert ExpenseTracker(tmp_path).monthly_budget == 300.0
    tracker.set_monthly_budget(None)
    assert ExpenseTracker(tmp_path).monthly_budget is None
