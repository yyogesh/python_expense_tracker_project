import datetime as dt

import pytest

from expense_tracker.validators import (
    ValidationError,
    parse_amount,
    parse_category,
    parse_date,
    parse_description,
    parse_month,
    parse_positive_int,
)

TODAY = dt.date(2026, 9, 30)


# @pytest.mark.parametrize runs the same test once for each pair of values.
@pytest.mark.parametrize(
    ("text", "expected"),
    [("12", 12.0), (" 12.5 ", 12.5), ("$1,200", 1200.0), ("3.456", 3.46)],
)
def test_parse_amount_valid(text, expected):
    assert parse_amount(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "-5", "0", "nan", "inf", "2000000"])
def test_parse_amount_invalid(text):
    with pytest.raises(ValidationError):
        parse_amount(text)


@pytest.mark.parametrize(
    ("text", "expected"), [("1", "Food"), ("food", "Food"), (" FOOD ", "Food")]
)
def test_parse_category_valid(text, expected):
    assert parse_category(text) == expected


@pytest.mark.parametrize("text", ["0", "99", "pizza", ""])
def test_parse_category_invalid(text):
    with pytest.raises(ValidationError):
        parse_category(text)


def test_parse_description_strips_and_limits_length():
    assert parse_description("  hi  ") == "hi"
    with pytest.raises(ValidationError):
        parse_description("x" * 101)


def test_parse_date_empty_means_today():
    assert parse_date("", today=TODAY) == TODAY


def test_parse_date_valid():
    assert parse_date("2026-09-01", today=TODAY) == dt.date(2026, 9, 1)


@pytest.mark.parametrize("text", ["01/09/2026", "2026-13-01", "2026-10-24", "soon"])
def test_parse_date_invalid(text):
    with pytest.raises(ValidationError):
        parse_date(text, today=TODAY)


def test_parse_month():
    assert parse_month("2026-08", today=TODAY) == (2026, 8)
    assert parse_month("", today=TODAY) == (2026, 9)
    with pytest.raises(ValidationError):
        parse_month("August", today=TODAY)


def test_parse_positive_int():
    assert parse_positive_int(" 3 ") == 3
    for bad in ["0", "-1", "a", ""]:
        with pytest.raises(ValidationError):
            parse_positive_int(bad)
