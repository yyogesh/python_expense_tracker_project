expense-tracker/
├── pyproject.toml           # Project info, dependencies, tool settings
├── README.md                # How to install and use the project
├── .gitignore               # Files Git should not track
├── src/
│   └── expense_tracker/
│       ├── __init__.py      # Marks this folder as a Python package
│       ├── __main__.py      # Lets us run: python -m expense_tracker
│       ├── cli.py           # Menu and user interaction
│       ├── config.py        # Constants: file paths, categories, defaults
│       ├── models.py        # Expense dataclass
│       ├── storage.py       # Load/save JSON, export CSV
│       ├── validators.py    # Checks user input (amount, date, category)
│       └── reports.py       # Totals, filters, summaries, charts
├── tests/
│   ├── conftest.py          # Shared test setup (fixtures)
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_validators.py
│   └── test_reports.py
└── data/                    # Your real expense data (ignored by Git)


pip install -e ".[charts]


expense-tracker

python -m expense-tracker


python -m pip 


EXPENSE_TRACKER_DATA_DIR="$HOME/my-expenses" expense-tracker


$env:EXPENSE_TRACKER_DATA_DIR = "$HOME\my-expenses"

EXPENSE_TRACKER_LOG_LEVEL=DEBUG expense-tracker                # macOS/Linux
$env:EXPENSE_TRACKER_LOG_LEVEL="DEBUG"; expense-tracker # window


echo $?                  # macOS / Linux
echo $LASTEXITCODE       # Windows PowerShell
echo %ERRORLEVEL%        # Windows Command Prompt


pip install -e .

pip install -e ".[charts]"

pip install -e ".[dev]"


float ==> base 2

base 10


>>> import sqlite3
>>> conn = sqlite3.connect(":memory:")

>>> conn.execute("INSERT INTO people (name, age) VALUES ('Asha', 31)")
>>> conn.execute("INSERT INTO people (name, age) VALUES ('Ben', 25)")
>>> conn.execute("SELECT * FROM people").fetchall()
[(1, 'Asha', 31), (2, 'Ben', 25)]


>>> conn.execute("SELECT name FROM people WHERE age > 30").fetchall()
[('Asha',)]
>>> conn.execute("SELECT name FROM people ORDER BY age").fetchall()
[('Ben',), ('Asha',)]
>>> conn.execute("UPDATE people SET age = 26 WHERE id = 2")
>>> conn.execute("DELETE FROM people WHERE id = 1")
>>> conn.execute("SELECT * FROM people").fetchall()
[(2, 'Ben', 26)]

CREATE TABLE  = the dataclass fields
INSERT        = list.append
SELECT        = load everything
WHERE         = list comprehension with "if"
ORDER BY      = sorted()
UPDATE        = dataclasses.replace
DELETE        = list.remove



$12.50

A: Float
B: Text
C: Integer 1250 cent


