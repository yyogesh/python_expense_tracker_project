"""Reports - calculations and analysis on a list of expenses.

Why this file exists:
    "How much did I spend on food in September?" is a *question about data*,
    not about files or menus. Every function here receives expenses and
    returns an answer. Nothing is printed, so each function is easy to test
    and reuse (the CLI prints the results, the charts module draws them).

 Decimal everywhere:
    Every amount coming in is a Decimal, so every answer going out is a
    Decimal too. Adding Decimals is exact, so we only round where a division
    can create more than two decimal places (the average).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from expense_tracker.config import BUDGET_WARNING_RATIO, MONTH_FORMAT
from expense_tracker.models import Expense, to_money

ZERO = Decimal("0.00")


def total(expenses: Iterable[Expense]) -> Decimal:
    # sum() starts at the int 0, so sum([]) would be 0, not a Decimal.
    # The second argument gives sum() a Decimal to start from instead.
    return sum((expense.amount for expense in expenses), ZERO)


def average(expenses: Sequence[Expense]) -> Decimal:
    if not expenses:
        return ZERO
    # Division CAN produce many decimal places (10 / 3), so round here.
    return to_money(total(expenses) / len(expenses))


def largest(expenses: Iterable[Expense]) -> Expense | None:
    # default=None avoids an error when the list is empty.
    return max(expenses, key=lambda expense: expense.amount, default=None)


def filter_by_category(expenses: Iterable[Expense], category: str) -> list[Expense]:
    # A list comprehension: build a new list from items that pass a test.
    return [expense for expense in expenses if expense.category == category]


def filter_by_month(
    expenses: Iterable[Expense], year: int, month: int
) -> list[Expense]:
    return [
        expense
        for expense in expenses
        if expense.date.year == year and expense.date.month == month
    ]


def totals_by_category(expenses: Iterable[Expense]) -> dict[str, Decimal]:
    """{"Food": Decimal("120.50"), "Transport": Decimal("40.00"), ...}.

    Biggest first. Like float() gives 0.0, Decimal() gives Decimal("0"), so
    defaultdict(Decimal) starts every new key at zero and += just works.
    """
    sums: defaultdict[str, Decimal] = defaultdict(Decimal)
    for expense in expenses:
        sums[expense.category] += expense.amount
    # No round() needed any more: adding Decimals never creates extra digits.
    return dict(sorted(sums.items(), key=lambda item: item[1], reverse=True))


def totals_by_month(expenses: Iterable[Expense]) -> dict[str, Decimal]:
    """{"2026-08": Decimal("300.00"), ...} - oldest month first."""
    sums: defaultdict[str, Decimal] = defaultdict(Decimal)
    for expense in expenses:
        sums[expense.date.strftime(MONTH_FORMAT)] += expense.amount
    return {month: sums[month] for month in sorted(sums)}


@dataclass(frozen=True)
class BudgetStatus:
    """How much of a monthly budget has been used."""

    budget: Decimal
    spent: Decimal

    @property
    def remaining(self) -> Decimal:
        return self.budget - self.spent  # exact, no rounding needed

    @property
    def ratio(self) -> Decimal:
        """0.5 means half the budget is used; 1.2 means 20% over.

        A Decimal, so spending exactly 80% gives exactly 0.8. With floats,
        9.60 / 12 is 0.7999999999999999 and the warning never showed.
        """
        return self.spent / self.budget if self.budget else Decimal(0)

    @property
    def level(self) -> str:
        """One of "ok", "warning" or "over"."""
        if self.ratio > 1:
            return "over"
        if self.ratio >= BUDGET_WARNING_RATIO:
            return "warning"
        return "ok"


def budget_status(
    expenses: Iterable[Expense], budget: Decimal, year: int, month: int
) -> BudgetStatus:
    spent = total(filter_by_month(expenses, year, month))
    return BudgetStatus(budget=budget, spent=spent)
