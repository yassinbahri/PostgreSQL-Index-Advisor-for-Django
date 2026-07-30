<p align="center">
  <img src="https://raw.githubusercontent.com/yassinbahri/django-index-optimizer/main/docs/assets/hero.png" alt="Database query paths are analyzed and transformed into an efficient index tree" width="100%">
</p>

<h1 align="center">django-index-optimizer</h1>

<p align="center">
  <strong>Turn recurring PostgreSQL query patterns into reviewable index recommendations for Django.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/django-index-optimizer/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/django-index-optimizer.svg"></a>
  <a href="https://pypistats.org/packages/django-index-optimizer"><img alt="Monthly downloads" src="https://img.shields.io/pypi/dm/django-index-optimizer?color=44B78B"></a>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
  <a href="https://www.djangoproject.com/"><img alt="Django 5.2–6.0" src="https://img.shields.io/badge/Django-5.2%E2%80%936.0-0C4B33?logo=django&logoColor=white"></a>
  <a href="LICENSE"><img alt="BSD 2-Clause license" src="https://img.shields.io/badge/License-BSD%202--Clause-35c978"></a>
  <a href="ROADMAP.md"><img alt="Status alpha" src="https://img.shields.io/badge/Status-alpha-f0b45d"></a>
</p>

`django-index-optimizer` is an experimental Django app for learning from
PostgreSQL's `pg_stat_statements` data. Its goal is to identify repeated query
patterns, compare them with existing indexes, and produce recommendations that
a developer can understand before changing the database.

> [!WARNING]
> The published `0.1.0` release is an early proof of concept with known
> execution-path defects. Do not run its management command against a
> production database. The `0.2.0` work on `main` is focused on making analysis
> preview-only and database changes explicitly opt-in.

## What the project is becoming

```text
pg_stat_statements
        │
        ▼
 recurring query patterns
        │
        ▼
 existing-index comparison
        │
        ▼
 explained recommendations
        │
        ▼
 review first ──► apply only when explicitly requested
```

The planned safe workflow will:

1. collect slow or frequently executed PostgreSQL statements;
2. identify filter, join, ordering, and grouping columns;
3. ignore recommendations already covered by an index;
4. explain the evidence behind each candidate;
5. generate reviewable SQL without executing it by default;
6. apply changes only through an explicit opt-in command.

Correctness and database safety take priority over generating a large number
of suggestions.

## Current status

| Area | `0.1.0` on PyPI | `0.2.0` development goal |
| --- | --- | --- |
| Query source | `pg_stat_statements` | Version-aware collection and diagnostics |
| Recommendations | Single-column proof of concept | Structured, evidence-based candidates |
| Existing indexes | Not reliably compared | Detect equivalent and covering indexes |
| Default behavior | Attempts database changes | Preview only |
| Applying indexes | Known PostgreSQL defect | Explicit opt-in with safely quoted SQL |
| Tests | Minimal | Unit and PostgreSQL integration coverage |

See the [roadmap](ROADMAP.md) for the audited defects, release scope, and later
ideas.

## Explore the published alpha

If you want to inspect the historical implementation, use a disposable local
PostgreSQL database:

```console
python -m pip install django-index-optimizer==0.1.0
```

Add the app:

```python
INSTALLED_APPS = [
    # ...
    "optimizer",
]
```

Enable `pg_stat_statements` in PostgreSQL:

```conf
shared_preload_libraries = 'pg_stat_statements'
```

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

The historical command is:

```console
python manage.py optimize_indexes
```

To inspect a different number of statements, pass a positive limit:

```console
python manage.py optimize_indexes --limit 25
```
It is documented for reproducibility, not recommended for production use.

## Download statistics

<p>
  <a href="https://pypistats.org/packages/django-index-optimizer"><img alt="django-index-optimizer monthly downloads" src="https://img.shields.io/pypi/dm/django-index-optimizer?style=for-the-badge&color=44B78B"></a>
</p>

PyPI download counts include automated environments such as CI and are not a
count of unique users. [View the current breakdown on PyPI Stats](https://pypistats.org/packages/django-index-optimizer).

## Contributing

New contributors are welcome, including developers who are still learning
Django or PostgreSQL internals.

1. Choose an unassigned [`good first issue`](https://github.com/yassinbahri/django-index-optimizer/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22).
2. Comment with the approach you want to take and wait for confirmation.
3. Follow the environment, test, and pull-request steps in
   [CONTRIBUTING.md](CONTRIBUTING.md).

Most beginner issues use unit tests and do not require a local PostgreSQL
server unless the issue explicitly says otherwise.

## Security

Report database-safety or SQL-injection concerns privately through
[GitHub security advisories](https://github.com/yassinbahri/django-index-optimizer/security/advisories/new).
Never include credentials or sensitive production queries in a public issue.

## License

BSD 2-Clause. See [LICENSE](LICENSE).
