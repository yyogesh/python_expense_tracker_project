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