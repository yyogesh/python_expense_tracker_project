import datetime as dt
from decimal import Decimal

import pytest

from expense_tracker import reports
from expense_tracker.models import Expense
from expense_tracker.reports import BudgetStatus

DAY = dt.date(2026, 9, 1)


def test_total_and_average(sample_expenses):
    assert reports.total(sample_expenses) == Decimal("200.00")
    assert reports.average(sample_expenses) == Decimal("50.00")
    assert reports.total([]) == Decimal("0.00")
    assert reports.average([]) == Decimal("0.00")


def test_total_is_exact():
    # With floats, 0.10 + 0.20 is 0.30000000000000004.
    expenses = [
        Expense(1, Decimal("0.10"), "Food", "", DAY),
        Expense(2, Decimal("0.20"), "Food", "", DAY),
    ]
    assert reports.total(expenses) == Decimal("0.30")


def test_average_rounds_to_cents():
    expenses = [Expense(i, Decimal("10.00"), "Food", "", DAY) for i in (1, 2, 3)]
    expenses.append(Expense(4, Decimal("0.01"), "Food", "", DAY))
    # 30.01 / 4 = 7.5025 -> 7.50
    assert reports.average(expenses) == Decimal("7.50")


def test_largest(sample_expenses):
    assert reports.largest(sample_expenses).description == "Repairs"
    assert reports.largest([]) is None


def test_filters(sample_expenses):
    assert len(reports.filter_by_category(sample_expenses, "Food")) == 2
    assert len(reports.filter_by_month(sample_expenses, 2026, 8)) == 2
    assert reports.filter_by_month(sample_expenses, 2025, 1) == []


def test_totals_by_category_biggest_first(sample_expenses):
    assert reports.totals_by_category(sample_expenses) == {
        "Housing": Decimal("100.00"),
        "Food": Decimal("80.00"),
        "Transport": Decimal("20.00"),
    }


def test_totals_by_month(sample_expenses):
    assert reports.totals_by_month(sample_expenses) == {
        "2026-08": Decimal("70.00"),
        "2026-09": Decimal("130.00"),
    }


@pytest.mark.parametrize(
    ("spent", "level"),
    [("50", "ok"), ("80", "warning"), ("100", "warning"), ("100.01", "over")],
)
def test_budget_levels(spent, level):
    assert BudgetStatus(budget=Decimal("100"), spent=Decimal(spent)).level == level


def test_budget_warning_at_exactly_80_percent():
    # With floats, 9.60 / 12 is 0.7999999999999999 and this said "ok".
    status = BudgetStatus(budget=Decimal("12.00"), spent=Decimal("9.60"))
    assert status.ratio == Decimal("0.8")
    assert status.level == "warning"


def test_budget_status_for_month(sample_expenses):
    status = reports.budget_status(sample_expenses, Decimal("150.00"), 2026, 9)
    assert status.spent == Decimal("130.00")
    assert status.remaining == Decimal("20.00")
