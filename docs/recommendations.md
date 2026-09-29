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

## Django model mapping

The advisor compares each PostgreSQL `(schema, table)` identity with managed,
non-proxy models in Django's application registry. It then maps database column
names back to concrete Django field names. This means a foreign-key column such
as `author_id` can produce:

```python
models.Index(fields=["author"])
```

The mapping supports default tables, custom `db_table` values, common
schema-qualified table forms, custom `db_column` values, inherited concrete
fields, relation fields, and generated fields.

The `model_mapping` field makes uncertainty explicit:

- `matched`: exactly one managed model and every column matched;
- `unmapped_table`: no managed model owns the table;
- `ambiguous_table`: multiple managed models declare the same table;
- `unmapped_column`: the model was found but at least one column was not;
- `not_checked`: model mapping was not requested through the lower-level Python
  API.

The management command always performs the check. It does not choose a model
when ownership is ambiguous and does not return a partial field suggestion when
a column is unknown.

## Explainable scoring

Each candidate receives a score from 0 to 100. The score is an explainable
ranking aid, not a machine-learning confidence value. Its components are:

- workload, from 0 to 40, based on statement calls and total execution time;
- table impact, from 0 to 25, based on estimated rows and relation size;
- read pressure, from 0 to 20, based on sequential scans;
- write penalty, from 0 to 30, based on inserts, updates, and deletes.

The total is `workload + table impact + read pressure - write penalty`, clamped
to the 0-100 range. Reports expose every component and the evidence used to
calculate it, so two candidates can be compared without treating the final
number as a black box.

### Conservative suppression

The advisor omits a candidate when either of these rules applies:

- the table has fewer than 1,000 estimated rows *and* occupies less than 1 MiB;
- the table has at least 1,000 recorded writes and its write count is at least
  four times the candidate's calls plus the table's sequential scans.

These rules deliberately avoid recommending indexes whose likely maintenance
cost outweighs the available read evidence.

### Statistics availability

Table evidence is read without modifying the database from `pg_class`,
`pg_namespace`, `pg_stat_all_tables`, and `pg_relation_size()`. If those
statistics cannot be read, the advisor keeps the candidate, reports
`table_statistics` as `null`, and ranks it from workload evidence only. It does
not invent table size or write activity.

PostgreSQL statistics can be reset, and the collection window for table
statistics may differ from `pg_stat_statements`. Treat the score as evidence to
review alongside your knowledge of the workload.

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

Planner validation remains outside the current scope. Recommendations are
still candidates for investigation rather than instructions to create indexes.

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
      "model_mapping": "matched",
      "django_model": "library.Book",
      "django_fields": ["author"],
      "django_field_kinds": ["relation"],
      "django_index": "models.Index(fields=[\"author\"])",
      "table_statistics": {
        "estimated_rows": 100000,
        "table_bytes": 104857600,
        "sequential_scans": 1000,
        "index_scans": 100,
        "inserts": 10,
        "updates": 10,
        "deletes": 0
      },
      "score": {
        "total": 60,
        "workload": 30,
        "table_impact": 15,
        "read_pressure": 15,
        "write_penalty": 0,
        "decision": "recommend",
        "reasons": [
          "Score combines workload frequency and time, table impact, sequential scan pressure, and estimated write overhead."
        ]
      },
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
