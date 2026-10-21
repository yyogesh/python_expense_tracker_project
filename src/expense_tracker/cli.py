"""Command-line interface - everything the user sees and types.

Why this file exists:
    This is the ONLY file that uses ``input()`` and ``print()``. It shows the
    menu, asks questions, and calls the tracker/reports/charts to do the real
    work. Keeping user interaction in one place means Version 2 could add a GUI
    or web page without touching the logic files.

Flow of the program:
    main() -> creates ExpenseTracker -> run() shows the menu in a loop ->
    each menu choice calls one small function (add_expense, show_summary...).
"""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Callable
from decimal import Decimal
from typing import TypeVar

from expense_tracker import __version__, reports
from expense_tracker.app_config import ConfigError, load_config
from expense_tracker.charts import ChartError, save_category_pie, save_monthly_bar
from expense_tracker.config import (
    CATEGORIES,
    CHARTS_DIR,
    CURRENCY,
    DATA_DIR,
    EXPORT_FILE,
)
from expense_tracker.logging_config import setup_logging
from expense_tracker.models import Expense
from expense_tracker.storage import StorageError, export_to_csv
from expense_tracker.tracker import ExpenseNotFoundError, ExpenseTracker
from expense_tracker.validators import (
    ValidationError,
    parse_amount,
    parse_category,
    parse_date,
    parse_description,
    parse_month,
    parse_positive_int,
)

logger = logging.getLogger(__name__)

# T is a "type variable": ask() returns whatever type its parser returns.
T = TypeVar("T")

# ===========================================================================
# Small helpers for input and output
# ===========================================================================


def money(amount: Decimal) -> str:
    """Decimal("12345.5") -> "$12,345.50". Decimal understands :,.2f too."""
    return f"{CURRENCY}{amount:,.2f}"


def ask(prompt: str, parser: Callable[[str], T]) -> T:
    """Ask a question until the answer is valid.

    ``parser`` is a function (for example ``parse_amount``). Passing functions
    as arguments lets ONE loop handle every kind of question.
    """
    while True:
        text = input(prompt)
        try:
            return parser(text)
        except ValidationError as error:
            print(f"  ! {error}")


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


def text_bar(ratio: float | Decimal, width: int = 20) -> str:
    """A tiny bar chart made of characters: [#####-----]."""
    # float() is fine here: a bar of # characters does not need exact cents.
    filled = round(min(float(ratio), 1.0) * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


# ===========================================================================
# Menu actions - one function per menu option
# ===========================================================================


def add_expense(tracker: ExpenseTracker) -> None:
    print("\nAdd a new expense")
    amount = ask("  Amount: ", parse_amount)
    print_categories()
    category = ask("  Category (number or name): ", parse_category)
    description = ask("  Description (optional): ", parse_description)
    date = ask("  Date YYYY-MM-DD (Enter = today): ", parse_date)

    expense = tracker.add(amount, category, description, date)
    print(f"  Saved expense #{expense.id}: {money(expense.amount)} on {category}.")
    warn_about_budget(tracker, expense.date)


def view_expenses(tracker: ExpenseTracker) -> None:
    print("\nAll expenses")
    print_expenses(tracker.expenses)


def edit_expense(tracker: ExpenseTracker) -> None:
    print("\nEdit an expense")
    expense_id = ask("  ID of the expense to edit: ", parse_positive_int)
    current = tracker.get(expense_id)  # raises ExpenseNotFoundError if missing
    print("  Press Enter to keep the value shown in [brackets].")

    amount = ask_with_default(
        f"  Amount [{money(current.amount)}]: ", parse_amount, current.amount
    )
    print_categories()
    category = ask_with_default(
        f"  Category [{current.category}]: ", parse_category, current.category
    )
    description = ask_with_default(
        f"  Description [{current.description}]: ",
        parse_description,
        current.description,
    )
    date = ask_with_default(f"  Date [{current.date}]: ", parse_date, current.date)

    tracker.update(
        expense_id,
        amount=amount,
        category=category,
        description=description,
        date=date,
    )
    print(f"  Expense #{expense_id} updated.")


def delete_expense(tracker: ExpenseTracker) -> None:
    print("\nDelete an expense")
    expense_id = ask("  ID of the expense to delete: ", parse_positive_int)
    expense = tracker.get(expense_id)
    print_expenses([expense])
    if confirm("  Are you sure?"):
        tracker.delete(expense_id)
        print(f"  Expense #{expense_id} deleted.")
    else:
        print("  Cancelled.")


def filter_by_category(tracker: ExpenseTracker) -> None:
    print("\nFilter by category")
    print_categories()
    category = ask("  Category (number or name): ", parse_category)
    print_expenses(reports.filter_by_category(tracker.expenses, category))


def filter_by_month(tracker: ExpenseTracker) -> None:
    print("\nFilter by month")
    year, month = ask("  Month YYYY-MM (Enter = this month): ", parse_month)
    print_expenses(reports.filter_by_month(tracker.expenses, year, month))


def show_summary(tracker: ExpenseTracker) -> None:
    expenses = tracker.expenses
    print("\nSummary report")
    if not expenses:
        print("  No expenses yet.")
        return

    grand_total = reports.total(expenses)
    biggest = reports.largest(expenses)
    print(f"  Total spent:      {money(grand_total)}")
    print(f"  Number of items:  {len(expenses)}")
    print(f"  Average expense:  {money(reports.average(expenses))}")
    if biggest is not None:
        print(
            f"  Largest expense:  {money(biggest.amount)} "
            f"({biggest.category}, {biggest.date})"
        )

    print("\n  By category:")
    for category, amount in reports.totals_by_category(expenses).items():
        share = amount / grand_total
        print(f"    {category:<13} {money(amount):>12}  {text_bar(share)} {share:.0%}")

    print("\n  By month:")
    for month, amount in reports.totals_by_month(expenses).items():
        print(f"    {month:<13} {money(amount):>12}")

    today = dt.date.today()
    warn_about_budget(tracker, today, always_show=True)


def set_budget(tracker: ExpenseTracker) -> None:
    print("\nMonthly budget")
    current = tracker.monthly_budget
    print(f"  Current budget: {money(current) if current else 'not set'}")

    def parse_budget(text: str) -> Decimal | None:
        """A parser defined inside a function: 0 or Enter removes the budget."""
        if text.strip() in ("", "0"):
            return None
        return parse_amount(text)

    budget = ask("  New monthly budget (0 or Enter = remove): ", parse_budget)
    tracker.set_monthly_budget(budget)
    print(f"  Budget {'set to ' + money(budget) if budget else 'removed'}.")


def warn_about_budget(
    tracker: ExpenseTracker, day: dt.date, *, always_show: bool = False
) -> None:
    """Print a warning if spending in ``day``'s month is near or over budget."""
    budget = tracker.monthly_budget
    if budget is None:
        return
    status = reports.budget_status(tracker.expenses, budget, day.year, day.month)
    month = day.strftime("%Y-%m")
    if status.level == "over":
        print(f"  !! OVER BUDGET for {month} by {money(-status.remaining)}.")
    elif status.level == "warning":
        print(
            f"  ! Careful: {status.ratio:.0%} of your {month} budget used, "
            f"{money(status.remaining)} left."
        )
    elif always_show:
        print(
            f"\n  Budget {month}: {money(status.spent)} of {money(budget)} "
            f"{text_bar(status.ratio)} {money(status.remaining)} left."
        )


def export_csv(tracker: ExpenseTracker) -> None:
    path = tracker.data_dir / EXPORT_FILE
    count = export_to_csv(tracker.expenses, path)
    print(f"\n  Exported {count} expense(s) to {path}")


def create_charts(tracker: ExpenseTracker) -> None:
    charts_dir = tracker.data_dir / CHARTS_DIR
    pie = save_category_pie(tracker.expenses, charts_dir / "by_category.png")
    bar = save_monthly_bar(tracker.expenses, charts_dir / "by_month.png")
    print(f"\n  Charts saved:\n    {pie}\n    {bar}")


# ===========================================================================
# Menu and main loop
# ===========================================================================

# A "dispatch dictionary": maps what the user types to (label, function).
# Adding a new feature = write a function + add ONE line here.
# No long if/elif chain needed.
MENU: dict[str, tuple[str, Callable[[ExpenseTracker], None]]] = {
    "1": ("Add expense", add_expense),
    "2": ("View all expenses", view_expenses),
    "3": ("Edit expense", edit_expense),
    "4": ("Delete expense", delete_expense),
    "5": ("Filter by category", filter_by_category),
    "6": ("Filter by month", filter_by_month),
    "7": ("Summary report", show_summary),
    "8": ("Set monthly budget", set_budget),
    "9": ("Export to CSV", export_csv),
    "10": ("Create charts", create_charts),
}


def print_menu() -> None:
    print("\n========== Expense Tracker ==========")
    for key, (label, _action) in MENU.items():
        print(f"  {key:>2}. {label}")
    print("   0. Exit")


def run(tracker: ExpenseTracker) -> None:
    """The main loop: show menu, run the chosen action, repeat."""
    while True:
        print_menu()
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            return
        if choice not in MENU:
            print("  ! Invalid option, please try again.")
            continue
        label, action = MENU[choice]
        logger.debug("Menu option %s: %s", choice, label)
        try:
            action(tracker)
        # Expected problems: show a message and keep the app running.
        except (ExpenseNotFoundError, StorageError, ChartError) as error:
            logger.warning("%s failed: %s", label, error)
            print(f"  ! {error}")


def main() -> int:
    """Start the app. Returns an exit code: 0 = OK, 1 = error."""
    try:
        config = load_config()
    except ConfigError as error:
        print(f"Configuration problem: {error}")
        return 1
    print(f"Expense Tracker v{__version__}  (data folder: {DATA_DIR.resolve()})")
    setup_logging(config.log_file, config.log_level)
    data_dir = config.data_dir.resolve()
    logger.info(f"Starting Expense Tracker v{__version__} with data folder: {data_dir}")
    try:
        tracker = ExpenseTracker(data_dir)
    except StorageError as error:
        logger.error(f"Could not load your data: {error}")
        return 1
    if tracker.imported:
        print(f"Moved {tracker.imported} expense(s) from Version 1 into the database.")

    with tracker:
        try:
            run(tracker)
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C or Ctrl+D: exit politely instead of showing a traceback.
            print("\nGoodbye!")
        except Exception:
            logger.exception("Unexpected error, the app crashed")
            raise
    logger.info("Stopped")
    return 0
