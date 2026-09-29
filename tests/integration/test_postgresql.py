import os

import pytest

pytestmark = [
    pytest.mark.postgresql,
    pytest.mark.skipif(
        os.getenv("DIO_TEST_POSTGRES") != "1",
        reason="Set DIO_TEST_POSTGRES=1 to run PostgreSQL integration tests.",
    ),
]


def test_workload_recommendation_and_existing_index_suppression():
    import django
    from django.db import connection

    from optimizer.analyzer import extract_query_patterns, get_frequent_queries
    from optimizer.model_mapping import build_model_map
    from optimizer.recommender import recommend_indexes

    django.setup()

    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
        cursor.execute("DROP TABLE IF EXISTS dio_integration_book")
        cursor.execute(
            """
            CREATE TABLE dio_integration_book (
                id bigint PRIMARY KEY,
                author_id bigint NOT NULL,
                published_at timestamptz
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO dio_integration_book
            SELECT number, number % 10, now()
            FROM generate_series(1, 1000) AS number
            """
        )
        cursor.execute("ANALYZE dio_integration_book")
        cursor.execute("SELECT pg_stat_statements_reset()")
        for _ in range(10):
            cursor.execute(
                "SELECT count(*) FROM dio_integration_book WHERE author_id = %s",
                [3],
            )

    patterns = extract_query_patterns(get_frequent_queries(limit=50))
    recommendations = recommend_indexes(
        patterns,
        min_calls=5,
        model_map=build_model_map(),
    )
    matching = [
        item
        for item in recommendations
        if item.table == "dio_integration_book" and item.columns == ("author_id",)
    ]
    assert len(matching) == 1
    assert matching[0].calls == 10
    assert matching[0].model_mapping == "matched"
    assert matching[0].django_model == "optimizer_integration.IntegrationBook"
    assert matching[0].django_fields == ("author",)
    assert matching[0].django_field_kinds == ("relation",)
    assert matching[0].django_index == 'models.Index(fields=["author"])'
    assert matching[0].table_statistics.estimated_rows == 1000
    assert matching[0].table_statistics.table_bytes > 0
    assert matching[0].score.decision == "recommend"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE INDEX dio_integration_book_author_date_idx
            ON dio_integration_book (author_id, published_at)
            """
        )

    recommendations = recommend_indexes(
        patterns,
        min_calls=5,
        model_map=build_model_map(),
    )
    assert not any(item.table == "dio_integration_book" for item in recommendations)
