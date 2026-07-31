from unittest.mock import patch

import pytest
from django.core.management.base import CommandError

from optimizer.management.commands.optimize_indexes import Command


def test_handle_passes_limit_to_query_analyzer():
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.get_frequent_queries",
            return_value=[],
        ) as get_frequent_queries,
        patch(
            "optimizer.management.commands.optimize_indexes.extract_query_patterns",
            return_value={},
        ),
    ):
        Command().handle(limit=25)

    get_frequent_queries.assert_called_once_with(limit=25)


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
            return_value={},
        ),
    ):
        Command().handle()

    get_frequent_queries.assert_called_once_with(limit=50)