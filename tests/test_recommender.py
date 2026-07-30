from optimizer.recommender import recommend_indexes


def test_recommend_indexes_returns_columns_meeting_threshold():
    column_stats = {"author_id": 5, "title": 2}

    assert recommend_indexes(column_stats, threshold=5) == ["author_id"]
