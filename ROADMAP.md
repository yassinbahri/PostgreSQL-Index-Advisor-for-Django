# Roadmap

## Current status

Version `0.2.0` provides a safe, preview-only recommendation workflow. It does
not modify the database.

Version `0.2.0` resolved the release-blocking problems found in `0.1.0`:

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

## 0.2.0 safe-preview scope

The next release should prioritize correctness and safety over additional index
heuristics:

1. [x] Introduce structured recommendations containing schema, table, columns,
   workload evidence, query IDs, and deterministic index names.
2. [x] Collect current `pg_stat_statements` timing data with actionable setup
   and permission diagnostics.
3. [x] Replace regex extraction with PostgreSQL-aware AST parsing.
4. [x] Make the command preview-only and remove index execution from its path.
5. [x] Detect equivalent and leading-prefix indexes before recommending one.
6. [x] Provide human-readable and JSON reports with safely quoted SQL previews.
7. [x] Prevent the analyzer from learning from its own catalog queries.
8. [x] Run PostgreSQL 14, 15, 16, and 17 integration tests in CI.
9. [ ] Map tables and columns back to Django model and field names.

## 0.3 trust and validation

- collect table size, row estimates, write activity, and index usage;
- rank by workload impact while suppressing tiny or write-heavy tables;
- validate candidates with hypothetical indexes through optional HypoPG;
- show before-and-after planner cost and whether PostgreSQL would use the index;
- export a Django `AddIndex` migration for mapped models;
- snapshot reports so teams can compare recommendation changes in CI.

## 0.4 daily developer workflow

- multi-column candidates based on equality/range predicate order;
- join and ordering analysis;
- partial and covering-index candidates when evidence supports them;
- a local Django admin report with acknowledge/dismiss decisions;
- recommendation fingerprints and configuration-based ignore rules;
- unused, duplicate, invalid, and overlapping index diagnostics.

Automatic index creation is intentionally not on the roadmap until preview,
planner validation, locking behavior, and rollback guidance are mature.

## Contributing to the roadmap

Roadmap work is tracked in [GitHub issues](https://github.com/yassinbahri/PostgreSQL-Index-Advisor-for-Django/issues).
Issues labeled `good first issue` are deliberately scoped so a new contributor
can complete them without designing the recommendation engine. Comment on an
unassigned issue before starting; the maintainer will confirm its scope and
assign it to avoid duplicate work.
