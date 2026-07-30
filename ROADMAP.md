# Roadmap

## Current status

Version `0.1.0` has been recovered from the source archive published to PyPI.
It is an early alpha and should not be used to modify a production database.

The recovery audit found several release-blocking problems:

- the recommender returns column-name strings while the management command
  expects objects containing both a table and a column;
- query parsing does not reliably associate columns with their tables;
- current PostgreSQL versions expose `total_exec_time` and `mean_exec_time`,
  while the collector requests the older `total_time` and `mean_time` names;
- `CREATE INDEX CONCURRENTLY` is currently placed inside a `DO` transaction
  block, which PostgreSQL does not allow;
- there is no automated test suite or supported-version matrix;
- the command does not clearly separate previewing recommendations from
  applying database changes.

## Proposed 0.2.0 scope

The next release should prioritize correctness and safety over additional index
heuristics:

1. Introduce a structured recommendation containing schema, table, columns,
   evidence, and a deterministic index name.
2. Collect timing data from supported `pg_stat_statements` versions with clear
   diagnostics when the extension is unavailable.
3. Make the command preview-only by default and require an explicit `--apply`
   option before changing the database.
4. Create indexes outside transaction blocks with safely quoted identifiers.
5. Detect existing and equivalent indexes before recommending a new one.
6. Add unit tests plus PostgreSQL integration tests.
7. Publish an explicit Python, Django, and PostgreSQL support matrix.

## Later ideas

- multi-column recommendations based on repeated predicate order;
- selectivity and table-size signals;
- JSON and SQL report output;
- Django admin reporting;
- before-and-after `EXPLAIN` comparisons in an explicitly enabled safe mode.

These features should only be considered after the `0.2.0` correctness work is
complete.

## Contributor-sized tasks

The following issues are intentionally small and do not overlap the core
database-safety redesign:

- [#1: Expand recommendation threshold tests](https://github.com/yassinbahri/django-index-optimizer/issues/1)
- [#2: Add a `--limit` command option](https://github.com/yassinbahri/django-index-optimizer/issues/2)
- [#3: Document `pg_stat_statements` troubleshooting](https://github.com/yassinbahri/django-index-optimizer/issues/3)

Comment on an unassigned issue before starting. The maintainer will confirm the
scope and assign it to avoid duplicate work.
