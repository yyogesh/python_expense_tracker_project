import pytest

from expense_tracker.charts import ChartError, save_category_pie, save_monthly_bar

pytest.importorskip("matplotlib")
# pytest skips this whole file instead of failing it.
# A missing optional library isn’t a bug in our code, so it shouldn’t show up as a red failure.
# Skipped tests are reported separately, so you can still see they didn’t run.


def test_charts_are_created(tmp_path, sample_expenses):
    pie = save_category_pie(sample_expenses, tmp_path / "pie.png")
    bar = save_monthly_bar(sample_expenses, tmp_path / "bar.png")
    assert pie.exists() and pie.stat().st_size > 0
    assert bar.exists() and bar.stat().st_size > 0


def test_no_expenses_raises(tmp_path):
    with pytest.raises(ChartError):
        save_category_pie([], tmp_path / "pie.png")
