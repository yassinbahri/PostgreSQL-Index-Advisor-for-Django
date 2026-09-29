import json
from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest
from django.core.management.base import CommandError

from optimizer.management.commands.optimize_indexes import Command
from optimizer.types import IndexRecommendation, RecommendationScore, TableStatistics


@pytest.fixture(autouse=True)
def postgresql_connection():
    connection = MagicMock()
    connection.vendor = "postgresql"
    connection.ops.quote_name.side_effect = lambda value: f'"{value}"'
    with (
        patch(
            "optimizer.management.commands.optimize_indexes.connections",
            {"default": connection, "analytics": connection},
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.build_model_map",
            return_value={},
        ),
    ):
        yield connection


@pytest.fixture
def recommendation():
    return IndexRecommendation(
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

    recommend_indexes.assert_called_once_with(
        [], min_calls=12, using="default", model_map={}
    )


@pytest.mark.parametrize("min_calls", [0, -1])
def test_handle_rejects_non_positive_min_calls(min_calls):
    with pytest.raises(CommandError, match="--min-calls"):
        Command().handle(min_calls=min_calls)


def test_handle_outputs_versioned_machine_readable_json(capsys, recommendation):
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

    assert json.loads(capsys.readouterr().out) == {
        "report_version": 1,
        "recommendations": [
            {
                "schema": "public",
                "table": "library_book",
                "columns": ["author_id"],
                "index_name": "dio_library_book_author_id_idx",
                "calls": 20,
                "total_exec_time": 250,
                "mean_exec_time": 12.5,
                "query_ids": [42],
                "reason": "Repeated filter without an existing index.",
                "model_mapping": "not_checked",
                "django_model": None,
                "django_fields": [],
                "django_field_kinds": [],
                "django_index": None,
                "table_statistics": None,
                "score": None,
                "create_sql": 'CREATE INDEX CONCURRENTLY "example";',
            }
        ],
    }


def test_handle_outputs_versioned_empty_json_report(capsys):
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
        ),
    ):
        Command().handle(format="json")

    assert json.loads(capsys.readouterr().out) == {
        "report_version": 1,
        "recommendations": [],
    }


def test_handle_keeps_text_output_human_readable(capsys, recommendation):
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
        Command().handle(format="text")

    assert capsys.readouterr().out == (
        "1 recommendation(s). Review before applying.\n"
        "\npublic.library_book (author_id)\n"
        "  Suggested name: dio_library_book_author_id_idx\n"
        "  Evidence: Repeated filter without an existing index.\n"
        '  SQL preview: CREATE INDEX CONCURRENTLY "example";\n'
    )


def test_handle_outputs_django_model_and_index_suggestion(capsys, recommendation):
    mapped = replace(
        recommendation,
        model_mapping="matched",
        django_model="library.Book",
        django_fields=("author",),
        django_field_kinds=("relation",),
        django_index='models.Index(fields=["author"])',
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
            return_value=[mapped],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.create_index_sql",
            return_value='CREATE INDEX CONCURRENTLY "example";',
        ),
    ):
        Command().handle(format="text")

    output = capsys.readouterr().out
    assert "Django model: library.Book" in output
    assert "Django fields: author" in output
    assert 'Django suggestion: models.Index(fields=["author"])' in output


def test_handle_outputs_score_and_table_evidence(capsys, recommendation):
    scored = replace(
        recommendation,
        table_statistics=TableStatistics(
            estimated_rows=100_000,
            table_bytes=10_485_760,
            sequential_scans=500,
            index_scans=20,
            inserts=10,
            updates=20,
            deletes=5,
        ),
        score=RecommendationScore(
            total=55,
            workload=30,
            table_impact=10,
            read_pressure=15,
            write_penalty=0,
            decision="recommend",
            reasons=("Evidence-based candidate.",),
        ),
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
            return_value=[scored],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.create_index_sql",
            return_value='CREATE INDEX CONCURRENTLY "example";',
        ),
    ):
        Command().handle(format="text")

    output = capsys.readouterr().out
    assert "Score: 55/100" in output
    assert "workload 30, table 10, reads 15, write penalty 0" in output
    assert "100000 estimated rows" in output
    assert "500 sequential scans, 35 writes" in output


def test_handle_explains_unmapped_table(capsys, recommendation):
    unmapped = replace(recommendation, model_mapping="unmapped_table")
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
            return_value=[unmapped],
        ),
        patch(
            "optimizer.management.commands.optimize_indexes.create_index_sql",
            return_value='CREATE INDEX CONCURRENTLY "example";',
        ),
    ):
        Command().handle(format="text")

    assert "Django mapping: no managed Django model found" in capsys.readouterr().out


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


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_fail_on_recommendations_reports_before_raising(
    output_format, capsys, recommendation
):
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
        pytest.raises(CommandError, match="found 1 recommendation"),
    ):
        Command().handle(
            format=output_format,
            fail_on_recommendations=True,
        )

    output = capsys.readouterr().out
    if output_format == "json":
        assert json.loads(output)["recommendations"][0]["table"] == "library_book"
    else:
        assert "1 recommendation(s)" in output
        assert "library_book" in output


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_fail_on_recommendations_succeeds_when_report_is_empty(output_format, capsys):
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
        ),
    ):
        Command().handle(
            format=output_format,
            fail_on_recommendations=True,
        )

    output = capsys.readouterr().out
    if output_format == "json":
        assert json.loads(output) == {
            "report_version": 1,
            "recommendations": [],
        }
    else:
        assert "No missing indexes" in output
