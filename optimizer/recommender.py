def recommend_indexes(column_stats, threshold=5):
    recommended = []
    for column, freq in column_stats.items():
        if freq >= threshold:
            recommended.append(column)
    return recommended


def recommend_composite_indexes(column_pair_stats, threshold=3):
    """Recommend composite (two-column) indexes from co-occurrence counts.

    ``column_pair_stats`` maps a pair of column names to how often they appear
    together in the same ``WHERE`` clause. Pairs seen at least ``threshold``
    times are returned as a sorted, de-duplicated list of two-tuples.
    """
    recommended = set()
    for pair, freq in column_pair_stats.items():
        if freq < threshold:
            continue
        cols = tuple(pair) if isinstance(pair, (list, tuple, set, frozenset)) else (pair,)
        if len(cols) == 2:
            recommended.add(tuple(sorted(cols)))
    return sorted(recommended)
