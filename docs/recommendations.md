# Understanding recommendations

PostgreSQL Index Advisor for Django treats every recommendation as a review artifact, not
an instruction to change a database automatically.

## Evidence collected

The analyzer reads the highest-total-time statements for the selected database
from `pg_stat_statements`. For each unambiguous filter column it aggregates:

- calls across matching query IDs;
- total execution time across those statements;
- mean execution time derived from the aggregate;
- the PostgreSQL query IDs that contributed to the recommendation.

Raw query text is not included in text or JSON output. This reduces the chance
of copying sensitive query literals into CI artifacts, tickets, or chat.

## Existing-index coverage

Before returning a candidate, the recommender reads valid, ready indexes from
PostgreSQL's catalogs. A candidate is suppressed when its columns are already
the leading prefix of an existing index.

For example, an index on `(author_id, published_at)` covers the current
single-column candidate `(author_id)`. An index on `(published_at, author_id)`
does not provide the same leading-prefix coverage and does not suppress it.

Primary-key and unique indexes participate in the same comparison. Invalid or
not-yet-ready indexes do not count as coverage.

## Reading the SQL preview

The command prints `CREATE INDEX CONCURRENTLY` SQL with every schema, table,
column, and index name quoted through Django's PostgreSQL backend. The command
does not execute that SQL.

Before using a preview, verify at least:

1. the table is large enough for an index to be worthwhile;
2. the workload is representative and statistics were not just reset;
3. write overhead and disk usage are acceptable;
4. the index is not equivalent to a partial, expression, or operator-class
   index the current comparison cannot model;
5. PostgreSQL's planner is likely to use it.

Planner validation and write-overhead scoring are planned for the next stage.
Until then, recommendations are candidates for investigation.

## JSON contract

Use `--format json` when another tool or CI job needs to consume the report.
The top-level object identifies the report schema version and contains the
recommendations:

```json
{
  "report_version": 1,
  "recommendations": [
    {
      "schema": "public",
      "table": "library_book",
      "columns": ["author_id"],
      "index_name": "dio_library_book_author_id_idx",
      "calls": 120,
      "total_exec_time": 3480.5,
      "mean_exec_time": 29.004,
      "query_ids": [123456789],
      "reason": "Filtered in 120 calls ...",
      "create_sql": "CREATE INDEX CONCURRENTLY ...;"
    }
  ]
}
```

An empty report uses the same envelope with an empty `recommendations` array.
`report_version` versions the JSON schema independently of the package version.
Before report version 1, `--format json` returned a bare array; consumers
migrating from that output should now read the `recommendations` field.
`report_version` increases when an existing field is removed, renamed, changes
type, or changes meaning. New fields may be added without increasing it
while the package remains alpha, so consumers should ignore unknown fields.
Consumers should check `report_version` before reading recommendations and fail
clearly when they encounter a version they do not support. Consumers that need
an exact field set should also pin the package version.

## What is intentionally excluded today

The conservative `0.2.0` baseline does not guess about:

- multi-column ordering;
- join-only columns;
- `ORDER BY` and `GROUP BY` strategies;
- partial-index predicates;
- expression, GIN, GiST, BRIN, or operator-class indexes;
- unused-index deletion;
- planner cost improvement.

These need more evidence than predicate frequency alone. Returning fewer
explainable candidates is preferable to returning confident-looking noise.
