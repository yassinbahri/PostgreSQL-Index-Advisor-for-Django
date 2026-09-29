from unittest.mock import MagicMock, patch

from django.db.utils import DatabaseError

from optimizer.table_statistics import load_table_statistics
from optimizer.types import QueryPattern


def pattern(schema="public", table="library_book"):
    return QueryPattern(
        schema=schema,
        table=table,
        columns=("author_id",),
        calls=20,
        total_exec_time=250,
        mean_exec_time=12.5,
        query_ids=(42,),
    )


def test_load_table_statistics_collects_read_and_write_evidence():
    cursor = MagicMock()
    cursor.fetchone.return_value = (25000, 4_194_304, 800, 120, 20, 30, 5)
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    with patch("optimizer.table_statistics.connections", {"default": connection}):
        result = load_table_statistics([pattern()])

    statistics = result[("public", "library_book")]
    assert statistics.estimated_rows == 25000
    assert statistics.table_bytes == 4_194_304
    assert statistics.sequential_scans == 800
    assert statistics.index_scans == 120
    assert statistics.writes == 55
    cursor.execute.assert_called_once()
    assert cursor.execute.call_args.args[1] == ["public", "library_book"]


def test_load_table_statistics_queries_each_table_once():
    cursor = MagicMock()
    cursor.fetchone.return_value = (1000, 131_072, 10, 1, 0, 0, 0)
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    patterns = [
        pattern(),
        pattern(),
        pattern(schema="analytics", table="event"),
    ]

    with patch("optimizer.table_statistics.connections", {"default": connection}):
        result = load_table_statistics(patterns)

    assert set(result) == {("public", "library_book"), ("analytics", "event")}
    assert cursor.execute.call_count == 2


def test_load_table_statistics_omits_missing_relation():
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    with patch("optimizer.table_statistics.connections", {"default": connection}):
        assert load_table_statistics([pattern()]) == {}


def test_load_table_statistics_degrades_when_catalogs_are_unavailable():
    connection = MagicMock()
    connection.cursor.side_effect = DatabaseError("statistics unavailable")

    with patch("optimizer.table_statistics.connections", {"default": connection}):
        assert load_table_statistics([pattern()]) == {}
