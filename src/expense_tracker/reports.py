from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from expense_tracker.config import BUDGET_WARNING_RATIO, MONTH_FORMAT
from expense_tracker.models import Expense


def total(expenses: Iterable[Expense]) -> float:
    """Return the total amount of a list of expenses."""
    return round(sum(expense.amount for expense in expenses), 2)


def average(expenses: Sequence[Expense]) -> float:
    if not expenses:
        return 0.0
    return round(total(expenses) / len(expenses), 2)


def largest(expenses: Iterable[Expense]) -> Expense | None:
    return max(expenses, key=lambda expense: expense.amount, default=None)


def filter_by_category(expenses: Iterable[Expense], category: str) -> list[Expense]:
    return [expense for expense in expenses if expense.category == category]


def filter_by_month(
    expenses: Iterable[Expense], year: int, month: int
) -> list[Expense]:
    return [
        expense
        for expense in expenses
        if expense.date.year == year and expense.date.month == month
    ]


def totals_by_category(expenses: Iterable[Expense]) -> dict[str, float]:
    """{"Food": 120.5, "Transport": 40.0, ...} - biggest first."""
    sums: defaultdict[str, float] = defaultdict(float)

    for expense in expenses:
        sums[expense.category] += expense.amount

    ordered = sorted(sums.items(), key=lambda item: item[1], reverse=True)

    return {category: round(amount, 2) for category, amount in ordered}


def totals_by_month(expenses: Iterable[Expense]) -> dict[str, float]:
    """{"2026-08": 300.0, "2026-09": 150.0} - oldest month first."""
    sums: defaultdict[str, float] = defaultdict(float)
    for expense in expenses:
        sums[expense.date.strftime(MONTH_FORMAT)] += expense.amount
    return {month: round(sums[month], 2) for month in sorted(sums)}


@dataclass(frozen=True)
class BudgetStatus:
    """How much of a monthly budget has been used."""

    budget: float
    spent: float

    @property
    def remaining(self) -> float:
        return round(self.budget - self.spent, 2)

    @property
    def ratio(self) -> float:
        """0.5 means half the budget is used; 1.2 means 20% over."""
        return self.spent / self.budget if self.budget else 0.0

    @property
    def level(self) -> str:
        """One of "ok", "warning" or "over"."""
        if self.ratio > 1:
            return "over"
        if self.ratio >= BUDGET_WARNING_RATIO:
            return "warning"
        return "ok"


def budget_status(
    expenses: Iterable[Expense], budget: float, year: int, month: int
) -> BudgetStatus:
    spent = total(filter_by_month(expenses, year, month))
    return BudgetStatus(budget=budget, spent=spent)
