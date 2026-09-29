from django.db import connections
from django.db.utils import DatabaseError

from optimizer.types import TableStatistics


def load_table_statistics(patterns, using="default"):
    """Collect read-only relation statistics, degrading to no evidence."""
    tables = sorted({(pattern.schema, pattern.table) for pattern in patterns})
    if not tables:
        return {}

    statistics = {}
    try:
        with connections[using].cursor() as cursor:
            for schema, table in tables:
                cursor.execute(
                    """
                    /* postgresql-index-advisor-for-django:table-statistics */
                    SELECT
                        GREATEST(table_class.reltuples::bigint, 0),
                        pg_relation_size(table_class.oid),
                        COALESCE(stats.seq_scan, 0),
                        COALESCE(stats.idx_scan, 0),
                        COALESCE(stats.n_tup_ins, 0),
                        COALESCE(stats.n_tup_upd, 0),
                        COALESCE(stats.n_tup_del, 0)
                    FROM pg_class AS table_class
                    JOIN pg_namespace AS namespace
                      ON namespace.oid = table_class.relnamespace
                    LEFT JOIN pg_stat_all_tables AS stats
                      ON stats.relid = table_class.oid
                    WHERE namespace.nspname = %s
                      AND table_class.relname = %s
                      AND table_class.relkind IN ('r', 'p')
                    """,
                    [schema, table],
                )
                row = cursor.fetchone()
                if row is not None:
                    statistics[(schema, table)] = TableStatistics(*map(int, row))
    except DatabaseError:
        return {}
    return statistics
