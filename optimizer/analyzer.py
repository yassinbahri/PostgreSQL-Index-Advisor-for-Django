from django.db import connections
from django.db.utils import DatabaseError
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from optimizer.types import QueryPattern, QueryStat


class QueryCollectionError(RuntimeError):
    pass


def get_frequent_queries(limit=50, using="default"):
    try:
        with connections[using].cursor() as cursor:
            cursor.execute(
                """
                /* django-index-optimizer:collect-workload */
                SELECT queryid, query, calls, total_exec_time,
                       mean_exec_time, rows
                FROM pg_stat_statements
                WHERE dbid = (
                    SELECT oid
                    FROM pg_database
                    WHERE datname = current_database()
                )
                AND query IS NOT NULL
                ORDER BY total_exec_time DESC
                LIMIT %s
                """,
                [limit],
            )
            rows = cursor.fetchall()
    except DatabaseError as exc:
        raise QueryCollectionError(
            "Could not read pg_stat_statements. Confirm that the extension is "
            "installed in this database and that the Django database user can "
            "read it."
        ) from exc

    return [
        QueryStat(
            query_id=query_id,
            query=query,
            calls=calls,
            total_exec_time=total_exec_time,
            mean_exec_time=mean_exec_time,
            rows=row_count,
        )
        for query_id, query, calls, total_exec_time, mean_exec_time, row_count in rows
    ]


def extract_query_patterns(query_stats):
    aggregated = {}
    for query_stat in query_stats:
        for schema, table, column in _extract_filter_columns(query_stat.query):
            if schema in {"information_schema", "pg_catalog"} or table.startswith(
                "pg_"
            ):
                continue
            key = (schema, table, column)
            current = aggregated.setdefault(
                key,
                {
                    "calls": 0,
                    "total_exec_time": 0.0,
                    "query_ids": set(),
                },
            )
            current["calls"] += query_stat.calls
            current["total_exec_time"] += query_stat.total_exec_time
            if query_stat.query_id is not None:
                current["query_ids"].add(query_stat.query_id)

    patterns = []
    for (schema, table, column), evidence in aggregated.items():
        calls = evidence["calls"]
        patterns.append(
            QueryPattern(
                schema=schema,
                table=table,
                columns=(column,),
                calls=calls,
                total_exec_time=evidence["total_exec_time"],
                mean_exec_time=(evidence["total_exec_time"] / calls if calls else 0),
                query_ids=tuple(sorted(evidence["query_ids"])),
            )
        )
    return sorted(patterns, key=lambda pattern: pattern.total_exec_time, reverse=True)


def _extract_filter_columns(query):
    statement_type = query.lstrip().partition(" ")[0].upper()
    if statement_type not in {"DELETE", "SELECT", "UPDATE", "WITH"}:
        return []
    try:
        statement = parse_one(query, dialect="postgres")
    except ParseError:
        return []

    where = statement.find(exp.Where)
    if where is None:
        return []

    tables = list(statement.find_all(exp.Table))
    aliases = {
        table.alias_or_name: (table.db or "public", table.name) for table in tables
    }
    unique_tables = set(aliases.values())
    columns = []
    seen = set()
    for column in where.find_all(exp.Column):
        if column.table:
            table_identity = aliases.get(column.table)
        elif len(unique_tables) == 1:
            table_identity = next(iter(unique_tables))
        else:
            table_identity = None
        if table_identity is None:
            continue
        item = (*table_identity, column.name)
        if item not in seen:
            seen.add(item)
            columns.append(item)
    return columns
