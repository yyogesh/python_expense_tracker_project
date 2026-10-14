import dataclasses
import datetime as dt
from decimal import Decimal

import pytest

from expense_tracker.models import Expense, to_money

DAY = dt.date(2026, 9, 1)


def test_to_dict_turns_date_and_amount_into_text():
    expense = Expense(1, Decimal("9.50"), "Food", "Lunch", DAY)
    assert expense.to_dict() == {
        "id": 1,
        "amount": "9.50",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-09-01",
    }


def test_round_trip_through_dict():
    expense = Expense(7, Decimal("12.25"), "Health", "Pharmacy", dt.date(2026, 1, 31))
    assert Expense.from_dict(expense.to_dict()) == expense


def test_from_dict_allows_missing_description():
    data = {"id": 1, "amount": "3", "category": "Food", "date": "2026-09-01"}
    assert Expense.from_dict(data).description == ""


def test_from_dict_reads_version_1_float_amounts():
    # Version 1 saved amounts as JSON numbers; json.loads turns them into floats.
    data = {"id": 1, "amount": 19.99, "category": "Food", "date": "2026-09-01"}
    assert Expense.from_dict(data).amount == Decimal("19.99")


def test_expense_is_frozen():
    expense = Expense(1, Decimal("9.50"), "Food", "Lunch", DAY)
    with pytest.raises(dataclasses.FrozenInstanceError):
        expense.amount = Decimal("100")  # type: ignore[misc]


def test_float_amount_is_refused():
    with pytest.raises(TypeError):
        Expense(1, 9.5, "Food", "Lunch", DAY)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2.675", "2.68"), ("2.665", "2.67"), ("0.125", "0.13"), ("12", "12.00")],
)
def test_to_money_rounds_half_up(value, expected):
    assert to_money(value) == Decimal(expected)
    assert str(to_money(value)) == expected  # always two decimal places
