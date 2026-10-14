"""Charts - turning report data into PNG images with matplotlib.

Why this file exists:
    A picture of your spending is easier to understand than a table of
    numbers. matplotlib is an *external* library (not built into Python), so we
    keep it in its own file and make it OPTIONAL:

        pip install -e ".[charts]"

    If matplotlib is missing, the rest of the app still works; only the chart
    menu option shows a helpful message.

Key idea - lazy import:
    We import matplotlib *inside* a function instead of at the top of the file.
    That way the app starts even when matplotlib is not installed.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from expense_tracker.config import CURRENCY
from expense_tracker.models import Expense
from expense_tracker.reports import totals_by_category, totals_by_month


class ChartError(Exception):
    """Raised when a chart cannot be created."""


def _load_pyplot() -> Any:
    try:
        import matplotlib
    except ImportError as error:
        raise ChartError(
            'Charts need matplotlib. Install it with: pip install -e ".[charts]"'
        ) from error
    # "Agg" draws straight to image files, without opening a window.
    # This works everywhere, even on servers with no screen.
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def save_category_pie(expenses: Iterable[Expense], path: Path) -> Path:
    """Pie chart: what share of spending went to each category."""
    totals = totals_by_category(expenses)
    if not totals:
        raise ChartError("There are no expenses to chart yet.")
    plt = _load_pyplot()

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        # matplotlib draws pixels and works with floats; exact cents only
        # matter for the numbers we store and add up, not for a picture.
        [float(amount) for amount in totals.values()],
        labels=list(totals.keys()),
        autopct="%1.1f%%",  # show percentages with one decimal
        startangle=90,
    )
    ax.set_title("Spending by category", pad=20)  # pad = space above the pie
    ax.axis("equal")  # keep the pie round
    return _save(fig, plt, path)


def save_monthly_bar(expenses: Iterable[Expense], path: Path) -> Path:
    """Bar chart: total spending for each month."""
    totals = totals_by_month(expenses)
    if not totals:
        raise ChartError("There are no expenses to chart yet.")
    plt = _load_pyplot()

    fig, ax = plt.subplots(figsize=(9, 5))
    values = [float(amount) for amount in totals.values()]
    ax.bar(list(totals.keys()), values, color="#4C72B0")
    ax.set_title("Spending by month")
    ax.set_xlabel("Month")
    ax.set_ylabel(f"Amount ({CURRENCY})")
    ax.tick_params(axis="x", rotation=45)
    return _save(fig, plt, path)


def _save(fig: Any, plt: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)  # free memory - important when making many charts
    return path
