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

    def as_dict(self):
        return asdict(self)
