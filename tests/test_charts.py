import pytest

from expense_tracker.charts import ChartError, save_category_pie, save_monthly_bar

# Skip these tests if matplotlib is not installed.
pytest.importorskip("matplotlib")


def test_charts_are_created(tmp_path, sample_expenses):
    pie = save_category_pie(sample_expenses, tmp_path / "pie.png")
    bar = save_monthly_bar(sample_expenses, tmp_path / "bar.png")
    assert pie.exists() and pie.stat().st_size > 0
    assert bar.exists() and bar.stat().st_size > 0


def test_no_expenses_raises(tmp_path):
    with pytest.raises(ChartError):
        save_category_pie([], tmp_path / "pie.png")
