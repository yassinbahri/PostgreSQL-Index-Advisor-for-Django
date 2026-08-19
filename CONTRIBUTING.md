# Contributing to django-index-optimizer

Thank you for helping make PostgreSQL performance tooling easier to use from
Django. Small, focused contributions are welcome.

## Before starting

1. Choose an unassigned issue. Issues labeled `good first issue` are designed
   to be completed without deep PostgreSQL knowledge.
2. Leave a short comment describing the approach you plan to take.
3. Wait for assignment or maintainer confirmation before doing substantial
   work. This avoids two people solving the same issue.

## Local setup

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/PostgreSQL-Index-Advisor-for-Django.git
cd PostgreSQL-Index-Advisor-for-Django
python -m venv .venv
```

Activate the environment:

```bash
# Linux and macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the project and development tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Run the checks:

```bash
python -m pytest
python -m ruff check .
```

Some future integration tests will require PostgreSQL and
`pg_stat_statements`. An issue that requires PostgreSQL will say so explicitly;
beginner issues should otherwise run with mocks and need no database server.

## Pull requests

- Create a branch from the latest `main`.
- Keep the pull request focused on one issue.
- Add or update tests when behavior changes.
- Update documentation when user-facing behavior changes.
- Include `Closes #ISSUE_NUMBER` in the pull request description.
- Do not include generated files such as `__pycache__`, build artifacts, or
  virtual environments.

Maintainers may request changes. That is a normal part of collaboration, not a
rejection of the contribution.

## Safety expectations

This package analyzes database activity and may eventually create indexes.
Changes that execute SQL must:

- remain preview-only unless the user explicitly opts in;
- quote PostgreSQL identifiers safely;
- avoid executing `CREATE INDEX CONCURRENTLY` inside a transaction;
- include tests for failure paths;
- document any locks, permissions, or production risks.

Please do not test index creation against a production database.
