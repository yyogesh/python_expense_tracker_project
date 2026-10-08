import pytest

from expense_tracker import reports
from expense_tracker.reports import BudgetStatus


def test_total_and_average(sample_expenses):
    assert reports.total(sample_expenses) == 200.0
    assert reports.average(sample_expenses) == 50.0
    assert reports.average([]) == 0.0


def test_largest(sample_expenses):
    assert reports.largest(sample_expenses).description == "Repairs"
    assert reports.largest([]) is None


def test_filters(sample_expenses):
    assert len(reports.filter_by_category(sample_expenses, "Food")) == 2
    assert len(reports.filter_by_month(sample_expenses, 2026, 8)) == 2
    assert reports.filter_by_month(sample_expenses, 2025, 1) == []


def test_totals_by_category_biggest_first(sample_expenses):
    assert reports.totals_by_category(sample_expenses) == {
        "Housing": 100.0,
        "Food": 80.0,
        "Transport": 20.0,
    }


def test_totals_by_month(sample_expenses):
    assert reports.totals_by_month(sample_expenses) == {
        "2026-08": 70.0,
        "2026-09": 130.0,
    }


@pytest.mark.parametrize(
    ("spent", "level"), [(50, "ok"), (80, "warning"), (100, "warning"), (101, "over")]
)
def test_budget_levels(spent, level):
    assert BudgetStatus(budget=100, spent=spent).level == level


def test_budget_status_for_month(sample_expenses):
    status = reports.budget_status(sample_expenses, 150.0, 2026, 9)
    assert status.spent == 130.0
    assert status.remaining == 20.0
