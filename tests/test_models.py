import dataclasses
import datetime as dt

import pytest

from expense_tracker.models import Expense


def test_to_dict_turns_date_into_text():
    expense = Expense(1, 9.5, "Food", "Lunch", dt.date(2026, 9, 1))
    assert expense.to_dict()["date"] == "2026-09-01"
    assert expense.to_dict() == {
        "id": 1,
        "amount": 9.5,
        "category": "Food",
        "description": "Lunch",
        "date": "2026-09-01",
    }


def test_round_trip_through_dict():
    expense = Expense(7, 12.25, "Health", "Pharmacy", dt.date(2026, 1, 31))
    assert Expense.from_dict(expense.to_dict()) == expense


def test_from_dict_allows_missing_description():
    data = {"id": 1, "amount": 3, "category": "Food", "date": "2026-09-01"}
    assert Expense.from_dict(data).description == ""


def test_expense_is_frozen():
    expense = Expense(1, 9.5, "Food", "Lunch", dt.date(2026, 9, 1))
    with pytest.raises(dataclasses.FrozenInstanceError):
        expense.id = 2
