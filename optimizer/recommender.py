def recommend_indexes(column_stats, threshold=5):
    recommended = []
    for column, freq in column_stats.items():
        if freq >= threshold:
            recommended.append(column)
    return recommended
