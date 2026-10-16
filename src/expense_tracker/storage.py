"""Storage - saving and loading data in a SQLite database.

Why this file exists:
    Without saving, every expense disappears when the program closes. All
    reading and writing of data lives here. In Version 1 that meant JSON
    files; since Lesson 12 it means one SQLite database file. The rest of the
    app never sees SQL, so this is the file that changed.

Why SQLite?
    - It is built into Python (``import sqlite3``), so no new dependency.
    - The whole database is ONE ordinary file (``data/expenses.db``).
    - Saving one expense writes one row, not the whole file again.
    - The database hands out IDs and never reuses them (AUTOINCREMENT).
    - Rules such as "amount must be positive" are checked by the database
      itself, whoever writes to it.

How money is stored:
    SQLite has no exact decimal type, so amounts are saved as whole CENTS in
    an INTEGER column: $12.50 is stored as 1250. Integers are always exact,
    and SQL can add them up correctly.

Formats used:
    SQLite - the app's data (expenses and settings).
    JSON   - read once, to move Version 1 data into the database.
    CSV    - simple table format that Excel and Google Sheets can open.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from expense_tracker.models import Expense, to_money

CSV_FIELDS = ["id", "date", "category", "amount", "description"]

# The database "schema": which tables exist and what each column holds.
# IF NOT EXISTS makes it safe to run every time the app starts.
SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    category     TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    date         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class StorageError(Exception):
    """Raised when stored data cannot be read or written."""


# ---------------------------------------------------------------------------
# Money <-> cents
# ---------------------------------------------------------------------------


def to_cents(amount: Decimal) -> int:
    """Decimal("12.50") -> 1250. Exact: no float is involved."""
    return int(to_money(amount) * 100)


def from_cents(cents: int) -> Decimal:
    """1250 -> Decimal("12.50")."""
    return to_money(Decimal(cents) / 100)


# ---------------------------------------------------------------------------
# Opening the database
# ---------------------------------------------------------------------------


def connect(path: Path) -> sqlite3.Connection:
    """Open (or create) the database file and make sure the tables exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    # Rows behave like dictionaries: row["category"] instead of row[2].
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
    except sqlite3.DatabaseError as error:
        conn.close()
        raise StorageError(f"{path} is not a valid database: {error}") from error
    return conn


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------


def load_expenses(conn: sqlite3.Connection) -> list[Expense]:
    """All expenses, oldest first (by date, then by ID)."""
    rows = conn.execute("SELECT * FROM expenses ORDER BY date, id")
    return [_row_to_expense(row) for row in rows]


def get_expense(conn: sqlite3.Connection, expense_id: int) -> Expense | None:
    """One expense, or None if no expense has this ID."""
    # The ? is a placeholder. sqlite3 fills it in safely - never use an
    # f-string to put values into SQL.
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    return _row_to_expense(row) if row is not None else None


def insert_expense(
    conn: sqlite3.Connection,
    amount: Decimal,
    category: str,
    description: str,
    date: dt.date,
) -> Expense:
    """Save a NEW expense. The database chooses its ID."""
    with _transaction(conn):
        cursor = conn.execute(
            "INSERT INTO expenses (amount_cents, category, description, date) "
            "VALUES (?, ?, ?, ?)",
            (to_cents(amount), category, description, date.isoformat()),
        )
    # lastrowid is the ID the database just gave the new row.
    expense_id = cursor.lastrowid
    assert expense_id is not None  # always set after a successful INSERT
    return Expense(expense_id, to_money(amount), category, description, date)


def update_expense(conn: sqlite3.Connection, expense: Expense) -> None:
    """Overwrite the stored row that has ``expense.id``."""
    with _transaction(conn):
        conn.execute(
            "UPDATE expenses "
            "SET amount_cents = ?, category = ?, description = ?, date = ? "
            "WHERE id = ?",
            (
                to_cents(expense.amount),
                expense.category,
                expense.description,
                expense.date.isoformat(),
                expense.id,
            ),
        )


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    """Delete one expense. Returns False if there was nothing to delete."""
    with _transaction(conn):
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    return cursor.rowcount == 1


# ---------------------------------------------------------------------------
# Settings (a simple key -> value table)
# ---------------------------------------------------------------------------


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row is not None else None


def set_setting(conn: sqlite3.Connection, key: str, value: str | None) -> None:
    """Save a setting as text. ``None`` removes it."""
    with _transaction(conn):
        if value is None:
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))
        else:
            # REPLACE: insert a new row, or overwrite the row with this key.
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )


# ---------------------------------------------------------------------------
# Migration: moving Version 1 JSON data into the database (runs once)
# ---------------------------------------------------------------------------


def migrate_from_json(
    conn: sqlite3.Connection, expenses_path: Path, settings_path: Path
) -> int:
    """Copy Version 1 JSON files into the database, then rename them.

    Returns how many expenses were imported (0 if there was nothing to do).
    """
    old_files = [path for path in (expenses_path, settings_path) if path.exists()]
    if not old_files:
        return 0  # a new user, or the files were already migrated

    if conn.execute("SELECT 1 FROM expenses LIMIT 1").fetchone() is not None:
        # Never guess with someone's data: merging two sets of IDs could
        # silently mix them up. Stop and let the user decide.
        names = ", ".join(path.name for path in old_files)
        raise StorageError(
            f"The database already has expenses, but old files were found too: "
            f"{names}. Move them out of the data folder to continue."
        )

    # Read EVERYTHING first. A broken JSON file stops us before we write.
    expenses = _read_json_expenses(expenses_path)
    settings = _read_json_settings(settings_path)

    # One transaction: either every row is saved, or none is.
    with _transaction(conn):
        conn.executemany(
            "INSERT INTO expenses (id, amount_cents, category, description, date) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (e.id, to_cents(e.amount), e.category, e.description, str(e.date))
                for e in expenses
            ],
        )
        conn.executemany(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            [(key, str(value)) for key, value in settings.items()],
        )

    # Only after the data is safely saved: rename (not delete) the old files.
    for path in old_files:
        path.replace(path.with_name(path.name + ".migrated"))
    return len(expenses)


# ---------------------------------------------------------------------------
# CSV export (unchanged since Version 1)
# ---------------------------------------------------------------------------


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


@contextmanager
def _transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """Run the code inside a ``with`` block as ONE transaction.

    ``with conn:`` COMMITs (saves) when the block finishes, and ROLLs BACK
    (undoes everything) if it raises. It does NOT close the connection.
    We also turn sqlite3's errors into our own StorageError, so the rest of
    the app never needs to know that sqlite3 exists.
    """
    try:
        with conn:
            yield
    except sqlite3.Error as error:
        raise StorageError(f"Could not save to the database: {error}") from error


def _row_to_expense(row: sqlite3.Row) -> Expense:
    return Expense(
        id=row["id"],
        amount=from_cents(row["amount_cents"]),
        category=row["category"],
        description=row["description"],
        date=dt.date.fromisoformat(row["date"]),
    )


def _read_json_expenses(path: Path) -> list[Expense]:
    """The Version 1 ``load_expenses``. A missing file means no expenses."""
    if not path.exists():
        return []
    raw = _read_json(path)
    if not isinstance(raw, list):
        raise StorageError(f"{path} should contain a list of expenses.")
    try:
        return [Expense.from_dict(item) for item in raw]
    # InvalidOperation: an amount like "abc" (Decimal's error is not a ValueError)
    except (KeyError, ValueError, TypeError, InvalidOperation) as error:
        raise StorageError(f"{path} contains an invalid expense: {error}") from error


def _read_json_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise StorageError(f"{path} should contain a JSON object.")
    return raw


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StorageError(f"{path} is not valid JSON: {error}") from error
