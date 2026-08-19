import hashlib

from django.db import connections

from optimizer.types import IndexRecommendation


def recommend_indexes(patterns, min_calls=5, using="default"):
    existing_indexes = _load_existing_indexes(patterns, using=using)
    recommendations = []
    for pattern in patterns:
        if pattern.calls < min_calls:
            continue
        indexes = existing_indexes.get((pattern.schema, pattern.table), ())
        if any(index[: len(pattern.columns)] == pattern.columns for index in indexes):
            continue
        recommendations.append(
            IndexRecommendation(
                schema=pattern.schema,
                table=pattern.table,
                columns=pattern.columns,
                index_name=_index_name(pattern.table, pattern.columns),
                calls=pattern.calls,
                total_exec_time=pattern.total_exec_time,
                mean_exec_time=pattern.mean_exec_time,
                query_ids=pattern.query_ids,
                reason=(
                    f"Filtered in {pattern.calls} calls accounting for "
                    f"{pattern.total_exec_time:.1f} ms of execution time; no "
                    "existing index has these columns as its leading prefix."
                ),
            )
        )
    return recommendations


def _load_existing_indexes(patterns, using="default"):
    tables = sorted({(pattern.schema, pattern.table) for pattern in patterns})
    if not tables:
        return {}

    existing = {}
    with connections[using].cursor() as cursor:
        for schema, table in tables:
            cursor.execute(
                """
                /* django-index-optimizer:existing-indexes */
                SELECT array_agg(attribute.attname ORDER BY key.ordinality)
                FROM pg_index AS index
                JOIN pg_class AS table_class
                  ON table_class.oid = index.indrelid
                JOIN pg_namespace AS namespace
                  ON namespace.oid = table_class.relnamespace
                JOIN LATERAL unnest(index.indkey)
                  WITH ORDINALITY AS key(attnum, ordinality) ON TRUE
                JOIN pg_attribute AS attribute
                  ON attribute.attrelid = table_class.oid
                 AND attribute.attnum = key.attnum
                WHERE namespace.nspname = %s
                  AND table_class.relname = %s
                  AND index.indisvalid
                  AND index.indisready
                  AND key.ordinality <= index.indnkeyatts
                GROUP BY index.indexrelid
                """,
                [schema, table],
            )
            existing[(schema, table)] = tuple(
                tuple(columns) for (columns,) in cursor.fetchall()
            )
    return existing


def _index_name(table, columns):
    base = f"dio_{table}_{'_'.join(columns)}_idx"
    if len(base) <= 63:
        return base
    digest = hashlib.sha256(base.encode()).hexdigest()[:8]
    return f"{base[:54]}_{digest}"
