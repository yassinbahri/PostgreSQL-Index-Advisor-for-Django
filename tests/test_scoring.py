from optimizer.scoring import score_candidate
from optimizer.types import QueryPattern, TableStatistics


def pattern(*, calls=100, total_exec_time=10_000):
    return QueryPattern(
        schema="public",
        table="library_book",
        columns=("author_id",),
        calls=calls,
        total_exec_time=total_exec_time,
        mean_exec_time=total_exec_time / calls,
        query_ids=(42,),
    )


def statistics(
    *,
    rows=100_000,
    table_bytes=100 * 1024**2,
    sequential_scans=1_000,
    index_scans=100,
    inserts=10,
    updates=10,
    deletes=0,
):
    return TableStatistics(
        estimated_rows=rows,
        table_bytes=table_bytes,
        sequential_scans=sequential_scans,
        index_scans=index_scans,
        inserts=inserts,
        updates=updates,
        deletes=deletes,
    )


def test_score_exposes_every_component():
    score = score_candidate(pattern(), statistics())

    assert score.total == 60
    assert score.workload == 30
    assert score.table_impact == 15
    assert score.read_pressure == 15
    assert score.write_penalty == 0
    assert score.decision == "recommend"


def test_tiny_table_is_suppressed():
    score = score_candidate(
        pattern(calls=1_000),
        statistics(rows=999, table_bytes=1_048_575),
    )

    assert score.decision == "suppress"
    assert "smaller than 1,000" in score.reasons[0]


def test_write_heavy_table_is_suppressed():
    score = score_candidate(
        pattern(calls=100),
        statistics(
            sequential_scans=100,
            inserts=800,
            updates=200,
            deletes=0,
        ),
    )

    assert score.decision == "suppress"
    assert score.write_penalty == 30
    assert "four times" in score.reasons[0]


def test_statistics_unavailable_keeps_candidate_without_guessing_penalties():
    score = score_candidate(pattern(), None)

    assert score.decision == "recommend"
    assert score.total == score.workload
    assert score.table_impact == 0
    assert score.read_pressure == 0
    assert score.write_penalty == 0
    assert "unavailable" in score.reasons[0]


def test_large_read_heavy_table_scores_above_small_quiet_table():
    large = score_candidate(pattern(), statistics())
    small = score_candidate(
        pattern(calls=5, total_exec_time=100),
        statistics(
            rows=1_000,
            table_bytes=1024**2,
            sequential_scans=10,
        ),
    )

    assert large.total > small.total
