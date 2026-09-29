from unittest.mock import patch

from optimizer.model_mapping import DjangoFieldReference, DjangoModelReference
from optimizer.recommender import _index_name, recommend_indexes
from optimizer.types import QueryPattern


def pattern(*, calls=5, total_exec_time=100.0, columns=("author_id",)):
    return QueryPattern(
        schema="public",
        table="books_book",
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
