from optimizer.types import RecommendationScore

TINY_TABLE_BYTES = 1_048_576
TINY_TABLE_ROWS = 1_000
WRITE_HEAVY_MIN_WRITES = 1_000
WRITE_HEAVY_RATIO = 4


def score_candidate(pattern, statistics):
    """Return a deterministic score whose components remain reviewable."""
    workload = _workload_score(pattern.calls, pattern.total_exec_time)
    if statistics is None:
        return RecommendationScore(
            total=workload,
            workload=workload,
            table_impact=0,
            read_pressure=0,
            write_penalty=0,
            decision="recommend",
            reasons=("Table statistics were unavailable; no size or write penalty applied.",),
        )

    table_impact = max(
        _threshold_score(
            statistics.estimated_rows,
            ((10_000_000, 25), (1_000_000, 20), (100_000, 15), (10_000, 10), (1_000, 5)),
        ),
        _threshold_score(
            statistics.table_bytes,
            (
                (10 * 1024**3, 25),
                (1024**3, 20),
                (100 * 1024**2, 15),
                (10 * 1024**2, 10),
                (1024**2, 5),
            ),
        ),
    )
    read_pressure = _threshold_score(
        statistics.sequential_scans,
        ((10_000, 20), (1_000, 15), (100, 10), (10, 5)),
    )
    comparison_reads = max(pattern.calls + statistics.sequential_scans, 1)
    write_ratio = statistics.writes / comparison_reads
    write_penalty = _write_penalty(write_ratio)

    suppression_reasons = []
    if (
        statistics.estimated_rows < TINY_TABLE_ROWS
        and statistics.table_bytes < TINY_TABLE_BYTES
    ):
        suppression_reasons.append(
            "Suppressed because the table is smaller than 1,000 estimated rows "
            "and 1 MiB."
        )
    if (
        statistics.writes >= WRITE_HEAVY_MIN_WRITES
        and write_ratio >= WRITE_HEAVY_RATIO
    ):
        suppression_reasons.append(
            "Suppressed because write activity is at least four times the "
            "observed candidate read pressure."
        )

    total = max(0, min(100, workload + table_impact + read_pressure - write_penalty))
    reasons = suppression_reasons or [
        (
            "Score combines workload frequency and time, table impact, "
            "sequential scan pressure, and estimated write overhead."
        )
    ]
    return RecommendationScore(
        total=total,
        workload=workload,
        table_impact=table_impact,
        read_pressure=read_pressure,
        write_penalty=write_penalty,
        decision="suppress" if suppression_reasons else "recommend",
        reasons=tuple(reasons),
    )


def _workload_score(calls, total_exec_time):
    call_score = _threshold_score(
        calls,
        ((1_000, 25), (100, 20), (20, 15), (5, 10)),
    )
    time_score = _threshold_score(
        total_exec_time,
        ((60_000, 15), (10_000, 10), (1_000, 5)),
    )
    return call_score + time_score


def _write_penalty(write_ratio):
    if write_ratio >= 4:
        return 30
    if write_ratio >= 1:
        return 20
    if write_ratio >= 0.25:
        return 10
    return 0


def _threshold_score(value, thresholds):
    for minimum, score in thresholds:
        if value >= minimum:
            return score
    return 0
