from optimizer.recommender import recommend_indexes


def test_recommend_indexes_returns_columns_meeting_threshold():
    column_stats = {"author_id": 5, "title": 2}

    assert recommend_indexes(column_stats, threshold=5) == ["author_id"]

def test_recommend_indexes_excludes_frequencies_below_threshold():
    assert recommend_indexes({"author_id": 4}, threshold=5) == []


def test_recommend_indexes_respects_custom_threshold():
    assert recommend_indexes({"author_id": 3, "title": 2}, threshold=3) == ["author_id"]


def test_recommend_indexes_returns_empty_for_empty_input():
    assert recommend_indexes({}) == []


def test_recommend_indexes_preserves_input_order():
    column_stats = {"title": 7, "author_id": 9, "category_id": 6}

    assert recommend_indexes(column_stats) == ["title", "author_id", "category_id"]