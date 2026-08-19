from unittest.mock import MagicMock, patch

import pytest
from django.core.management.base import CommandError

from optimizer.management.commands.optimize_indexes import Command
from optimizer.types import IndexRecommendation


@pytest.fixture(autouse=True)
def postgresql_connection():
    connection = MagicMock()
    connection.vendor = "postgresql"
    connection.ops.quote_name.side_effect = lambda value: f'"{value}"'
    with patch(
        "optimizer.management.commands.optimize_indexes.connections",
        {"default": connection, "analytics": connection},
    ):
        yield connection


def test_handle_passes_limit_to_query_analyzer():
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries",
            return_value=[],
        ) as get_frequent_queries,
        patch(
            "optimizer.management.commands.optimize_indexes.extract_query_patterns",
            return_value=[],
        ),
    ):
        Command().handle(limit=25)

    get_frequent_queries.assert_called_once_with(limit=25, using="default")


@pytest.mark.parametrize("limit", [0, -1])
def test_handle_rejects_non_positive_limit_without_querying(limit):
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries"
        ) as get_frequent_queries,
        pytest.raises(CommandError, match="positive integer"),
    ):
        Command().handle(limit=limit)

    get_frequent_queries.assert_not_called()


def test_handle_defaults_to_fifty_statements():
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries",
            return_value=[],
        ) as get_frequent_queries,
        patch(
            "optimizer.management.commands.optimize_indexes.extract_query_patterns",
            return_value=[],
        ),
    ):
        Command().handle()

    get_frequent_queries.assert_called_once_with(limit=50, using="default")


def test_handle_passes_min_calls_to_recommender():
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries",
            return_value=[],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.extract_query_patterns",
            return_value=[],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.recommend_indexes",
            return_value=[],
        ) as recommend_indexes,
    ):
        Command().handle(min_calls=12)

    recommend_indexes.assert_called_once_with([], min_calls=12, using="default")


@pytest.mark.parametrize("min_calls", [0, -1])
def test_handle_rejects_non_positive_min_calls(min_calls):
    with pytest.raises(CommandError, match="--min-calls"):
        Command().handle(min_calls=min_calls)


def test_handle_outputs_machine_readable_json(capsys):
    recommendation = IndexRecommendation(
        schema="public",
        table="library_book",
        columns=("author_id",),
        index_name="dio_library_book_author_id_idx",
        calls=20,
        total_exec_time=250,
        mean_exec_time=12.5,
        query_ids=(42,),
        reason="Repeated filter without an existing index.",
    )
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries",
            return_value=[],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.extract_query_patterns",
            return_value=[],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.recommend_indexes",
            return_value=[recommendation],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.create_index_sql",
            return_value='CREATE INDEX CONCURRENTLY "example";',
        ),
    ):
        Command().handle(format="json")

    assert '"table": "library_book"' in capsys.readouterr().out


def test_handle_uses_selected_database_alias():
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries",
            return_value=[],
        ) as get_frequent_queries,
        patch(
            "optimizer.management.commands.optimize_indexes.extract_query_patterns",
            return_value=[],
        ),
    ):
        Command().handle(database="analytics")

    get_frequent_queries.assert_called_once_with(limit=50, using="analytics")


def test_handle_rejects_non_postgresql_database(postgresql_connection):
    postgresql_connection.vendor = "sqlite"

    with pytest.raises(CommandError, match="supports PostgreSQL only"):
        Command().handle()
