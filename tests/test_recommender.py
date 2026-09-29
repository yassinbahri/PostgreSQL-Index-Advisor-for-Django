from unittest.mock import patch

import pytest

from optimizer.model_mapping import DjangoFieldReference, DjangoModelReference
from optimizer.recommender import _index_name, recommend_indexes
from optimizer.types import QueryPattern, TableStatistics


@pytest.fixture(autouse=True)
def no_table_statistics():
    with patch("optimizer.recommender.load_table_statistics", return_value={}):
        yield


def pattern(
    *,
    calls=5,
    total_exec_time=100.0,
    columns=("author_id",),
    table="books_book",
):
    return QueryPattern(
        schema="public",
        table=table,
        columns=columns,
        calls=calls,
        total_exec_time=total_exec_time,
        mean_exec_time=total_exec_time / calls,
        query_ids=(42,),
    )


def test_recommend_indexes_returns_structured_evidence():
    with patch("optimizer.recommender._load_existing_indexes", return_value={}):
        recommendations = recommend_indexes([pattern()])

    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation.table == "books_book"
    assert recommendation.columns == ("author_id",)
    assert recommendation.calls == 5
    assert recommendation.query_ids == (42,)


def test_recommend_indexes_includes_django_native_suggestion():
    model_map = {
        ("public", "books_book"): (
            DjangoModelReference(
                label="books.Book",
                schema="public",
                table="books_book",
                fields=(
                    DjangoFieldReference(
                        name="author",
                        column="author_id",
                        kind="relation",
                    ),
                ),
            ),
        )
    }
    with patch("optimizer.recommender._load_existing_indexes", return_value={}):
        recommendation = recommend_indexes([pattern()], model_map=model_map)[0]

    assert recommendation.model_mapping == "matched"
    assert recommendation.django_model == "books.Book"
    assert recommendation.django_fields == ("author",)
    assert recommendation.django_field_kinds == ("relation",)
    assert recommendation.django_index == 'models.Index(fields=["author"])'


def test_recommend_indexes_reports_unmapped_table_without_guessing():
    with patch("optimizer.recommender._load_existing_indexes", return_value={}):
        recommendation = recommend_indexes([pattern()], model_map={})[0]

    assert recommendation.model_mapping == "unmapped_table"
    assert recommendation.django_model is None
    assert recommendation.django_fields == ()
    assert recommendation.django_index is None


def test_recommend_indexes_suppresses_tiny_table(no_table_statistics):
    tiny = TableStatistics(
        estimated_rows=100,
        table_bytes=64 * 1024,
        sequential_scans=500,
        index_scans=0,
        inserts=0,
        updates=0,
        deletes=0,
    )
    with (
        patch("optimizer.recommender._load_existing_indexes", return_value={}),
        patch(
            "optimizer.recommender.load_table_statistics",
            return_value={("public", "books_book"): tiny},
        ),
    ):
        assert recommend_indexes([pattern(calls=1_000)]) == []


def test_recommend_indexes_ranks_by_explainable_score(no_table_statistics):
    large = TableStatistics(
        estimated_rows=1_000_000,
        table_bytes=1024**3,
        sequential_scans=5_000,
        index_scans=100,
        inserts=10,
        updates=10,
        deletes=0,
    )
    small = TableStatistics(
        estimated_rows=1_000,
        table_bytes=1024**2,
        sequential_scans=10,
        index_scans=1,
        inserts=0,
        updates=0,
        deletes=0,
    )
    patterns = [
        pattern(table="small_book", total_exec_time=2_000),
        pattern(table="large_book", total_exec_time=1_000),
    ]
    with (
        patch("optimizer.recommender._load_existing_indexes", return_value={}),
        patch(
            "optimizer.recommender.load_table_statistics",
            return_value={
                ("public", "large_book"): large,
                ("public", "small_book"): small,
            },
        ),
    ):
        recommendations = recommend_indexes(patterns)

    assert [item.table for item in recommendations] == ["large_book", "small_book"]
    assert recommendations[0].score.total > recommendations[1].score.total
    assert recommendations[0].table_statistics == large


def test_recommend_indexes_excludes_frequencies_below_threshold():
    with patch("optimizer.recommender._load_existing_indexes", return_value={}):
        assert recommend_indexes([pattern(calls=4)], min_calls=5) == []


def test_recommend_indexes_excludes_existing_index_prefix():
    existing = {("public", "books_book"): (("author_id", "created_at"),)}
    with patch("optimizer.recommender._load_existing_indexes", return_value=existing):
        assert recommend_indexes([pattern()]) == []


def test_recommend_indexes_doesnt_treat_nonleading_column_as_covered():
    existing = {("public", "books_book"): (("created_at", "author_id"),)}
    with patch("optimizer.recommender._load_existing_indexes", return_value=existing):
        assert len(recommend_indexes([pattern()])) == 1


def test_recommend_indexes_returns_empty_for_empty_input():
    assert recommend_indexes([]) == []


def test_index_name_doesnt_exceed_postgresql_limit():
    name = _index_name("very_long_table_name_" * 4, ("very_long_column_name_" * 4,))

    assert len(name) <= 63
    assert name[-8:].isalnum()
