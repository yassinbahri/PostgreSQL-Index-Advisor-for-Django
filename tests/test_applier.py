import pytest

from optimizer.applier import IndexApplicationDisabled, create_index


def test_legacy_create_index_is_disabled():
    with pytest.raises(IndexApplicationDisabled, match="review the previewed SQL"):
        create_index("library_book", "author_id")
