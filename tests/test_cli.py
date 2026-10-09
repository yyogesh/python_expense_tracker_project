"""Testing code that uses input() and print().

``monkeypatch`` temporarily replaces things during a test. Here we replace the
built-in input() with a fake that returns prepared answers.
``capsys`` captures everything printed so we can check it.
"""

from expense_tracker.cli import ask, money, text_bar
from expense_tracker.validators import parse_amount


def test_money_format():
    assert money(1234.5) == "$1,234.50"


def test_text_bar():
    assert text_bar(0.5, width=10) == "[#####-----]"
    assert text_bar(2.0, width=4) == "[####]"  # never longer than full


def test_ask_repeats_until_valid(monkeypatch, capsys):
    answers = iter(["abc", "-3", "12.5"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert ask("Amount: ", parse_amount) == 12.5

    printed = capsys.readouterr().out
    assert printed.count("!") == 2  # two error messages shown
