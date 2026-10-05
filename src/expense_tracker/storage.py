"""Storage - saving and loading data from files."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from expense_tracker.models import Expense

CSV_FIELDS = ["id", "date", "category", "amount", "description"]


class StorageError(Exception):
    """Raised when a data file exists but cannot be read."""


def load_expenses(path: Path) -> list[Expense]:
    """Read expenses from a JSON file. A missing file means "no expenses yet"."""

    if not path.exists():
        return []

    raw = _read_json(path)

    if not isinstance(raw, list):
        raise StorageError(f"{path} should contain a list of expenses.")

    try:
        return [Expense.from_dict(item) for item in raw]
    except (KeyError, ValueError, TypeError) as error:
        raise StorageError(f"{path} contains an invalid expense: {error}") from error


def save_expenses(expenses: Iterable[Expense], path: Path) -> None:
    """Write all expenses to a JSON file."""
    _write_json_atomic(path, [expense.to_dict() for expense in expenses])


def load_settings(path: Path) -> dict[str, Any]:
    """Read user settings (like the monthly budget). Missing file -> {}."""
    if not path.exists():
        return {}
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise StorageError(f"{path} should contain a JSON object.")
    return raw


def save_settings(settings: dict[str, Any], path: Path) -> None:
    _write_json_atomic(path, settings)


def export_to_csv(expenses: Iterable[Expense], path: Path) -> int:
    """Write expenses to a CSV file. Returns how many rows were written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    # newline="" is required by the csv module to avoid blank lines on Windows.
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for expense in expenses:
            writer.writerow(expense.to_dict())
            count += 1
    return count


# ---------------------------------------------------------------------------
# Private helpers. The leading underscore means "used only inside this file".
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StorageError(f"{path} is not valid JSON: {error}") from error


def _write_json_atomic(path: Path, data: Any) -> None:
    """Write JSON safely.

    We first write to a temporary file, then rename it over the real file.
    Renaming is *atomic* (all-or-nothing), so if the computer crashes mid-save
    the old file is still intact instead of half-written and corrupted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp_path.replace(path)
