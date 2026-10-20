import csv
import datetime as dt
import json
from dataclasses import replace
from decimal import Decimal

import pytest

from expense_tracker.storage import (
    StorageError,
    connect,
    delete_expense,
    export_to_csv,
    from_cents,
    get_expense,
    get_setting,
    insert_expense,
    load_expenses,
    migrate_from_json,
    set_setting,
    to_cents,
    update_expense,
)

DAY = dt.date(2026, 9, 1)


@pytest.fixture
def conn(tmp_path):
    connection = connect(tmp_path / "expenses.db")
    yield connection
    connection.close()


def _write_v1_files(tmp_path, expenses, settings=None):
    expenses_path = tmp_path / "expenses.json"
    settings_path = tmp_path / "settings.json"
    expenses_path.write_text(json.dumps(expenses), encoding="utf-8")
    if settings is not None:
        settings_path.write_text(json.dumps(settings), encoding="utf-8")
    return expenses_path, settings_path


def test_cents_round_trip():
    assert to_cents(Decimal("12.50")) == 1250
    assert from_cents(1250) == Decimal("12.50")


def test_new_database_has_no_expenses(conn):
    assert load_expenses(conn) == []


def test_insert_then_load_gives_same_expenses(conn, sample_expenses):
    for e in sample_expenses:
        insert_expense(conn, e.amount, e.category, e.description, e.date)
    assert load_expenses(conn) == sample_expenses


def test_data_survives_reconnect(tmp_path):
    first = connect(tmp_path / "expenses.db")
    insert_expense(first, Decimal("19.99"), "Food", "Lunch", DAY)
    first.close()
    second = connect(tmp_path / "expenses.db")
    assert get_expense(second, 1).amount == Decimal("19.99")
    second.close()


def test_ids_are_never_reused(conn):
    first = insert_expense(conn, Decimal("1.00"), "Food", "a", DAY)
    delete_expense(conn, first.id)
    second = insert_expense(conn, Decimal("2.00"), "Food", "b", DAY)
    assert second.id == first.id + 1


def test_update_and_delete(conn):
    expense = insert_expense(conn, Decimal("10.00"), "Food", "Lunch", DAY)
    changed = replace(expense, amount=Decimal("12.00"))
    update_expense(conn, changed)
    assert get_expense(conn, expense.id) == changed
    assert delete_expense(conn, expense.id) is True
    assert delete_expense(conn, expense.id) is False
    assert get_expense(conn, expense.id) is None


def test_database_rejects_non_positive_amount(conn):
    with pytest.raises(StorageError):
        insert_expense(conn, Decimal("0.00"), "Food", "free", DAY)


def test_not_a_database_raises_storage_error(tmp_path):
    path = tmp_path / "expenses.db"
    path.write_text("this is not a database " * 10, encoding="utf-8")
    with pytest.raises(StorageError):
        connect(path)


def test_settings_round_trip(conn):
    assert get_setting(conn, "monthly_budget") is None
    set_setting(conn, "monthly_budget", "500.00")
    assert get_setting(conn, "monthly_budget") == "500.00"
    set_setting(conn, "monthly_budget", None)
    assert get_setting(conn, "monthly_budget") is None


def test_migrate_from_json(tmp_path, conn, sample_expenses):
    expenses_path, settings_path = _write_v1_files(
        tmp_path,
        [e.to_dict() for e in sample_expenses],
        {"monthly_budget": 500.0},
    )
    assert migrate_from_json(conn, expenses_path, settings_path) == 4
    assert load_expenses(conn) == sample_expenses
    assert get_setting(conn, "monthly_budget") == "500.0"
    # Old files are renamed, not deleted, so a second run does nothing.
    assert (tmp_path / "expenses.json.migrated").exists()
    assert not expenses_path.exists()
    assert migrate_from_json(conn, expenses_path, settings_path) == 0


def test_migrate_refuses_when_database_has_data(tmp_path, conn):
    insert_expense(conn, Decimal("1.00"), "Food", "a", DAY)
    expenses_path, settings_path = _write_v1_files(tmp_path, [])
    with pytest.raises(StorageError):
        migrate_from_json(conn, expenses_path, settings_path)
    assert expenses_path.exists()


def test_corrupted_json_raises_storage_error(tmp_path, conn):
    path = tmp_path / "expenses.json"
    path.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(StorageError):
        migrate_from_json(conn, path, tmp_path / "settings.json")


def test_wrong_shape_raises_storage_error(tmp_path, conn):
    expenses_path, settings_path = _write_v1_files(tmp_path, [{"id": 1}])
    with pytest.raises(StorageError):
        migrate_from_json(conn, expenses_path, settings_path)


def test_bad_amount_raises_storage_error(tmp_path, conn):
    expenses_path, settings_path = _write_v1_files(
        tmp_path,
        [{"id": 1, "amount": "abc", "category": "Food", "date": "2026-09-01"}],
    )
    with pytest.raises(StorageError):
        migrate_from_json(conn, expenses_path, settings_path)
    # Nothing half-written, and the old file is kept.
    assert load_expenses(conn) == []
    assert expenses_path.exists()


def test_export_to_csv(tmp_path, sample_expenses):
    path = tmp_path / "out" / "export.csv"
    assert export_to_csv(sample_expenses, path) == 4
    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["category"] == "Food"
    assert rows[0]["date"] == "2026-08-05"
