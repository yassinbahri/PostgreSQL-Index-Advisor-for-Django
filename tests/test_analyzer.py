from unittest.mock import MagicMock, patch

import pytest
from django.db.utils import DatabaseError

from optimizer.analyzer import (
    QueryCollectionError,
    extract_query_patterns,
    get_frequent_queries,
)
from optimizer.types import QueryStat


def query_stat(
    query,
    *,
    calls=10,
    total_exec_time=250.0,
    mean_exec_time=None,
    query_id=42,
    rows=10,
):
    return QueryStat(
        query_id=query_id,
        query=query,
        calls=calls,
        total_exec_time=total_exec_time,
        mean_exec_time=(
            total_exec_time / calls if mean_exec_time is None else mean_exec_time
        ),
        rows=rows,
    )


def test_extract_query_patterns_parses_filters_and_aliases():
    patterns = extract_query_patterns(
        [
            query_stat(
                """
                SELECT book.id
                FROM library_book AS book
                WHERE book.author_id = $1 AND book.published_at >= $2
                """
            )
        ]
    )

    assert [(item.table, item.columns) for item in patterns] == [
        ("library_book", ("author_id",)),
        ("library_book", ("published_at",)),
    ]


def test_extract_query_patterns_aggregates_workload_evidence():
    patterns = extract_query_patterns(
        [
            query_stat(
                "SELECT * FROM library_book WHERE author_id = $1",
                calls=4,
                total_exec_time=40,
                query_id=1,
            ),
            query_stat(
                "SELECT * FROM library_book WHERE author_id = $1",
                calls=6,
                total_exec_time=90,
                query_id=2,
            ),
        ]
    )

    assert len(patterns) == 1
    assert patterns[0].calls == 10
    assert patterns[0].total_exec_time == 130
    assert patterns[0].mean_exec_time == 13
    assert patterns[0].query_ids == (1, 2)


def test_extract_query_patterns_skips_ambiguous_unqualified_columns():
    patterns = extract_query_patterns(
        [
            query_stat(
                """
                SELECT * FROM author
                JOIN book ON book.author_id = author.id
                WHERE id = $1
                """
            )
        ]
    )

    assert patterns == []


def test_extract_query_patterns_skips_invalid_sql():
    assert extract_query_patterns([query_stat("not valid SELECT (")]) == []


def test_extract_query_patterns_skips_system_catalogs():
    patterns = extract_query_patterns(
        [query_stat("SELECT * FROM pg_index WHERE indisvalid = true")]
    )

    assert patterns == []


def test_get_frequent_queries_returns_structured_records():
    cursor = MagicMock()
    cursor.fetchall.return_value = [(42, "SELECT 1", 3, 12.5, 4.1, 3)]
    cursor_context = MagicMock()
    cursor_context.__enter__.return_value = cursor
    db_connection = MagicMock()
    db_connection.cursor.return_value = cursor_context
    with patch("optimizer.analyzer.connections", {"default": db_connection}):
        rows = get_frequent_queries(limit=25)

    assert rows == [
        query_stat(
            "SELECT 1",
            calls=3,
            total_exec_time=12.5,
            mean_exec_time=4.1,
            rows=3,
        )
    ]
    cursor.execute.assert_called_once()
    assert cursor.execute.call_args.args[1] == [25]


def test_get_frequent_queries_explains_extension_errors():
    db_connection = MagicMock()
    db_connection.cursor.side_effect = DatabaseError("missing relation")
    with (
        patch("optimizer.analyzer.connections", {"default": db_connection}),
        pytest.raises(QueryCollectionError, match="pg_stat_statements"),
    ):
        get_frequent_queries()
