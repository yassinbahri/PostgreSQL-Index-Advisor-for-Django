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
  <a href="https://www.djangoproject.com/"><img alt="Django 5.2–6.1" src="https://img.shields.io/badge/Django-5.2%E2%80%936.1-0C4B33?logo=django&logoColor=white"></a>
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
> production database. Version `0.2.0` replaces that path with a preview-only,
> evidence-based workflow.

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
 review first ──► migration or database change process
```

The `0.2.0` development workflow:

1. collects slow or frequently executed PostgreSQL statements;
2. parses PostgreSQL filter predicates into schema, table, and column evidence;
3. ignores recommendations already covered by an index prefix;
4. explains the evidence behind each candidate;
5. generates reviewable, safely quoted SQL;
6. never changes the database.

Correctness and database safety take priority over generating a large number
of suggestions.

## Current status

| Area | `0.1.0` on PyPI | `0.2.0` development preview |
| --- | --- | --- |
| Query source | `pg_stat_statements` | Current timing columns and actionable diagnostics |
| Recommendations | Single-column proof of concept | Structured candidates ranked by workload time |
| Existing indexes | Not reliably compared | Detect equivalent and leading-prefix coverage |
| Default behavior | Attempts database changes | Preview only |
| Applying indexes | Known PostgreSQL defect | Never applied; safely quoted SQL is previewed |
| Tests | Minimal | Parser, collector, recommender, command, and SQL coverage |

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
For setup and troubleshooting, see the [`pg_stat_statements` guide](docs/pg-stat-statements.md).

## Try the 0.2 development preview

Use a development database first. Install the current branch directly from
GitHub until `0.2.0` is released:

```console
python -m pip install "django-index-optimizer @ git+https://github.com/yassinbahri/django-index-optimizer.git@v0.2-preview-workflow"
```

Preview query-backed recommendations:

```console
python manage.py optimize_indexes --limit 100 --min-calls 10
```

Each recommendation includes the affected table and columns, workload calls,
total execution time, the reason it was selected, and safely quoted
`CREATE INDEX CONCURRENTLY` SQL. The SQL is printed for review and is never
executed.

For CI, scripts, or a review artifact:

```console
python manage.py optimize_indexes --limit 100 --min-calls 10 --format json \
  > index-recommendations.json
```

Normalized SQL text from `pg_stat_statements` is parsed in memory but is not
included in reports. Query IDs are included so a recommendation can be traced
back without copying potentially sensitive literals into an artifact.

See [Understanding recommendations](docs/recommendations.md) for the evidence
model, existing-index rules, JSON fields, and the checks to perform before
using a SQL preview.

### Current conservative limits

- Only filter predicates that can be mapped unambiguously to one table are
  considered.
- Recommendations are currently single-column B-tree candidates.
- PostgreSQL system catalogs and the optimizer's own queries are ignored.
- Planner validation, write-overhead scoring, joins, ordering, partial indexes,
  and multi-column candidates are planned rather than guessed prematurely.

Supported combinations follow Django: Django 5.2 supports PostgreSQL 14+, and
Django 6.1 supports PostgreSQL 15+. Python 3.10–3.14 is supported where the
selected Django release supports it. PostgreSQL 14–17 are covered by the
project's integration-test matrix.

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
