from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class QueryStat:
    query_id: int | None
    query: str
    calls: int
    total_exec_time: float
    mean_exec_time: float
    rows: int


@dataclass(frozen=True)
class QueryPattern:
    schema: str
    table: str
    columns: tuple[str, ...]
    calls: int
    total_exec_time: float
    mean_exec_time: float
    query_ids: tuple[int, ...]


@dataclass(frozen=True)
class TableStatistics:
    estimated_rows: int
    table_bytes: int
    sequential_scans: int
    index_scans: int
    inserts: int
    updates: int
    deletes: int

    @property
    def writes(self):
        return self.inserts + self.updates + self.deletes


@dataclass(frozen=True)
class RecommendationScore:
    total: int
    workload: int
    table_impact: int
    read_pressure: int
    write_penalty: int
    decision: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class IndexRecommendation:
    schema: str
    table: str
    columns: tuple[str, ...]
    index_name: str
    calls: int
    total_exec_time: float
    mean_exec_time: float
    query_ids: tuple[int, ...]
    reason: str
    model_mapping: str = "not_checked"
    django_model: str | None = None
    django_fields: tuple[str, ...] = ()
    django_field_kinds: tuple[str, ...] = ()
    django_index: str | None = None
    table_statistics: TableStatistics | None = None
    score: RecommendationScore | None = None

    def as_dict(self):
        return asdict(self)
