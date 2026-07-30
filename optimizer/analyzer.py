from django.db import connection
import re

def get_frequent_queries(limit=50):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT query, calls, total_time, rows, mean_time
            FROM pg_stat_statements
            ORDER BY total_time DESC
            LIMIT %s;
        """, [limit])
        return cursor.fetchall()

def extract_query_patterns(queries):
    column_counter = {}
    for query, *_ in queries:
        for match in re.findall(r'WHERE\\s+(.+?)(?:\\s+GROUP|\\s+ORDER|;|$)', query, re.IGNORECASE):
            cols = re.findall(r'(\\w+)\\s*=|>|<', match)
            for col in cols:
                column_counter[col] = column_counter.get(col, 0) + 1
    return column_counter
