from optimizer.recommender import recommend_indexes, recommend_composite_indexes


def test_recommend_indexes_returns_columns_meeting_threshold():
    column_stats = {"author_id": 5, "title": 2}

    assert recommend_indexes(column_stats, threshold=5) == ["author_id"]


def test_recommend_composite_indexes_dedupes_and_sorts():
    pair_stats = {
        ("author_id", "created_at"): 7,
        ("created_at", "author_id"): 9,
        ("title", "slug"): 1,
    }

    assert recommend_composite_indexes(pair_stats, threshold=3) == [("author_id", "created_at")]


def test_recommend_composite_indexes_respects_threshold():
    pair_stats = {("a", "b"): 2}

    assert recommend_composite_indexes(pair_stats, threshold=3) == []
