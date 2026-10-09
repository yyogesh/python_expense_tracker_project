"""Command-line interface - everything the user sees and types."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from expense_tracker import reports
from expense_tracker.config import CATEGORIES, CURRENCY
from expense_tracker.models import Expense
from expense_tracker.validators import ValidationError

# def say_hello(name: str) -> str:
#     return f"Hello, {name}!"

# def execute_action(action: Callable[[str], str]) -> None:
#     result = action("Yogesh")
#     print(result)

# execute_action(say_hello)


# def get_first_number(items: list[int]) -> int:
#     return items[0]


# def get_first_string(items: list[str]) -> str:
#     return items[0]


# T = TypeVar("T")

# def get_first(items: list[T]) -> T:
#     return items[0]

# number = get_first([10, 20, 30])
# name = get_first(["Yogesh", "Amit", "Rahul"])


T = TypeVar("T")


def money(amount: float) -> str:
    """12345.5 -> "$12,345.50"."""
    return f"{CURRENCY}{amount:,.2f}"


def ask(prompt: str, parser: Callable[[str], T]) -> T:
    """Ask a question until the answer is valid."""
    while True:
        text = input(prompt)
        try:
            return parser(text)
        except ValidationError as error:
            print(f"  ! {error}")


# ask("Enter a number: ", parse_amount)


def ask_with_default(prompt: str, parser: Callable[[str], T], default: T) -> T:
    """Like ask(), but pressing Enter keeps ``default`` (used when editing)."""
    while True:
        text = input(prompt)
        if not text.strip():
            return default
        try:
            return parser(text)
        except ValidationError as error:
            print(f"  ! {error}")


def confirm(prompt: str) -> bool:
    return input(f"{prompt} (y/n): ").strip().lower() in ("y", "yes")


def print_categories() -> None:
    # enumerate(..., start=1) gives (1, "Food"), (2, "Transport"), ...
    options = ", ".join(f"{i}={name}" for i, name in enumerate(CATEGORIES, start=1))
    print(f"  Categories: {options}")


def print_expenses(expenses: list[Expense]) -> None:
    """Print expenses as a neat table using f-string alignment.

    ``:>4`` = right-align in 4 characters, ``:<10`` = left-align in 10.
    """
    if not expenses:
        print("  No expenses found.")
        return
    header = f"  {'ID':>4}  {'Date':<10}  {'Category':<13}  {'Amount':>12}  Description"
    print(header)
    print("  " + "-" * (len(header) + 10))
    for e in expenses:
        print(
            f"  {e.id:>4}  {e.date.isoformat():<10}  {e.category:<13}  "
            f"{money(e.amount):>12}  {e.description}"
        )
    print(f"  {len(expenses)} expense(s), total {money(reports.total(expenses))}")


#     ID  Date        Category             Amount  Description
#   ----------------------------------------------------------------------
#      1  2026-09-02  Food                 $45.20  Groceries
#      2  2026-09-03  Housing           $1,250.00  Rent
#   2 expense(s), total $1,295.20


def text_bar(ratio: float, width: int = 20) -> str:
    """A tiny bar chart made of characters: [#####-----]."""
    filled = round(min(ratio, 1.0) * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


# Housing   $380.00  [#################---] 86%
