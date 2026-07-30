# django-index-optimizer

[![PyPI](https://img.shields.io/pypi/v/django-index-optimizer?logo=pypi&logoColor=white)](https://pypi.org/project/django-index-optimizer/)
[![Monthly downloads](https://img.shields.io/pypi/dm/django-index-optimizer?color=44B78B)](https://pypistats.org/packages/django-index-optimizer)
[![Python](https://img.shields.io/pypi/pyversions/django-index-optimizer?logo=python&logoColor=white)](https://pypi.org/project/django-index-optimizer/)
[![License](https://img.shields.io/github/license/yassinbahri/django-index-optimizer)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-D9A441)](ROADMAP.md)

Analyze PostgreSQL query statistics and turn recurring query patterns into
actionable index recommendations for Django applications.

## Project status

The source for the published `0.1.0` release has been recovered and preserved
in this repository. That release is an early proof of concept and has known
execution-path defects. **Do not run it against a production database.**

Development is now focused on a safer `0.2.0` release that will be preview-only
by default, support current PostgreSQL statistics columns, and include automated
tests. See the [roadmap](ROADMAP.md) for the audited problems and planned scope.

## Intended workflow

`django-index-optimizer` is designed to:

1. read slow or frequently executed statements from `pg_stat_statements`;
2. identify filter, ordering, grouping, and join columns;
3. compare candidates with existing PostgreSQL indexes;
4. explain each recommendation and generate reviewable SQL;
5. apply an index only after the user explicitly opts in.

Correctness and database safety take priority over automatically creating a
large number of indexes.

## Published alpha

The historical alpha remains available for reproducibility:

```bash
pip install django-index-optimizer==0.1.0
```

Add the application to Django:

```python
INSTALLED_APPS = [
    # ...
    "optimizer",
]
```

PostgreSQL must load and enable `pg_stat_statements`:

```conf
shared_preload_libraries = 'pg_stat_statements'
```

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

The documented management command is:

```bash
python manage.py optimize_indexes
```

It is retained for historical reference while the `0.2.0` safety work is in
progress. Use a disposable development database if you are investigating the
current implementation.

## Download statistics

PyPI Stats reported the following mirror-filtered activity on 2026-07-30:

| Period | Downloads |
| --- | ---: |
| Last day | 0 |
| Last week | 8 |
| Last month | 31 |

[View the current statistics on PyPI Stats](https://pypistats.org/packages/django-index-optimizer).
Download counts include automated environments such as CI and should not be
interpreted as a count of unique users.

## Contributing

New contributors are welcome. Start with an unassigned issue labeled
[`good first issue`](https://github.com/yassinbahri/django-index-optimizer/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22),
leave a comment describing your approach, and wait for confirmation before
doing substantial work.

The complete fork, environment, test, and pull-request workflow is in
[CONTRIBUTING.md](CONTRIBUTING.md). Beginner issues do not require a local
PostgreSQL server unless the issue says otherwise.

## Security

Please report database-safety or SQL-injection concerns privately through
[GitHub security advisories](https://github.com/yassinbahri/django-index-optimizer/security/advisories/new).
Do not include credentials or sensitive production queries in a public issue.

## License

MIT. See [LICENSE](LICENSE).
