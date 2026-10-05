import csv

import pytest

from expense_tracker.storage import (
    StorageError,
    export_to_csv,
    load_expenses,
    load_settings,
    save_expenses,
    save_settings,
)


def test_missing_file_means_no_expenses(tmp_path):
    assert load_expenses(tmp_path / "nope.json") == []


def test_save_then_load_gives_same_expenses(tmp_path, sample_expenses):
    path = tmp_path / "expenses.json"
    save_expenses(sample_expenses, path)
    assert load_expenses(path) == sample_expenses


def test_save_leaves_no_temp_file(tmp_path, sample_expenses):
    save_expenses(sample_expenses, tmp_path / "expenses.json")
    assert [p.name for p in tmp_path.iterdir()] == ["expenses.json"]


def test_corrupted_json_raises_storage_error(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(StorageError):
        load_expenses(path)


def test_wrong_shape_raises_storage_error(tmp_path):
    path = tmp_path / "expenses.json"
    path.write_text('[{"id": 1}]', encoding="utf-8")
    with pytest.raises(StorageError):
        load_expenses(path)


def test_settings_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    assert load_settings(path) == {}
    save_settings({"monthly_budget": 500.0}, path)
    assert load_settings(path) == {"monthly_budget": 500.0}


def test_export_to_csv(tmp_path, sample_expenses):
    path = tmp_path / "out" / "export.csv"
    assert export_to_csv(sample_expenses, path) == 4
    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["category"] == "Food"
    assert rows[0]["date"] == "2026-08-05"
